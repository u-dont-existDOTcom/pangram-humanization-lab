from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


RUNNER_VERSION = "pangram-gui-browserbase-v1"
MODEL_ID = "pangram-4"

_SEGMENT_LABELS = (
    "Fully AI Generated",
    "Moderately AI Assisted",
    "Lightly AI Assisted",
    "Human Written",
)
_SUMMARY_FIELDS = {
    "AI Generated": "fraction_ai",
    "Moderately AI Assisted": "fraction_moderately_ai_assisted",
    "Lightly AI Assisted": "fraction_lightly_ai_assisted",
    "Human Written": "fraction_human",
}
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_SEGMENT_HEADER_RE = re.compile(
    r"(?P<label>Fully\s+AI\s+Generated|Moderately\s+AI\s+Assisted|Lightly\s+AI\s+Assisted|Human\s+Written)"
    r"\s*(?:[|•·—–-]\s*)?"
    r"(?P<words>\d[\d,]*)\s+Words?"
    r"(?:\s*(?:[|•·—–-]\s*)?(?P<confidence>High|Medium|Low)\s+Confidence)?",
    re.IGNORECASE,
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def measurement_dir(root: Path, input_sha256: str) -> Path:
    if not _HEX64_RE.fullmatch(input_sha256):
        raise ValueError("input_sha256 must be 64 lowercase hexadecimal characters")
    return root / MODEL_ID / input_sha256


def completed_result_exists(root: Path, input_sha256: str) -> bool:
    receipt = measurement_dir(root, input_sha256) / "result.json"
    if not receipt.is_file():
        return False
    try:
        value = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(value, dict)
        and value.get("status") == "complete"
        and value.get("runner_version") == RUNNER_VERSION
    )


def build_session_payload(
    context_id: str,
    *,
    persist: bool,
    keep_alive: bool,
    timeout: int,
    user_metadata: dict[str, str],
) -> dict[str, object]:
    if not context_id.strip():
        raise ValueError("context_id is required")
    if timeout < 60 or timeout > 21600:
        raise ValueError("timeout must be between 60 and 21600 seconds")
    return {
        "browserSettings": {
            "context": {
                "id": context_id,
                "persist": bool(persist),
            }
        },
        "keepAlive": bool(keep_alive),
        "timeout": timeout,
        "userMetadata": dict(user_metadata),
    }


def _canonical_label(raw: str) -> str:
    compact = " ".join(raw.split()).lower()
    for label in _SEGMENT_LABELS:
        if compact == label.lower():
            return label
    raise ValueError(f"unknown Pangram segment label: {raw!r}")


def _summary_fraction(summary_text: str, label: str) -> float | None:
    escaped = re.escape(label)
    patterns = (
        rf"(?P<percent>\d+(?:\.\d+)?)\s*%\s*(?:of\s+the\s+document\s*)?{escaped}",
        rf"{escaped}\s*(?:[:|•·—–-]\s*)?(?P<percent>\d+(?:\.\d+)?)\s*%",
    )
    for pattern in patterns:
        match = re.search(pattern, summary_text, flags=re.IGNORECASE)
        if match:
            return float(match.group("percent")) / 100.0
    return None


def _clean_segment_text(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^[\s|•·—–-]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_report_text(body: str) -> dict[str, Any]:
    """Parse Pangram GUI report text without inventing fields the GUI did not expose."""
    marker = re.search(r"\bAnalyzed\s+Text\b", body, flags=re.IGNORECASE)
    if marker:
        summary_text = body[: marker.start()]
        segment_text = body[marker.end() :]
    else:
        summary_text = body
        segment_text = body

    summary: dict[str, float | None] = {
        "fraction_ai": None,
        "fraction_moderately_ai_assisted": None,
        "fraction_lightly_ai_assisted": None,
        "fraction_human": None,
    }
    for label, field in _SUMMARY_FIELDS.items():
        summary[field] = _summary_fraction(summary_text, label)

    matches = list(_SEGMENT_HEADER_RE.finditer(segment_text))
    segments: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(segment_text)
        segment_body = _clean_segment_text(segment_text[match.end() : end])
        confidence = match.group("confidence")
        segments.append(
            {
                "label": _canonical_label(match.group("label")),
                "word_count": int(match.group("words").replace(",", "")),
                "confidence": confidence.title() if confidence else None,
                "text": segment_body,
            }
        )

    return {"summary": summary, "segments": segments}
