"""
CloudinaryService — wraps cloudinary SDK for file uploads.
All media and PDFs are stored here; only URL + public_id are kept in DB.
"""

import asyncio
import logging
import os
import tempfile
from io import BytesIO

import cloudinary
import cloudinary.uploader

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Configure Cloudinary SDK once
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


class CloudinaryService:
    # ── Upload raw bytes (images) ─────────────────────────────────
    async def upload_bytes(
        self,
        file_bytes: bytes,
        folder: str = "evidence",
        filename: str = "upload",
    ) -> str:
        """Upload image bytes to Cloudinary; return secure URL."""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._sync_upload_bytes,
            file_bytes,
            folder,
            filename,
        )

    def _sync_upload_bytes(self, file_bytes: bytes, folder: str, filename: str) -> str:
        try:
            result = cloudinary.uploader.upload(
                BytesIO(file_bytes),
                folder=folder,
                public_id=os.path.splitext(filename)[0],
                resource_type="image",
                overwrite=False,
                unique_filename=True,
            )
            url = result.get("secure_url", "")
            logger.info("Cloudinary upload OK: %s", url)
            return url
        except Exception as e:
            logger.error("Cloudinary upload failed: %s", e)
            return ""

    # ── Upload file path (PDFs) ───────────────────────────────────
    async def upload_file(
        self,
        file_path: str,
        folder: str = "fir_reports",
        resource_type: str = "raw",
        public_id: str | None = None,
    ) -> str:
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._sync_upload_file,
            file_path,
            folder,
            resource_type,
            public_id,
        )

    def _sync_upload_file(
        self,
        file_path: str,
        folder: str,
        resource_type: str,
        public_id: str | None,
    ) -> str:
        try:
            kwargs: dict = {
                "folder": folder,
                "resource_type": resource_type,
                "overwrite": True,
            }
            if public_id:
                kwargs["public_id"] = public_id

            result = cloudinary.uploader.upload(file_path, **kwargs)
            url = result.get("secure_url", "")
            logger.info("Cloudinary file upload OK: %s", url)
            return url
        except Exception as e:
            logger.error("Cloudinary file upload failed: %s", e)
            return ""
