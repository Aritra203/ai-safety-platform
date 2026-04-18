"""
RiskEngine — converts category probability scores to a risk level.

Scoring logic:
  - Compute a weighted composite score
  - Grooming & threat carry higher weight
  - Map composite to LOW / MEDIUM / HIGH / CRITICAL
"""

from typing import Dict, Tuple

# ── Category weights ──────────────────────────────────────────────
CATEGORY_WEIGHTS = {
    "grooming": 1.5,
    "threat": 1.3,
    "sexual_harassment": 1.2,
    "hate_speech": 1.0,
    "cyberbullying": 0.9,
}

# ── Risk thresholds ───────────────────────────────────────────────
THRESHOLDS = [
    (0.75, "CRITICAL"),
    (0.50, "HIGH"),
    (0.25, "MEDIUM"),
    (0.0,  "LOW"),
]


class RiskEngine:
    def compute(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """
        Returns (risk_level, overall_score) where overall_score ∈ [0, 1].
        """
        if not scores:
            return "LOW", 0.0

        # Weighted composite
        weighted_sum = 0.0
        weight_total = 0.0
        for cat, score in scores.items():
            w = CATEGORY_WEIGHTS.get(cat, 1.0)
            weighted_sum += score * w
            weight_total += w

        overall = round(weighted_sum / max(weight_total, 1.0), 4)

        # Check if any single category is critically high (override)
        if scores.get("grooming", 0) > 0.7 or scores.get("threat", 0) > 0.85:
            return "CRITICAL", max(overall, 0.75)

        for threshold, level in THRESHOLDS:
            if overall >= threshold:
                return level, overall

        return "LOW", overall
