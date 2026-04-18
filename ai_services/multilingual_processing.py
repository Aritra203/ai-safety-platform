"""
MultilingualProcessor — Language detection and text normalization.

Handles:
  - Hindi (Devanagari)
  - Hinglish (Roman-script Hindi)
  - Bengali (বাংলা)
  - English
  - L33tspeak / obfuscation stripping

Uses langdetect for language identification.
"""

import logging
import re
import unicodedata
from typing import Tuple

logger = logging.getLogger(__name__)

# ── L33tspeak substitution map ────────────────────────────────────
L33T_MAP = {
    "0": "o", "1": "i", "3": "e", "4": "a",
    "5": "s", "6": "g", "7": "t", "8": "b", "@": "a",
    "$": "s", "!": "i", "|": "i",
}

# ── Common Hinglish abuse → English normalization ─────────────────
HINGLISH_NORM = {
    r"\bbc\b": "motherfucker",
    r"\bmc\b": "motherfucker",
    r"\bbk\b": "bastard",
    r"\bchutiya\b": "idiot",
    r"\bbewakoof\b": "stupid",
    r"\bgandu\b": "asshole",
    r"\bkamina\b": "scoundrel",
    r"\bmaar dalenge\b": "will kill",
    r"\bjaan se marunga\b": "will kill",
    r"\bkhatam kar dunga\b": "will finish off",
    r"\bchod dene\b": "abandon",
}

# ── Supported language codes ──────────────────────────────────────
SUPPORTED_LANGS = {"en", "hi", "bn", "ur"}


class MultilingualProcessor:
    def __init__(self):
        self._langdetect_available = self._check_langdetect()

    def _check_langdetect(self) -> bool:
        try:
            import langdetect
            return True
        except ImportError:
            logger.warning("langdetect not installed — defaulting to 'en'")
            return False

    def process(self, text: str) -> Tuple[str, str]:
        """
        Returns (language_code, normalized_text).
        """
        # 1. Detect language
        lang = self._detect_language(text)

        # 2. Strip l33tspeak obfuscation
        normalized = self._strip_leet(text)

        # 3. Normalize Hinglish tokens
        normalized = self._normalize_hinglish(normalized)

        # 4. Unicode normalisation
        normalized = unicodedata.normalize("NFC", normalized)

        # 5. Strip excessive whitespace / special chars
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return lang, normalized

    def _detect_language(self, text: str) -> str:
        if not self._langdetect_available:
            return self._heuristic_detect(text)
        try:
            from langdetect import detect
            lang = detect(text)
            return lang if lang in SUPPORTED_LANGS else lang  # pass through
        except Exception:
            return self._heuristic_detect(text)

    def _heuristic_detect(self, text: str) -> str:
        """Simple heuristic for language detection without langdetect."""
        devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
        bengali = sum(1 for c in text if "\u0980" <= c <= "\u09FF")
        total = max(len(text), 1)

        if devanagari / total > 0.15:
            return "hi"
        if bengali / total > 0.15:
            return "bn"
        return "en"

    def _strip_leet(self, text: str) -> str:
        """Replace l33t characters with their alphabetic equivalents."""
        result = []
        for char in text:
            result.append(L33T_MAP.get(char, char))
        return "".join(result)

    def _normalize_hinglish(self, text: str) -> str:
        """Replace common Hinglish abuse terms with English equivalents for better model performance."""
        for pattern, replacement in HINGLISH_NORM.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
