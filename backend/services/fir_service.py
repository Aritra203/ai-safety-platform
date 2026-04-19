"""
FIR Service — generates court-ready PDF using ReportLab Platypus,
uploads to Cloudinary, and persists metadata.
"""

import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

from backend.config.settings import settings
from backend.models.schemas import FinalizeFIRRequest
from backend.services.cloudinary_service import CloudinaryService

logger = logging.getLogger(__name__)


def get_ist_now():
    """Get current time in IST (UTC+5:30)"""
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist


def convert_to_ist(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to IST"""
    return utc_dt + timedelta(hours=5, minutes=30)


class FIRService:
    def __init__(self, db):
        self.db = db
        self.output_dir = Path(settings.FIR_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Create FIR record ─────────────────────────────────────────
    async def create_fir_record(self, analysis_id: str) -> str:
        # Verify analysis exists
        analysis = await self.db.analyses.find_one({"id": analysis_id})
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        fir_id = f"FIR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        await self.db.fir_reports.insert_one({
            "fir_id": fir_id,
            "analysis_id": analysis_id,
            "status": "draft",
            "created_at": datetime.utcnow(),
            "pdf_path": None,
            "pdf_url": None,
        })
        logger.info("FIR record created: %s", fir_id)
        return fir_id

    # ── Generate FIR PDF ──────────────────────────────────────────
    async def generate_fir_pdf(self, data: FinalizeFIRRequest) -> str:
        fir_record = await self._find_fir_record(data.fir_id)
        if not fir_record:
            raise ValueError(f"FIR {data.fir_id} not found")

        canonical_fir_id = fir_record.get("fir_id", data.fir_id)

        analysis = await self.db.analyses.find_one({"id": data.analysis_id})

        pdf_path = self.output_dir / f"{canonical_fir_id}.pdf"
        self._build_pdf(pdf_path, data, analysis)

        # Upload to Cloudinary
        cloudinary = CloudinaryService()
        pdf_url = await cloudinary.upload_file(
            str(pdf_path),
            folder="fir_reports",
            resource_type="raw",
            public_id=canonical_fir_id,
        )

        # Update DB record
        await self.db.fir_reports.update_one(
            {"fir_id": canonical_fir_id},
            {"$set": {
                "status": "finalized",
                "pdf_path": str(pdf_path),
                "pdf_url": pdf_url,
                "complainant_name": data.complainant_name,
                "complainant_contact": data.complainant_contact,
                "complainant_address": data.complainant_address,
                "accused_name": data.accused_name,
                "accused_details": data.accused_details,
                "incident_date": data.incident_date,
                "incident_time": data.incident_time,
                "incident_location": data.incident_location,
                "additional_info": data.additional_info,
                "legal_sections": data.legal_sections,
                "evidence_urls": data.evidence_urls,
                "finalized_at": datetime.utcnow(),
            }},
        )
        logger.info("FIR finalized: %s → %s", canonical_fir_id, pdf_url)
        return pdf_url

    # ── Get PDF path ──────────────────────────────────────────────
    async def get_fir_pdf_path(self, fir_id: str) -> str:
        record = await self._find_fir_record(fir_id)
        if not record or not record.get("pdf_path"):
            raise ValueError(f"PDF for FIR {fir_id} not ready")
        return record["pdf_path"]

    async def get_fir_download_targets(self, fir_id: str) -> tuple[str | None, str | None]:
        """Return local PDF path and cloud URL for download fallback handling."""
        record = await self._find_fir_record(fir_id)
        if not record:
            raise ValueError(f"FIR {fir_id} not found")

        pdf_path = record.get("pdf_path")
        pdf_url = record.get("pdf_url")

        # Recover legacy finalized FIRs that are missing PDF pointers.
        if (not pdf_path and not pdf_url) and record.get("status") == "finalized":
            logger.warning("Missing PDF references for %s; attempting legacy recovery", record.get("fir_id"))
            recovered_url = await self._recover_legacy_pdf(record)
            if recovered_url:
                refreshed = await self._find_fir_record(record.get("fir_id", fir_id))
                if refreshed:
                    pdf_path = refreshed.get("pdf_path")
                    pdf_url = refreshed.get("pdf_url")

        if not pdf_path and not pdf_url:
            raise ValueError(f"PDF for FIR {fir_id} not ready")

        return pdf_path, pdf_url

    async def _find_fir_record(self, fir_id: str) -> dict | None:
        """Find FIR record by exact id, then case-insensitive fallback."""
        record = await self.db.fir_reports.find_one({"fir_id": fir_id})
        if record:
            return record

        return await self.db.fir_reports.find_one(
            {"fir_id": {"$regex": f"^{re.escape(fir_id)}$", "$options": "i"}}
        )

    async def _recover_legacy_pdf(self, record: dict) -> str:
        """
        Rebuild PDF for older finalized records that lost pdf_path/pdf_url metadata.
        Returns recovered cloud URL or empty string on failure.
        """
        try:
            analysis_id = record.get("analysis_id")
            if not analysis_id:
                logger.warning("Legacy FIR recovery skipped: missing analysis_id for %s", record.get("fir_id"))
                return ""

            fallback_incident_date = datetime.utcnow().strftime("%Y-%m-%d")
            payload = FinalizeFIRRequest(
                fir_id=record.get("fir_id", ""),
                analysis_id=analysis_id,
                complainant_name=record.get("complainant_name") or "Unknown",
                complainant_contact=record.get("complainant_contact") or "Not Provided",
                complainant_address=record.get("complainant_address") or "",
                accused_name=record.get("accused_name") or "",
                accused_details=record.get("accused_details") or "",
                incident_date=record.get("incident_date") or fallback_incident_date,
                incident_time=record.get("incident_time") or "",
                incident_location=record.get("incident_location") or "",
                additional_info=record.get("additional_info") or "",
                legal_sections=record.get("legal_sections") or [],
                evidence_urls=record.get("evidence_urls") or [],
            )

            return await self.generate_fir_pdf(payload)
        except Exception as e:
            logger.warning("Legacy FIR recovery failed for %s: %s", record.get("fir_id"), e)
            return ""

    # ── Get FIR history ──────────────────────────────────────────
    async def get_fir_history(self, limit: int = 50, skip: int = 0):
        """Fetch FIR history sorted by creation date (newest first)"""
        firs = await self.db.fir_reports.find(
            {},
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit,
        ).to_list(length=limit)
        
        total = await self.db.fir_reports.count_documents({})
        
        # Convert to response format
        history_items = []
        for fir in firs:
            history_items.append({
                "fir_id": fir.get("fir_id"),
                "status": fir.get("status", "draft"),
                "complainant_name": fir.get("complainant_name", "—"),
                "accused_name": fir.get("accused_name"),
                "incident_date": fir.get("incident_date", "—"),
                "incident_location": fir.get("incident_location"),
                "created_at": fir.get("created_at"),
                "finalized_at": fir.get("finalized_at"),
                "pdf_url": fir.get("pdf_url"),
            })
        
        return {"firs": history_items, "total": total}

    # ── ReportLab PDF builder ─────────────────────────────────────
    def _build_pdf(
        self,
        pdf_path: Path,
        data: FinalizeFIRRequest,
        analysis: dict | None,
    ) -> None:
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        story = []

        # ── Custom styles ─────────────────────────────────────────
        title_style = ParagraphStyle(
            "FIRTitle",
            fontSize=16,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.HexColor("#1a1a2e"),
        )
        subtitle_style = ParagraphStyle(
            "FIRSubtitle",
            fontSize=11,
            fontName="Helvetica",
            alignment=TA_CENTER,
            spaceAfter=4,
            textColor=colors.HexColor("#4a4a6a"),
        )
        section_style = ParagraphStyle(
            "Section",
            fontSize=10,
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=4,
            textColor=colors.HexColor("#c0392b"),
            borderPad=4,
        )
        body_style = ParagraphStyle(
            "Body",
            fontSize=9,
            fontName="Helvetica",
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#2c2c2c"),
        )
        mono_style = ParagraphStyle(
            "Mono",
            fontSize=8,
            fontName="Courier",
            textColor=colors.HexColor("#555555"),
            leading=12,
        )

        # ── Header ────────────────────────────────────────────────
        story.append(Paragraph("FIRST INFORMATION REPORT (FIR)", title_style))
        story.append(Paragraph("Under the Information Technology Act, 2000 & Indian Penal Code", subtitle_style))
        story.append(Paragraph("Generated by SafeGuard AI Platform", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#c0392b")))
        story.append(Spacer(1, 0.4 * cm))

        # ── FIR metadata table ────────────────────────────────────
        ist_now = get_ist_now()
        meta_data = [
            ["FIR Number:", data.fir_id, "Date:", ist_now.strftime("%d %B %Y")],
            ["Time of Filing:", ist_now.strftime("%H:%M IST"), "Case ID:", data.analysis_id[:16] + "..."],
        ]
        meta_table = Table(meta_data, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 4 * cm])
        meta_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8f8f8"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 0.5 * cm))

        # ── Complainant Details ───────────────────────────────────
        story.append(Paragraph("1. COMPLAINANT DETAILS", section_style))
        comp_data = [
            ["Name:", data.complainant_name],
            ["Contact:", data.complainant_contact],
        ]
        if data.complainant_address:
            comp_data.append(["Address:", data.complainant_address])
        
        comp_table = Table(comp_data, colWidths=[4 * cm, 13 * cm])
        comp_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(comp_table)
        
        # ── Accused/Respondent Details ────────────────────────────
        if data.accused_name or data.accused_details:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph("2. AGAINST WHOM (ACCUSED/RESPONDENT)", section_style))
            accused_data = []
            if data.accused_name:
                accused_data.append(["Name/Account:", data.accused_name])
            if data.accused_details:
                accused_data.append(["Username/Profile:", data.accused_details])
            
            if accused_data:
                accused_table = Table(accused_data, colWidths=[4 * cm, 13 * cm])
                accused_table.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(accused_table)
            section_num = 3
        else:
            section_num = 2

        # ── Incident Details ─────────────────────────────────────
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"{section_num}. INCIDENT DETAILS", section_style))
        incident_data = [
            ["Date:", data.incident_date],
            ["Time (IST):", data.incident_time or "Not Specified"],
            ["Location:", data.incident_location or "Online Platform"],
        ]
        incident_table = Table(incident_data, colWidths=[4 * cm, 13 * cm])
        incident_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(incident_table)

        # ── AI Analysis Summary ───────────────────────────────────
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"{section_num + 1}. AI ANALYSIS SUMMARY", section_style))

        if analysis:
            risk = analysis.get("risk_level", "UNKNOWN")
            risk_color = {
                "LOW": "#27ae60", "MEDIUM": "#f39c12",
                "HIGH": "#e67e22", "CRITICAL": "#c0392b"
            }.get(risk, "#888888")

            ai_data = [
                ["Risk Level:", risk, "Overall Score:", f"{analysis.get('overall_score', 0)*100:.1f}%"],
                ["Language:", analysis.get("language_detected", "Unknown"), "Timestamp:", str(analysis.get("timestamp", ""))[:19]],
            ]
            ai_table = Table(ai_data, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 4 * cm])
            ai_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor(risk_color)),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(ai_table)
            story.append(Spacer(1, 0.2 * cm))

            # Category scores
            labels = analysis.get("labels", {})
            if labels:
                scores_data = [["Category", "Score", "Category", "Score"]]
                items = list(labels.items())
                for i in range(0, len(items), 2):
                    row = [items[i][0].replace("_", " ").title(), f"{items[i][1]*100:.1f}%"]
                    if i + 1 < len(items):
                        row += [items[i+1][0].replace("_", " ").title(), f"{items[i+1][1]*100:.1f}%"]
                    else:
                        row += ["—", "—"]
                    scores_data.append(row)

                scores_table = Table(scores_data, colWidths=[5 * cm, 3 * cm, 5 * cm, 3 * cm])
                scores_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c0392b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fef9f9"), colors.white]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(scores_table)

        # ── Incident Description ──────────────────────────────────
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"{section_num + 2}. INCIDENT DESCRIPTION & EVIDENCE", section_style))
        original_text = analysis.get("original_text", "N/A") if analysis else "N/A"
        story.append(Paragraph(
            f"The following content was submitted for analysis and flagged as harmful:<br/><br/>"
            f'<font name="Courier" size="8" color="#555555">"{original_text[:800]}"</font>',
            body_style
        ))

        if data.additional_info:
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph("<b>Complainant's Description of Incident:</b>", body_style))
            story.append(Paragraph(data.additional_info, body_style))

        # ── Legal Sections ────────────────────────────────────────
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"{section_num + 3}. APPLICABLE LEGAL PROVISIONS", section_style))

        if data.legal_sections:
            legal_data = [["#", "Legal Section / Provision"]]
            for i, section in enumerate(data.legal_sections, 1):
                legal_data.append([str(i), section])

            legal_table = Table(legal_data, colWidths=[1 * cm, 16 * cm])
            legal_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(legal_table)
        else:
            story.append(Paragraph("No specific legal sections mapped.", body_style))

        # ── Evidence URLs ─────────────────────────────────────────
        if data.evidence_urls:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(f"{section_num + 4}. DIGITAL EVIDENCE / SUPPORTING DOCUMENTS", section_style))
            for i, url in enumerate(data.evidence_urls, 1):
                story.append(Paragraph(f"{i}. {url}", mono_style))

        # ── AI Explanation ────────────────────────────────────────
        if analysis and analysis.get("explanation"):
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(f"{section_num + 5}. AI REASONING & EXPLAINABILITY", section_style))
            story.append(Paragraph(analysis["explanation"], body_style))

        # ── Declaration ───────────────────────────────────────────
        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            "DECLARATION: I, the complainant, hereby declare that the information provided above is "
            "true and correct to the best of my knowledge. This FIR has been generated using the "
            "SafeGuard AI platform with AI-assisted evidence analysis. The AI analysis is provided "
            "as supporting evidence and does not substitute for official law enforcement investigation.",
            ParagraphStyle("Decl", fontSize=7, fontName="Helvetica", alignment=TA_JUSTIFY,
                           textColor=colors.HexColor("#666666"), leading=11)
        ))
        story.append(Spacer(1, 0.8 * cm))

        # Signature line
        sig_data = [
            ["Complainant Signature", "", "Date"],
            [data.complainant_name, "", data.incident_date],
        ]
        sig_table = Table(sig_data, colWidths=[7 * cm, 3 * cm, 7 * cm])
        sig_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LINEABOVE", (0, 0), (0, 0), 1, colors.black),
            ("LINEABOVE", (2, 0), (2, 0), 1, colors.black),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(sig_table)

        # Footer note
        story.append(Spacer(1, 0.5 * cm))
        ist_now = get_ist_now()
        story.append(Paragraph(
            f"Generated by SafeGuard AI | FIR ID: {data.fir_id} | {ist_now.strftime('%Y-%m-%d %H:%M IST')}",
            ParagraphStyle("Footer", fontSize=6, fontName="Helvetica",
                           alignment=TA_CENTER, textColor=colors.HexColor("#aaaaaa"))
        ))

        doc.build(story)
        logger.info("PDF built: %s", pdf_path)
