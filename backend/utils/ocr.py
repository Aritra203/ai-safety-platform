"""
OCR utility — extracts text from image bytes using Tesseract + PaddleOCR fallback.
Preprocesses images for better handwriting detection.
Falls back to empty string on failure.
"""

import logging
from io import BytesIO

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
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

        # Normalize orientation metadata if present.
        image = ImageOps.exif_transpose(image)

        # Convert to grayscale and upscale small inputs to help handwritten OCR.
        image = image.convert("L")
        w, h = image.size
        if max(w, h) < 1400:
            image = image.resize((int(w * 2), int(h * 2)), resample=Image.Resampling.LANCZOS)

        # Improve contrast and local edges for pen-stroke text.
        image = ImageOps.autocontrast(image)
        image = ImageEnhance.Contrast(image).enhance(1.8)
        image = image.filter(ImageFilter.MedianFilter(size=3))

        return image
    except Exception as e:
        logger.warning("Image preprocessing failed (%s), proceeding without it", e)
        return image


def _pil_to_jpg_bytes(image: "Image") -> bytes:
    """Encode PIL image to jpg bytes for OCR engines expecting file input."""
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def _crop_text_region(image):
    """Crop likely text region to improve OCR on images with large empty margins."""
    try:
        import cv2
        import numpy as np

        gray = np.array(image.convert("L"))
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 80:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if w < 8 or h < 8:
                continue
            boxes.append((x, y, w, h))

        if not boxes:
            return image

        x1 = min(b[0] for b in boxes)
        y1 = min(b[1] for b in boxes)
        x2 = max(b[0] + b[2] for b in boxes)
        y2 = max(b[1] + b[3] for b in boxes)

        pad = 24
        img_w, img_h = image.size
        left = max(0, x1 - pad)
        top = max(0, y1 - pad)
        right = min(img_w, x2 + pad)
        bottom = min(img_h, y2 + pad)

        if right - left < 30 or bottom - top < 20:
            return image

        return image.crop((left, top, right, bottom))
    except Exception as e:
        logger.warning("Text region crop skipped: %s", e)
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

        original_image = image.copy()
        processed_image = _preprocess_image(image)
        cropped_image = _crop_text_region(processed_image)

        # Try Tesseract on processed image, then on original image.
        text = _extract_with_tesseract(processed_image)
        if not text:
            text = _extract_with_tesseract(cropped_image)
        if not text:
            text = _extract_with_tesseract(original_image)
        
        # If Tesseract yields nothing, fallback to PaddleOCR on processed then original image.
        if not text:
            logger.info("Tesseract failed, attempting PaddleOCR fallback...")
            text = _extract_with_paddle(_pil_to_jpg_bytes(processed_image))
        if not text:
            text = _extract_with_paddle(_pil_to_jpg_bytes(cropped_image))
        if not text:
            text = _extract_with_paddle(image_bytes)

        logger.info("Final OCR result: %d characters extracted", len(text))
        return text

    except ImportError as e:
        logger.error("Required OCR dependencies not installed: %s", e)
        return ""
    except Exception as e:
        logger.error("OCR pipeline failed: %s", e)
        return ""
