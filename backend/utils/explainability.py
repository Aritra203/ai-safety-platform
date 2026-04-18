"""
ExplainabilityEngine — token-level attribution for transparent AI decisions.

Highlights which specific words/phrases triggered the classification,
and generates annotated HTML for the frontend.
"""

import re
import html
from typing import Dict, List

from models.schemas import ToxicToken

# ── Token patterns per category (ordered by priority) ────────────
TOKEN_PATTERNS: Dict[str, List[tuple]] = {
    "threat": [
        (r"\b(kill|murder|hurt|attack|destroy|maarenge|jaan se)\b", 0.9),
        (r"\b(watch your back|regret|won't forgive|dekhna)\b", 0.8),
        (r"\b(make you pay|suffer|end you|khatam|nahi chodunga)\b", 0.75),
        (r"\b(threat|threaten|intimidate)\b", 0.7),
    ],
    "cyberbullying": [
        (r"\b(loser|idiot|stupid|moron|worthless|pathetic)\b", 0.8),
        (r"\b(chutiya|bewakoof|gandu|kamina|sala)\b", 0.85),
        (r"\b(ugly|fat|disgusting|freak|nobody)\b", 0.7),
        (r"\b(kill yourself|kys|go die)\b", 0.95),
    ],
    "hate_speech": [
        (r"\b(terrorist|jihadi|kafir|lannat|kaafir)\b", 0.85),
        (r"\b(hate|despise|filth|vermin|subhuman)\b", 0.75),
        (r"\b(communal|anti-national)\b", 0.7),
    ],
    "sexual_harassment": [
        (r"\b(sexy|nude|naked|send (me )?(your )?(photo|pic|video))\b", 0.85),
        (r"\b(want to see|show me|private|intimate)\b", 0.7),
        (r"\b(photo bhejo|raat ko baat)\b", 0.8),
    ],
    "grooming": [
        (r"\b(our secret|keep it secret|don.t tell|trust me only)\b", 0.90),
        (r"\b(mature for your age|not like other kids|special friend)\b", 0.88),
        (r"\b(meet me|come alone|where do you live|pick you up)\b", 0.85),
        (r"\b(gift|money|i.ll give you|paisa)\b", 0.70),
    ],
}


class ExplainabilityEngine:
    def highlight_tokens(
        self, text: str, scores: Dict[str, float]
    ) -> List[ToxicToken]:
        """
        Find all toxic tokens in text and return a list of ToxicToken objects.
        Only highlights tokens from categories with score > 0.2.
        """
        found: List[ToxicToken] = []
        seen_spans: set = set()

        for category, pattern_list in TOKEN_PATTERNS.items():
            if scores.get(category, 0.0) < 0.2:
                continue

            for pattern, base_score in pattern_list:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    span = (match.start(), match.end())
                    if span not in seen_spans:
                        seen_spans.add(span)
                        token_score = round(
                            min(base_score * scores.get(category, 1.0), 1.0), 3
                        )
                        found.append(
                            ToxicToken(
                                token=match.group(),
                                score=token_score,
                                category=category,
                            )
                        )

        # Sort by score descending
        found.sort(key=lambda x: x.score, reverse=True)
        return found[:15]  # max 15 highlights

    def build_highlighted_html(
        self, text: str, toxic_tokens: List[ToxicToken]
    ) -> str:
        """
        Build HTML with <mark> spans around toxic tokens.
        Escapes HTML entities to prevent XSS.
        """
        if not toxic_tokens:
            return html.escape(text)

        # Build replacement map: (start, end) → replacement
        replacements: List[tuple] = []
        for token_obj in toxic_tokens:
            pattern = re.escape(token_obj.token)
            for match in re.finditer(pattern, text, re.IGNORECASE):
                category_cls = f"toxic-{token_obj.category.replace('_', '-')}"
                escaped = html.escape(match.group())
                replacement = (
                    f'<mark class="toxic-highlight {category_cls}" '
                    f'data-score="{token_obj.score}" '
                    f'data-category="{token_obj.category}" '
                    f'title="{token_obj.category} ({token_obj.score*100:.0f}%)">'
                    f"{escaped}</mark>"
                )
                replacements.append((match.start(), match.end(), replacement))

        if not replacements:
            return html.escape(text)

        # Apply replacements from right to left to preserve positions
        replacements.sort(key=lambda x: x[0], reverse=True)
        result = list(text)
        used_ranges: List[tuple] = []

        for start, end, repl in replacements:
            # Check for overlap
            overlap = any(s < end and start < e for s, e in used_ranges)
            if not overlap:
                result[start:end] = list(repl)
                used_ranges.append((start, end))

        return "".join(result)
