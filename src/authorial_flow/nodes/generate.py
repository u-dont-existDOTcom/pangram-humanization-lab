from __future__ import annotations

import re
from ..authority import AuthorityUnit


def _split_sentence_boundaries(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z“\"'])", text.strip())
    return [p.strip() for p in parts if p.strip()]


def candidate_semantic_spans(candidate: str) -> list[str]:
    """Conservatively isolate visible semantic advances.

    The splitter is intentionally biased against allowing a later clause to rescue a poor entry.
    It avoids splitting ordinary compound predicates such as "happen and matter".
    """
    text = " ".join(candidate.strip().split())
    if not text:
        return []
    sentence_parts = _split_sentence_boundaries(text)
    if len(sentence_parts) > 1:
        spans: list[str] = []
        for part in sentence_parts:
            spans.extend(candidate_semantic_spans(part))
        return spans

    # Strong rhetorical boundaries.
    for pattern in (
        r"\s+[—–]\s+",
        r";\s+",
        r",\s+(?=which\b)",
        r",\s+(?=and\s+(?:that|this|it|they|we|I)\b)",
    ):
        m = re.search(pattern, text, flags=re.I)
        if m:
            left = text[:m.start()].strip(" ,;—–")
            right = text[m.end():].strip(" ,;—–")
            if left and right and len(left.split()) >= 2 and len(right.split()) >= 2:
                # Restore a grammatically useful connective for interpretability without changing
                # the fact that the two advances are separately judged.
                if pattern.startswith(r",\s+(?=which"):
                    right = "which " + right.removeprefix("which ")
                return [left, right]

    # Substantive colon joins, not labels or tiny introductions.
    m = re.search(r":\s+", text)
    if m:
        left, right = text[:m.start()].strip(), text[m.end():].strip()
        if len(left.split()) >= 5 and len(right.split()) >= 5:
            return [left, right]
    return [text]


def writer_payload(
    section_job: str,
    units: list[AuthorityUnit],
    accepted_moves: list[str],
    pressure: dict,
    promoted_rules: list[dict] | None = None,
    owner_directives: list[dict] | None = None,
    rejected_proposals: list[dict] | None = None,
) -> dict:
    """Construct writer-visible data. Raw source and owner examples are absent by design.

    Only abstract rules that have passed the learning promotion gate may be included. Exact learning
    examples and owner-gold case bodies remain evaluator-side.
    """
    return {
        "section_job": section_job,
        "units": [u.model_dump(mode="json") for u in units],
        "accepted_moves": list(accepted_moves),
        "committed_pressure": dict(pressure),
        "promoted_rules": list(promoted_rules or []),
        "owner_directives": list(owner_directives or []),
        "rejected_proposals": list(rejected_proposals or []),
    }
