"""
ToxicityClassifier — Multi-label harmful content classification.

Uses a HuggingFace transformer (unitary/toxic-bert by default) plus
a rule-based augmentation layer for Hinglish / obfuscated text.

Output: dict of category → float probability in [0, 1].
"""

import logging
import re
from functools import lru_cache
from typing import Dict

logger = logging.getLogger(__name__)

# ── HuggingFace model label → our category mapping ───────────────
# For binary models (toxic/not_toxic): distribute across categories
# For multi-label models: direct mapping
HF_LABEL_MAP = {
    "toxic": "cyberbullying",  # Fallback for binary classifier
    "severe_toxic": "threat",
    "obscene": "sexual_harassment",
    "threat": "threat",
    "insult": "cyberbullying",
    "identity_hate": "hate_speech",
}

# ── Rule-based keyword signals ────────────────────────────────────
KEYWORD_RULES: Dict[str, list] = {
    "threat": [
        r"\bkill\b", r"\bhurt\b", r"\bdekhna\b", r"\bdekh lena\b",
        r"\bwatch your back\b", r"\bregret\b", r"\bwon't forgive\b",
        r"\bmaar\b", r"\bjaan se\b", r"\bkhatam\b",
        r"\bdeath\b", r"\bdie\b", r"\beliminate\b",
        r"\bno right to live\b", r"\bshould be dead\b", r"\bdeserves death\b",
        r"\bwipe out\b", r"\bexterminate\b",
    ],
    "cyberbullying": [
        r"\bloser\b", r"\bstupid\b", r"\bidiot\b", r"\bbewakoof\b",
        r"\bchutiya\b", r"\bsala\b", r"\bkamina\b", r"\bdesperate\b",
        r"\bfool\b", r"\bdumb\b", r"\bworthless\b", r"\bgay\b",
        r"\bmother[f-]ucker\b", r"\basshole\b", r"\bbitch\b",
    ],
    "hate_speech": [
        r"\bterrorist\b", r"\bcommunal\b", r"\bjihadi\b",
        r"\blanat\b", r"\bkaafir\b", r"\bpig\b",
        r"\bhate\b", r"\bMuslim\b", r"\bHindu\b", r"\bChristian\b", r"\bJew\b",
        r"\bscum\b", r"\bunholy\b", r"\binfidel\b",
    ],
    "sexual_harassment": [
        r"\bsexy\b", r"\bnude\b", r"\bsend pics\b", r"\bphoto bhejo\b",
        r"\bvideo call\b", r"\bkoi dekhega nahi\b",
        r"\bsuck\b", r"\bfucker\b", r"\bass\b", r"\bcock\b", r"\bpussy\b",
        r"\bfuck\b", r"\bblowjob\b", r"\bsex\b", r"\bporn\b",
        r"\brape\b", r"\bsexual\b", r"\bgrope\b",
    ],
}


class ToxicityClassifier:
    def __init__(self):
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        try:
            from transformers import pipeline as hf_pipeline
            from config.settings import settings

            logger.info("Loading HuggingFace toxicity model: %s", settings.HF_MODEL_NAME)
            self.pipeline = hf_pipeline(
                "text-classification",
                model=settings.HF_MODEL_NAME,
                tokenizer=settings.HF_MODEL_NAME,
                device=-1,  # CPU; set to 0 for GPU
                top_k=None,
                truncation=True,
                max_length=512,
            )
            logger.info("✅ Toxicity model loaded")
        except Exception as e:
            logger.warning("HuggingFace model unavailable (%s) — using rule-only mode", e)
            self.pipeline = None

    def classify(self, text: str) -> Dict[str, float]:
        scores: Dict[str, float] = {
            "cyberbullying": 0.0,
            "threat": 0.0,
            "hate_speech": 0.0,
            "sexual_harassment": 0.0,
        }

        # 1. Rule-based category detection (run FIRST to identify which categories apply)
        category_hits: Dict[str, int] = {}
        for category, patterns in KEYWORD_RULES.items():
            hits = sum(
                1 for p in patterns
                if re.search(p, text, re.IGNORECASE)
            )
            if hits > 0:
                category_hits[category] = hits

        # 2. Transformer model scores
        model_score = 0.0
        if self.pipeline:
            try:
                outputs = self.pipeline(text[:512])
                for item in outputs[0]:
                    label = item["label"].lower()
                    score = float(item["score"])
                    
                    # For "toxic" label: apply to categories that matched rules
                    if label == "toxic" and category_hits:
                        model_score = score
                    # For specific labels (multi-label models): direct mapping
                    else:
                        mapped = HF_LABEL_MAP.get(label)
                        if mapped and score > scores.get(mapped, 0):
                            scores[mapped] = round(score, 4)
            except Exception as e:
                logger.warning("Transformer inference error: %s", e)

        # 3. Apply model score to detected categories
        if model_score > 0 and category_hits:
            for category, hits in category_hits.items():
                # Boost based on hit count, but model score is primary
                boost = min(hits * 0.05, 0.15)
                combined = min(model_score + boost, 1.0)
                scores[category] = round(max(scores.get(category, 0.0), combined), 4)
        else:
            # Fallback: apply rule-based boost if no model score
            for category, hits in category_hits.items():
                boost = min(hits * 0.15, 0.45)
                scores[category] = round(min(scores.get(category, 0.0) + boost, 1.0), 4)

        return scores
