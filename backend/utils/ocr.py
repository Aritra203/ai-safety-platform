"""
OCR utility — extracts text from image bytes using Tesseract via pytesseract.
Falls back to empty string on failure.
"""

import logging
from io import BytesIO

logger = logging.getLogger(__name__)


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image bytes using Tesseract OCR.
    Supports English, Hindi (Devanagari), and Bengali.
    Returns extracted text or empty string on failure.
    """
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(BytesIO(image_bytes))

        # Convert to RGB if needed (handles RGBA / P modes)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # Try multi-language OCR: English + Hindi + Bengali
        try:
            text = pytesseract.image_to_string(
                image,
                lang="eng+hin+ben",
                config="--psm 6 --oem 3",
            )
        except pytesseract.pytesseract.TesseractError:
            # Fallback to English-only if language packs missing
            logger.warning("Multi-language OCR failed, falling back to eng")
            text = pytesseract.image_to_string(image, lang="eng")

        cleaned = text.strip()
        logger.info("OCR extracted %d characters", len(cleaned))
        return cleaned

    except ImportError:
        logger.error("pytesseract / Pillow not installed — OCR unavailable")
        return ""
    except Exception as e:
        logger.error("OCR failed: %s", e)
        return ""
