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
    stored_text_sha256: str
    stored_word_count: int
    match_mode: str

    @property
    def report_url(self) -> str:
        return f"https://www.pangram.com/history/{self.uuid}"

    def public_proof(self) -> dict[str, object]:
        return {
            "api_path": "/api/history/<uuid>/",
            "exact_text_field_path": list(self.field_path),
            "authorized_text_sha256": self.input_sha256,
            "authorized_word_count": self.word_count,
            "stored_text_sha256": self.stored_text_sha256,
            "stored_word_count": self.stored_word_count,
            "transport_match_mode": self.match_mode,
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


def _line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _match_mode(candidate: str, exact_text: str) -> str | None:
    if candidate == exact_text:
        return "exact_utf8"

    candidate_lf = _line_endings(candidate)
    exact_lf = _line_endings(exact_text)
    if candidate_lf == exact_lf:
        return "line_endings_normalized"

    # Terminal newline normalization is safe for the reader-visible article
    # boundary and common in textarea/server serialization. Do not remove
    # interior whitespace or spaces from line ends.
    if candidate_lf.rstrip("\n") == exact_lf.rstrip("\n"):
        return "terminal_newlines_normalized"

    # A browser/server may trim the outer boundary. This mode remains bounded:
    # the complete interior string must be byte-identical after line-ending
    # normalization, and callers additionally require identical word count.
    if candidate_lf.strip() == exact_lf.strip():
        return "outer_whitespace_normalized"

    return None


def exact_text_proof(payload: Any, exact_text: str) -> dict[str, object] | None:
    target_sha = _sha256(exact_text)
    target_words = len(exact_text.split())
    for field_path, candidate in _iter_strings(payload):
        mode = _match_mode(candidate, exact_text)
        if mode is None:
            continue
        stored_words = len(candidate.split())
        if stored_words != target_words:
            continue
        return {
            "field_path": field_path,
            "input_sha256": target_sha,
            "word_count": target_words,
            "stored_text_sha256": _sha256(candidate),
            "stored_word_count": stored_words,
            "match_mode": mode,
        }
    return None


def history_record_comparison_summary(
    payload: Any,
    exact_text: str,
    *,
    limit: int = 16,
) -> dict[str, object]:
    """Return content-free structural comparison data for recovery debugging.

    No candidate text is returned. Whitespace-collapsed equality is diagnostic
    only and is never accepted by ``match_exact_history_record``.
    """
    if limit < 1:
        raise ValueError("limit must be positive")

    target_words = len(exact_text.split())
    target_chars = len(exact_text)
    target_collapsed = " ".join(exact_text.split())
    rows: list[dict[str, object]] = []
    for field_path, candidate in _iter_strings(payload):
        if len(candidate) < 32:
            continue
        candidate_words = len(candidate.split())
        candidate_chars = len(candidate)
        mode = _match_mode(candidate, exact_text)
        collapsed_equal = " ".join(candidate.split()) == target_collapsed
        contains_exact = bool(exact_text) and exact_text in candidate
        contained_by_exact = bool(candidate) and candidate in exact_text

        # Keep only plausibly document-sized strings or actual/near matches.
        if (
            mode is None
            and not collapsed_equal
            and not contains_exact
            and not contained_by_exact
            and abs(candidate_words - target_words) > max(8, target_words // 20)
            and abs(candidate_chars - target_chars) > max(64, target_chars // 20)
        ):
            continue

        rows.append(
            {
                "field_path": [str(value) for value in field_path],
                "character_count": candidate_chars,
                "word_count": candidate_words,
                "character_delta": candidate_chars - target_chars,
                "word_delta": candidate_words - target_words,
                "accepted_match_mode": mode,
                "whitespace_collapsed_equal_diagnostic_only": collapsed_equal,
                "candidate_contains_exact": contains_exact,
                "candidate_is_substring_of_exact": contained_by_exact,
            }
        )
        if len(rows) >= limit:
            break

    return {
        "authorized_character_count": target_chars,
        "authorized_word_count": target_words,
        "candidate_fields": rows,
        "privacy_note": "No Pangram history-record text or private result URL is included.",
    }


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
        stored_text_sha256=str(proof["stored_text_sha256"]),
        stored_word_count=int(proof["stored_word_count"]),
        match_mode=str(proof["match_mode"]),
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
