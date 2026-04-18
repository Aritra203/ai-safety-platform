"""
AnalysisService — orchestrates the full AI pipeline:
  1. Language detection & normalization
  2. Multi-label toxicity classification
  3. Grooming pattern detection
  4. Explainability (token attribution)
  5. Risk scoring
  6. Legal mapping
  7. Persist to MongoDB
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import List

from models.schemas import (
    AnalysisResponse,
    CategoryScores,
    ConversationMessage,
    LegalMapping,
    ToxicToken,
)
from ai_services.toxicity import ToxicityClassifier
from ai_services.grooming_detection import GroomingDetector
from ai_services.context_analysis import ContextAnalyzer
from ai_services.multilingual_processing import MultilingualProcessor
from utils.legal_mapper import LegalMapper
from utils.risk_engine import RiskEngine
from utils.explainability import ExplainabilityEngine

logger = logging.getLogger(__name__)

# ── Singletons (loaded once on first use) ────────────────────────
_toxicity_clf: ToxicityClassifier | None = None
_grooming_det: GroomingDetector | None = None
_context_ana: ContextAnalyzer | None = None
_multilingual: MultilingualProcessor | None = None
_legal_mapper = LegalMapper()
_risk_engine = RiskEngine()
_explainer = ExplainabilityEngine()


def _get_toxicity() -> ToxicityClassifier:
    global _toxicity_clf
    if _toxicity_clf is None:
        _toxicity_clf = ToxicityClassifier()
    return _toxicity_clf


def _get_grooming() -> GroomingDetector:
    global _grooming_det
    if _grooming_det is None:
        _grooming_det = GroomingDetector()
    return _grooming_det


def _get_context() -> ContextAnalyzer:
    global _context_ana
    if _context_ana is None:
        _context_ana = ContextAnalyzer()
    return _context_ana


def _get_multilingual() -> MultilingualProcessor:
    global _multilingual
    if _multilingual is None:
        _multilingual = MultilingualProcessor()
    return _multilingual


class AnalysisService:
    def __init__(self, db):
        self.db = db

    # ── Text analysis ─────────────────────────────────────────────
    async def analyze_text(self, text: str) -> AnalysisResponse:
        return await asyncio.get_event_loop().run_in_executor(
            None, self._sync_analyze_text, text, None
        )

    # ── Image analysis ────────────────────────────────────────────
    async def analyze_image(self, image_bytes: bytes, image_url: str) -> AnalysisResponse:
        from utils.ocr import extract_text_from_image
        extracted_text = await asyncio.get_event_loop().run_in_executor(
            None, extract_text_from_image, image_bytes
        )
        if not extracted_text.strip():
            extracted_text = "[No text detected in image]"

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._sync_analyze_text, extracted_text, image_url
        )
        result.image_url = image_url
        return result

    # ── Conversation context analysis ─────────────────────────────
    async def analyze_context(self, messages: List[ConversationMessage]) -> AnalysisResponse:
        return await asyncio.get_event_loop().run_in_executor(
            None, self._sync_analyze_context, messages
        )

    # ── Internal sync pipeline ────────────────────────────────────
    def _sync_analyze_text(self, text: str, image_url: str | None) -> AnalysisResponse:
        multilingual = _get_multilingual()
        toxicity_clf = _get_toxicity()
        grooming_det = _get_grooming()

        # 1. Language detection + normalization
        lang, normalized_text = multilingual.process(text)
        logger.info("Language: %s | Normalized length: %d", lang, len(normalized_text))

        # 2. Multi-label toxicity scores
        scores: dict = toxicity_clf.classify(normalized_text)

        # 3. Grooming check
        grooming_score = grooming_det.score(normalized_text)
        scores["grooming"] = grooming_score

        # 4. Token-level explainability
        toxic_tokens: List[ToxicToken] = _explainer.highlight_tokens(
            normalized_text, scores
        )

        # 5. Highlighted HTML
        highlighted_html = _explainer.build_highlighted_html(
            normalized_text, toxic_tokens
        )

        # 6. Risk level
        risk_level, overall_score = _risk_engine.compute(scores)

        # 7. Legal mapping
        legal_mappings: List[LegalMapping] = _legal_mapper.map(scores, risk_level)

        # 8. Human-readable explanation
        explanation = _build_explanation(scores, risk_level, lang)

        result = AnalysisResponse(
            id=str(uuid.uuid4()),
            risk_level=risk_level,
            overall_score=overall_score,
            labels=CategoryScores(**{k: v for k, v in scores.items() if k in CategoryScores.model_fields}),
            toxic_tokens=toxic_tokens,
            original_text=text,
            highlighted_text=highlighted_html,
            legal_mappings=legal_mappings,
            explanation=explanation,
            timestamp=datetime.utcnow(),
            language_detected=lang,
            image_url=image_url,
        )

        # Persist (fire and forget in sync context — stored after return)
        self._persist_sync(result)
        return result

    def _sync_analyze_context(self, messages: List[ConversationMessage]) -> AnalysisResponse:
        context_analyzer = _get_context()
        # Merge all texts for baseline toxicity
        combined_text = " ".join(m.text for m in messages)

        # Run context-aware scoring (escalation detection)
        ctx_scores = context_analyzer.analyze(messages)

        # Also run base toxicity on combined
        baseline = _get_toxicity().classify(combined_text)
        # Merge: context scores can amplify baseline
        for key in baseline:
            ctx_scores[key] = max(ctx_scores.get(key, 0.0), baseline[key])

        grooming_score = _get_grooming().score_conversation(messages)
        ctx_scores["grooming"] = grooming_score

        lang, _ = _get_multilingual().process(combined_text)
        toxic_tokens = _explainer.highlight_tokens(combined_text, ctx_scores)
        highlighted_html = _explainer.build_highlighted_html(combined_text, toxic_tokens)
        risk_level, overall_score = _risk_engine.compute(ctx_scores)
        legal_mappings = _legal_mapper.map(ctx_scores, risk_level)
        explanation = _build_explanation(ctx_scores, risk_level, lang, is_context=True)

        result = AnalysisResponse(
            id=str(uuid.uuid4()),
            risk_level=risk_level,
            overall_score=overall_score,
            labels=CategoryScores(**{k: v for k, v in ctx_scores.items() if k in CategoryScores.model_fields}),
            toxic_tokens=toxic_tokens,
            original_text=combined_text,
            highlighted_text=highlighted_html,
            legal_mappings=legal_mappings,
            explanation=explanation,
            timestamp=datetime.utcnow(),
            language_detected=lang,
        )
        self._persist_sync(result)
        return result

    def _persist_sync(self, result: AnalysisResponse) -> None:
        """Best-effort MongoDB persistence (non-blocking)."""
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                self.db.analyses.insert_one(result.model_dump())
            )
            loop.close()
        except Exception as e:
            logger.warning("Persistence skipped: %s", e)


# ── Helpers ───────────────────────────────────────────────────────
def _build_explanation(
    scores: dict,
    risk_level: str,
    lang: str,
    is_context: bool = False,
) -> str:
    top = sorted(
        [(k, v) for k, v in scores.items() if v > 0.15],
        key=lambda x: x[1],
        reverse=True,
    )[:3]

    if not top:
        return "No significant harmful content detected in this text."

    prefix = "Across the conversation thread, " if is_context else ""
    categories = ", ".join(
        f"{k.replace('_', ' ')} ({v*100:.0f}%)" for k, v in top
    )
    lang_note = f" Content was detected in {lang}." if lang != "en" else ""

    return (
        f"{prefix}The AI flagged this content at {risk_level} risk level. "
        f"Primary concerns: {categories}.{lang_note} "
        f"The model identified specific linguistic patterns associated with harm. "
        f"Review highlighted tokens for evidence details."
    )
