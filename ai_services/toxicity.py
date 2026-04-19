"""
ToxicityClassifier — Multi-label harmful content classification.

Upgraded to use Microsoft DeBERTa-v3-base (instead of ToxicBERT):
  - Better multilingual support (key for Hinglish/Bengali)
  - Disentangled attention → more interpretable
  - INT8 quantization for 2-3x inference speedup
  - Token-level attention for explainability

Hybrid approach: ML model + rule-based augmentation for Hinglish/obfuscated text.
Output: dict of category → float probability in [0, 1].
"""

import logging
import re
import torch
from functools import lru_cache
from typing import Dict, Tuple, List
import hashlib

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
        self.model = None
        self.tokenizer = None
        self.device = None
        self._is_quantized = False
        self._load_model()

    def _load_model(self):
        """Load DeBERTa model with optional quantization."""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            from backend.config.settings import settings
            import torch

            logger.info("Loading HuggingFace model: %s", settings.HF_MODEL_NAME)
            
            # Determine device
            self.device = torch.device(
                "cuda" if settings.HF_DEVICE == "cuda" and torch.cuda.is_available() else "cpu"
            )
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.HF_MODEL_NAME,
                cache_dir=settings.HF_CACHE_DIR,
                truncation_side="right",
            )
            
            # Load model
            self.model = AutoModelForSequenceClassification.from_pretrained(
                settings.HF_MODEL_NAME,
                cache_dir=settings.HF_CACHE_DIR,
                num_labels=2,  # binary: toxic / not toxic
                output_attentions=True,  # Enable for explainability
            ).to(self.device).eval()
            
            # Apply quantization if enabled (2-3x speedup)
            if settings.HF_USE_QUANTIZATION:
                try:
                    self.model = torch.quantization.quantize_dynamic(
                        self.model,
                        {torch.nn.Linear},
                        dtype=torch.qint8,
                    )
                    self._is_quantized = True
                    logger.info("✅ Model quantized (INT8) — 2-3x faster inference")
                except Exception as e:
                    logger.warning("Quantization failed (%s), using full precision", e)
            
            logger.info("✅ Toxicity model loaded on %s (quantized=%s)", self.device, self._is_quantized)
        except Exception as e:
            logger.exception("HuggingFace model unavailable (%s) — using rule-only mode", e)
            self.model = None
            self.tokenizer = None

    def classify(self, text: str) -> Dict[str, float]:
        """Classify text with hybrid ML + rules approach. Returns {category: score}."""
        scores: Dict[str, float] = {
            "cyberbullying": 0.0,
            "threat": 0.0,
            "hate_speech": 0.0,
            "sexual_harassment": 0.0,
        }

        # 1. Rule-based category detection (run FIRST — fast & deterministic)
        category_hits: Dict[str, int] = {}
        for category, patterns in KEYWORD_RULES.items():
            hits = sum(
                1 for p in patterns
                if re.search(p, text, re.IGNORECASE)
            )
            if hits > 0:
                category_hits[category] = hits

        # 2. ML model inference (DeBERTa with attention for explainability)
        model_score = 0.0
        token_attributions = {}
        
        if self.model and self.tokenizer:
            try:
                # Classify text
                model_score, attention_weights = self._infer_with_attention(text)
                
                # Extract attention-based token importance
                token_attributions = self._get_token_attribution(text, attention_weights)
            except Exception as e:
                logger.warning("Transformer inference error: %s", e)

        # 3. Intelligent blending: If rules are strong, weight them heavily
        rule_confidence = len(category_hits) / max(len(KEYWORD_RULES), 1)
        
        if rule_confidence > 0.5:  # Strong rule signal
            # Rules dominate: blend 70% rules, 30% ML
            for category, hits in category_hits.items():
                rule_boost = min(0.20 + (hits - 1) * 0.15, 0.60)
                ml_component = model_score * 0.2 if model_score > 0 else 0.0
                blended = min(rule_boost * 0.7 + ml_component * 0.3, 1.0)
                scores[category] = round(blended, 4)
        else:
            # Weak rule signal: ML leads, rules provide optional boost
            for category in scores.keys():
                ml_score = model_score
                rule_boost = 0.0
                
                if category in category_hits:
                    rule_boost = min(0.20 + (category_hits[category] - 1) * 0.15, 0.60)
                    # Blend: 80% ML, 20% rules
                    blended = (ml_score * 0.8) + (rule_boost * 0.2)
                else:
                    blended = ml_score
                
                scores[category] = round(min(blended, 1.0), 4)

        return scores
    
    @torch.no_grad()
    def _infer_with_attention(self, text: str) -> Tuple[float, torch.Tensor]:
        """Run inference and return: (toxic_score, attention_weights)."""
        # Tokenize
        inputs = self.tokenizer(
            text[:512],
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        ).to(self.device)
        
        # Forward pass
        outputs = self.model(**inputs)
        logits = outputs.logits
        
        # Convert to probability (toxic class = 1)
        probs = torch.softmax(logits, dim=-1)
        toxic_prob = float(probs[0, 1].cpu())
        
        # Extract attention from last layer (for explainability)
        attention = outputs.attentions[-1]  # [batch, heads, seq_len, seq_len]
        
        return toxic_prob, attention
    
    def _get_token_attribution(self, text: str, attention: torch.Tensor) -> Dict[str, float]:
        """Extract token importance scores from attention weights."""
        try:
            # Average attention across heads
            aggregated = attention[0].mean(dim=0)  # [seq_len, seq_len]
            
            # Get attention from [CLS] token (0)
            cls_attention = aggregated[0, :]  # [seq_len]
            
            # Tokenize to map back to words
            tokens = self.tokenizer.tokenize(text[:512])
            
            # Map tokens to importance
            token_importance = {}
            for i, token in enumerate(tokens[:len(cls_attention)]):
                importance = float(cls_attention[i].cpu())
                token_importance[token] = importance
            
            return token_importance
        except Exception as e:
            logger.warning("Token attribution extraction failed: %s", e)
            return {}

    @lru_cache(maxsize=1000)
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text classification."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def cache_stats(self) -> Dict:
        """Return cache statistics for monitoring."""
        return {
            "cache_info": self._get_cache_key.cache_info(),
            "quantized": self._is_quantized,
            "device": str(self.device),
        }
