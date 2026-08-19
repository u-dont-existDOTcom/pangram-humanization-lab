from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlsplit

_HISTORY_API_RE = re.compile(
    r"^/api/history/(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/?$"
)
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


@dataclass(frozen=True)
class ExactHistoryRecord:
    uuid: str
    payload: dict[str, Any]
    field_path: tuple[str, ...]
    input_sha256: str
    word_count: int

    @property
    def report_url(self) -> str:
        return f"https://www.pangram.com/history/{self.uuid}"

    def public_proof(self) -> dict[str, object]:
        return {
            "api_path": "/api/history/<uuid>/",
            "exact_text_field_path": list(self.field_path),
            "exact_text_sha256": self.input_sha256,
            "exact_word_count": self.word_count,
            "record_model_id": self.payload.get("model_id"),
            "record_prediction": self.payload.get("prediction"),
            "record_prediction_prob": self.payload.get("prediction_prob"),
        }


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def history_api_uuid(raw_url: str) -> str | None:
    try:
        parsed = urlsplit(str(raw_url))
    except Exception:
        return None
    if parsed.scheme != "https" or parsed.netloc.casefold() != "web.pangram.com":
        return None
    match = _HISTORY_API_RE.fullmatch(parsed.path)
    return match.group("uuid").lower() if match else None


def _iter_strings(
    value: Any,
    *,
    ancestry: tuple[str, ...] = (),
    depth: int = 0,
) -> Iterable[tuple[tuple[str, ...], str]]:
    if depth > 10:
        return
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _iter_strings(
                child,
                ancestry=(*ancestry, str(key)),
                depth=depth + 1,
            )
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _iter_strings(
                child,
                ancestry=(*ancestry, f"[{index}]"),
                depth=depth + 1,
            )
        return
    if not isinstance(value, str):
        return

    yield ancestry, value

    # Pangram has historically used response_payload fields that may themselves
    # be JSON-encoded strings. Parse only bounded JSON-looking strings in memory.
    stripped = value.strip()
    if len(stripped) > 5_000_000 or not stripped.startswith(("{", "[")):
        return
    try:
        nested = json.loads(stripped)
    except (json.JSONDecodeError, TypeError, ValueError):
        return
    yield from _iter_strings(
        nested,
        ancestry=(*ancestry, "<decoded-json>"),
        depth=depth + 1,
    )


def exact_text_proof(payload: Any, exact_text: str) -> dict[str, object] | None:
    target_sha = _sha256(exact_text)
    for field_path, candidate in _iter_strings(payload):
        if candidate != exact_text:
            continue
        return {
            "field_path": field_path,
            "input_sha256": target_sha,
            "word_count": len(exact_text.split()),
        }
    return None


def match_exact_history_record(
    response_url: str,
    payload: Any,
    exact_text: str,
) -> ExactHistoryRecord | None:
    uuid = history_api_uuid(response_url)
    if uuid is None or not isinstance(payload, dict):
        return None
    proof = exact_text_proof(payload, exact_text)
    if proof is None:
        return None
    payload_uuid = str(payload.get("uuid", "")).strip().lower()
    if payload_uuid and _UUID_RE.fullmatch(payload_uuid) and payload_uuid != uuid:
        return None
    return ExactHistoryRecord(
        uuid=uuid,
        payload=payload,
        field_path=tuple(str(value) for value in proof["field_path"]),
        input_sha256=str(proof["input_sha256"]),
        word_count=int(proof["word_count"]),
    )


def _percent_from_body(body: str, kind: str) -> float | None:
    normalized = " ".join(str(body).split())
    if kind == "ai":
        patterns = (
            r"\bAI\s+(?P<p>\d+(?:\.\d+)?)\s*%\b",
            r"\b(?P<p>\d+(?:\.\d+)?)\s*%\s*AI(?:\s+Generated)?\b",
        )
    else:
        patterns = (
            r"\bHuman\s+(?P<p>\d+(?:\.\d+)?)\s*%\b",
            r"\b(?P<p>\d+(?:\.\d+)?)\s*%\s*Human(?:\s+Written)?\b",
        )
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return float(match.group("p")) / 100.0
    return None


def parse_history_record_result(
    record: ExactHistoryRecord,
    rendered_body: str,
) -> dict[str, object]:
    ai = _percent_from_body(rendered_body, "ai")
    human = _percent_from_body(rendered_body, "human")

    # The live diagnostic proves that prediction/prediction_prob fields exist,
    # but not whether prediction_prob is confidence in the label, AI probability,
    # or another quantity. Do not infer score semantics from those fields.
    if ai is None or human is None or abs((ai + human) - 1.0) > 0.02:
        raise RuntimeError(
            "exact Pangram history record was identified, but its rendered Human/AI summary "
            "could not be parsed without guessing prediction_prob semantics"
        )

    return {
        "report_layout": "history_api_bound_overview_v1",
        "summary_source": "rendered_history_report",
        "summary": {
            "fraction_ai": round(float(ai), 10),
            "fraction_moderately_ai_assisted": 0.0,
            "fraction_lightly_ai_assisted": 0.0,
            "fraction_human": round(float(human), 10),
        },
        # The current long-document report paginates highlights and no longer
        # exposes the old per-segment word-count headers. Exact document identity
        # comes from the stored API record, not from inventing segment counts.
        "segments": [],
        "history_record_identity": record.public_proof(),
    }
