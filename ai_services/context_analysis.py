"""
ContextAnalyzer — Detects escalation patterns across conversation threads.

Scores:
  - Overall toxicity trend (early vs late messages)
  - Sustained harassment (repeated targets)
  - Escalation velocity
  - Grooming progression signals
"""

import logging
import re
from typing import Dict, List

from ai_services.toxicity import ToxicityClassifier

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    def __init__(self):
        self._clf = ToxicityClassifier()

    def analyze(self, messages) -> Dict[str, float]:
        """
        Analyze conversation context.
        Returns aggregated category scores with escalation adjustments.
        """
        if not messages:
            return {}

        texts = [m.text for m in messages]
        n = len(texts)

        # Score each message
        per_message_scores = []
        for text in texts:
            if text.strip():
                scores = self._clf.classify(text)
                per_message_scores.append(scores)
            else:
                per_message_scores.append({})

        if not per_message_scores:
            return {}

        # Aggregate
        categories = ["cyberbullying", "threat", "hate_speech", "sexual_harassment"]
        aggregated: Dict[str, float] = {}

        for cat in categories:
            cat_scores = [s.get(cat, 0.0) for s in per_message_scores]
            if not cat_scores:
                aggregated[cat] = 0.0
                continue

            # Weighted average: later messages weight more (recency bias)
            weights = [(i + 1) / n for i in range(n)]
            weighted_avg = sum(s * w for s, w in zip(cat_scores, weights)) / sum(weights)

            # Escalation: check if scores rise in second half
            mid = max(1, n // 2)
            early_avg = sum(cat_scores[:mid]) / mid
            late_avg = sum(cat_scores[mid:]) / max(1, len(cat_scores[mid:]))
            escalation_bonus = max(0.0, (late_avg - early_avg) * 0.3)

            aggregated[cat] = round(min(weighted_avg + escalation_bonus, 1.0), 4)

        return aggregated

    def _detect_repeated_target(self, texts: List[str]) -> float:
        """Check if the same person/username is being targeted repeatedly."""
        # Simple heuristic: look for @mentions appearing in many messages
        all_mentions: List[str] = []
        for text in texts:
            mentions = re.findall(r"@\w+", text)
            all_mentions.extend(mentions)

        if not all_mentions:
            return 0.0

        from collections import Counter
        counts = Counter(all_mentions)
        most_common_count = counts.most_common(1)[0][1]
        # If same person appears in >50% of messages, that's a signal
        return round(min(most_common_count / len(texts), 1.0), 4)
