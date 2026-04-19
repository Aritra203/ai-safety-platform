"""
OCR utility — extracts text from image bytes using Tesseract + PaddleOCR fallback.
Preprocesses images for better handwriting detection.
Falls back to empty string on failure.
"""

import logging
from io import BytesIO
import numpy as np

logger = logging.getLogger(__name__)

# ── Lazy-load PaddleOCR (expensive, only on first use) ───────────────
_paddle_ocr = None


def _get_paddle_ocr():
    """Lazy-load PaddleOCR to avoid startup overhead."""
    global _paddle_ocr
    if _paddle_ocr is None:
        try:
            from paddleocr import PaddleOCR
            _paddle_ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            logger.info("✅ PaddleOCR initialized")
        except Exception as e:
            logger.warning("PaddleOCR unavailable (%s)", e)
            _paddle_ocr = False  # Mark as failed to avoid retry
    return _paddle_ocr if _paddle_ocr is not False else None


def _preprocess_image(image):
    """
    Preprocess image for better OCR accuracy.
    Handles contrast, deskew, and binarization for handwritten text.
    """
    try:
        from PIL import Image, ImageEnhance
        import cv2

        # Enhance contrast for better text visibility
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)  # 50% more contrast

        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)

        # Convert to numpy array for CV2 preprocessing
        img_array = np.array(image)
        
        # Denoise if it's a color image
        if len(img_array.shape) == 3:
            img_array = cv2.fastNlMeansDenoisingColored(img_array, None, h=10, templateWindowSize=7, searchWindowSize=21)
        else:
            img_array = cv2.fastNlMeansDenoising(img_array, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Convert back to PIL
        image = Image.fromarray(img_array)
        
        return image
    except Exception as e:
        logger.warning("Image preprocessing failed (%s), proceeding without it", e)
        return image


def _extract_with_tesseract(image: "Image") -> str:
    """
    Extract text using Tesseract OCR with enhanced PSM for handwriting.
    """
    try:
        import pytesseract

        # PSM 11: Sparse text with OSD (best for handwriting)
        # PSM 6: Assume single block of text (fallback)
        for psm in ["--psm 11", "--psm 6 --oem 3"]:
            try:
                text = pytesseract.image_to_string(
                    image,
                    lang="eng+hin+ben",
                    config=f"{psm} --dpi 300",
                )
                if text.strip():
                    logger.info("Tesseract extracted %d characters with %s", len(text.strip()), psm)
                    return text.strip()
            except pytesseract.pytesseract.TesseractError:
                continue
        
        logger.warning("Tesseract extraction yielded no text")
        return ""
    except Exception as e:
        logger.error("Tesseract extraction failed: %s", e)
        return ""


def _extract_with_paddle(image_bytes: bytes) -> str:
    """
    Extract text using PaddleOCR (better for handwriting & complex layouts).
    """
    try:
        paddle_ocr = _get_paddle_ocr()
        if paddle_ocr is None:
            return ""

        # Save image to temp file for PaddleOCR
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        try:
            result = paddle_ocr.ocr(tmp_path, cls=True)
            text_parts = []

            # PaddleOCR 3.x can return dict-based output; keep compatibility with list-based output too.
            if result and isinstance(result, list) and isinstance(result[0], dict):
                for page in result:
                    rec_texts = page.get("rec_texts") or []
                    text_parts.extend([t for t in rec_texts if t])
            else:
                for line in result or []:
                    for word_info in line:
                        if word_info and len(word_info) >= 2:
                            text_parts.append(word_info[1][0])
            
            text = " ".join(text_parts).strip()
            if text:
                logger.info("PaddleOCR extracted %d characters", len(text))
            return text
        finally:
            import os
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    except Exception as e:
        logger.warning("PaddleOCR extraction failed: %s", e)
        return ""


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image bytes using Tesseract + PaddleOCR fallback.
    Preprocesses image for improved handwriting detection.
    Supports English, Hindi (Devanagari), and Bengali.
    Returns extracted text or empty string on failure.
    """
    try:
        from PIL import Image

        image = Image.open(BytesIO(image_bytes))

        # Convert to RGB if needed (handles RGBA / P modes)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # Preprocess image for better OCR accuracy
        image = _preprocess_image(image)

        # Try Tesseract first (faster, multi-language support)
        text = _extract_with_tesseract(image)
        
        # If Tesseract yields nothing, fallback to PaddleOCR
        if not text:
            logger.info("Tesseract failed, attempting PaddleOCR fallback...")
            text = _extract_with_paddle(image_bytes)

        logger.info("Final OCR result: %d characters extracted", len(text))
        return text

    except ImportError as e:
        logger.error("Required OCR dependencies not installed: %s", e)
        return ""
    except Exception as e:
        logger.error("OCR pipeline failed: %s", e)
        return ""
