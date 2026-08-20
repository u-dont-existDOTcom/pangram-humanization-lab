from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from pangram_lab.history_api_record import ExactHistoryRecord


_TEXT_KEYS = (
    "text",
    "content",
    "segment",
    "span",
    "sentence",
    "window_text",
    "chunk",
)
_OFFSET_PAIRS = (
    ("start", "end"),
    ("start_char", "end_char"),
    ("char_start", "char_end"),
    ("start_index", "end_index"),
    ("start_idx", "end_idx"),
)
_METADATA_KEY_RE = re.compile(
    r"(?:label|prediction|class|confidence|prob|score|fraction|human|ai|stage|version|page|index|rank|type|word|token|length)",
    re.IGNORECASE,
)
_LOCALIZATION_KEY_RE = re.compile(
    r"(?:window|segment|highlight|span|sentence|chunk|start|end|offset|prediction|class|confidence|prob|score|fraction)",
    re.IGNORECASE,
)
_COLLECTION_PATH_RE = re.compile(r"(?:window|segment|highlight|span|sentence|chunk)", re.IGNORECASE)


@dataclass(frozen=True)
class BoundSpan:
    start: int
    end: int
    text_key: str
    text: str
    binding_mode: str


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _decoded_mapping(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if len(stripped) > 5_000_000 or not stripped.startswith("{"):
        return None
    try:
        decoded = json.loads(stripped)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return decoded if isinstance(decoded, dict) else None


def _candidate_roots(record: ExactHistoryRecord) -> list[tuple[tuple[str, ...], dict[str, Any]]]:
    roots: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    for top_name in ("response", "response_payload"):
        top = _decoded_mapping(record.payload.get(top_name))
        if top is None:
            continue
        for child_name in ("overall", "in_page"):
            child = _decoded_mapping(top.get(child_name))
            if child is not None:
                roots.append(((top_name, child_name), child))
    return roots


def _walk(value: Any, path: tuple[str, ...] = (), depth: int = 0) -> Iterable[tuple[tuple[str, ...], Mapping[str, Any]]]:
    if depth > 12:
        return
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from _walk(child, (*path, str(key)), depth + 1)
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _walk(child, (*path, f"[{index}]"), depth + 1)


def _safe_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _has_offset_fields(mapping: Mapping[str, Any]) -> bool:
    return any(start_key in mapping and end_key in mapping for start_key, end_key in _OFFSET_PAIRS)


def _is_span_candidate(path: tuple[str, ...], mapping: Mapping[str, Any]) -> bool:
    return _has_offset_fields(mapping) or any(_COLLECTION_PATH_RE.search(part) for part in path)


def _selected_text(mapping: Mapping[str, Any], exact_text: str) -> tuple[str, str] | None:
    for key in _TEXT_KEYS:
        value = mapping.get(key)
        if isinstance(value, str) and value and value != exact_text:
            return key, value
    return None


def _linebreak_removed_starts(exact_text: str) -> list[int]:
    """Map each index in Pangram's observed linebreak-stripped representation to raw text.

    Live long-document History evidence on 2026-08-20 showed `start_index` drift
    equal to the cumulative CR/LF characters in the exact submitted boundary.
    This mapping is never trusted by itself: callers must also prove the stored
    window preview at the resulting raw start and, when supplied, the window word
    count across the complete raw slice.
    """
    return [index for index, char in enumerate(exact_text) if char not in "\r\n"]


def _raw_boundary_from_linebreak_removed(starts: list[int], exact_text: str, index: int) -> int | None:
    if index < 0 or index > len(starts):
        return None
    if index == len(starts):
        return len(exact_text)
    return starts[index]


def _bind_indexed_window(mapping: Mapping[str, Any], exact_text: str) -> BoundSpan | None:
    """Bind a Pangram window's complete raw span through its validated indices.

    Pangram's current long-document `overall.windows[].text` may be a short
    preview even when start/end and word_count describe a much larger window.
    We therefore bind the complete window through start/end only when the live
    transport normalization is independently proved by the preview and word
    count. No approximate coordinate conversion is accepted.
    """
    selected = _selected_text(mapping, exact_text)
    start = _safe_int(mapping.get("start_index"))
    end = _safe_int(mapping.get("end_index"))
    if selected is None or start is None or end is None or start < 0 or end <= start:
        return None

    text_key, preview = selected
    starts = _linebreak_removed_starts(exact_text)
    raw_start = _raw_boundary_from_linebreak_removed(starts, exact_text, start)
    raw_end = _raw_boundary_from_linebreak_removed(starts, exact_text, end)
    if raw_start is None or raw_end is None or raw_end <= raw_start:
        return None

    raw_window = exact_text[raw_start:raw_end]
    if not raw_window.startswith(preview):
        return None

    expected_words = _safe_int(mapping.get("word_count"))
    if expected_words is not None and len(raw_window.split()) != expected_words:
        return None

    return BoundSpan(
        start=raw_start,
        end=raw_end,
        text_key=text_key,
        text=raw_window,
        binding_mode="pangram_linebreak_removed_indices+preview+word_count",
    )


def _unique_substring_span(exact_text: str, candidate: str) -> tuple[int, int] | None:
    if not candidate or candidate == exact_text:
        return None
    first = exact_text.find(candidate)
    if first < 0:
        return None
    if exact_text.find(candidate, first + 1) >= 0:
        return None
    return first, first + len(candidate)


def _bound_span(mapping: Mapping[str, Any], exact_text: str) -> BoundSpan | None:
    # Current long-document windows get the stronger complete-window binding
    # first. This handles short stored previews without pretending the preview is
    # the whole detector window.
    indexed = _bind_indexed_window(mapping, exact_text)
    if indexed is not None:
        return indexed

    selected = _selected_text(mapping, exact_text)
    if selected is None:
        return None
    selected_key, selected_text = selected

    # For other layouts, prefer explicit raw character offsets only when the
    # associated text proves exactly what those offsets mean.
    for start_key, end_key in _OFFSET_PAIRS:
        start = _safe_int(mapping.get(start_key))
        end = _safe_int(mapping.get(end_key))
        if start is None or end is None or start < 0 or end <= start or end > len(exact_text):
            continue
        if exact_text[start:end] == selected_text:
            return BoundSpan(
                start=start,
                end=end,
                text_key=selected_key,
                text=selected_text,
                binding_mode=f"explicit_raw_offsets:{start_key}/{end_key}",
            )

    unique = _unique_substring_span(exact_text, selected_text)
    if unique is None:
        return None
    return BoundSpan(
        start=unique[0],
        end=unique[1],
        text_key=selected_key,
        text=selected_text,
        binding_mode="unique_exact_substring",
    )


def _word_bounds(exact_text: str, start: int, end: int) -> tuple[int, int]:
    words = list(re.finditer(r"\S+", exact_text))
    word_start = sum(1 for match in words if match.end() <= start)
    word_end = sum(1 for match in words if match.start() < end)
    return word_start, word_end


def _scalar_metadata(mapping: Mapping[str, Any]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in mapping.items():
        if key in _TEXT_KEYS or not _METADATA_KEY_RE.search(str(key)):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            result[str(key)] = value
    return result


def _shape(mapping: Mapping[str, Any], path: tuple[str, ...], reason: str) -> dict[str, object]:
    text_lengths = {
        key: len(value)
        for key, value in mapping.items()
        if isinstance(value, str) and key in _TEXT_KEYS
    }
    return {
        "field_path": list(path),
        "keys": sorted(str(key) for key in mapping.keys())[:80],
        "text_field_lengths": text_lengths,
        "scalar_metadata": _scalar_metadata(mapping),
        "reason": reason,
    }


def localize_history_record(
    record: ExactHistoryRecord,
    exact_text: str,
    *,
    max_unresolved_shapes: int = 80,
) -> dict[str, object]:
    """Bind Pangram stored-result windows to exact authorized-text offsets.

    This is localization evidence only. It does not treat page/window results as
    whole-document score authority. Raw span text is used in memory for exact
    binding but is not returned or persisted.
    """
    if record.input_sha256 != _sha256(exact_text) or record.word_count != len(exact_text.split()):
        raise ValueError("history record is not bound to the supplied exact authorized text")
    if max_unresolved_shapes < 1:
        raise ValueError("max_unresolved_shapes must be positive")

    roots = _candidate_roots(record)
    dedup: dict[tuple[int, int, str], dict[str, object]] = {}
    unresolved: list[dict[str, object]] = []
    scanned_objects = 0

    for root_path, root in roots:
        for relative_path, mapping in _walk(root):
            scanned_objects += 1
            full_path = (*root_path, *relative_path)
            if not _is_span_candidate(relative_path, mapping):
                continue
            span = _bound_span(mapping, exact_text)
            if span is None:
                if (
                    len(unresolved) < max_unresolved_shapes
                    and any(_LOCALIZATION_KEY_RE.search(str(key)) for key in mapping.keys())
                ):
                    unresolved.append(_shape(mapping, full_path, "no_exact_transport_binding"))
                continue

            word_start, word_end = _word_bounds(exact_text, span.start, span.end)
            digest = _sha256(span.text)
            identity = (span.start, span.end, digest)
            evidence = {
                "field_path": list(full_path),
                "root": ".".join(root_path),
                "text_field": span.text_key,
                "binding_mode": span.binding_mode,
                "scalar_metadata": _scalar_metadata(mapping),
            }
            existing = dedup.get(identity)
            if existing is None:
                dedup[identity] = {
                    "char_start_0": span.start,
                    "char_end_0_exclusive": span.end,
                    "word_start_0": word_start,
                    "word_end_0_exclusive": word_end,
                    "word_count": max(0, word_end - word_start),
                    "span_sha256": digest,
                    "evidence": [evidence],
                }
            else:
                existing_evidence = existing.setdefault("evidence", [])
                if isinstance(existing_evidence, list):
                    existing_evidence.append(evidence)

    spans = sorted(
        dedup.values(),
        key=lambda item: (int(item["char_start_0"]), int(item["char_end_0_exclusive"])),
    )
    return {
        "schema_version": 2,
        "status": "localized" if spans else "no_bound_spans",
        "purpose": "stored_history_localization_only_not_document_score_authority",
        "authorized_text_sha256": record.input_sha256,
        "authorized_word_count": record.word_count,
        "history_record_identity": record.public_proof(),
        "source_roots_scanned": [".".join(path) for path, _ in roots],
        "objects_scanned": scanned_objects,
        "localized_span_count": len(spans),
        "spans": spans,
        "unresolved_candidate_shapes": unresolved,
        "transport_index_note": (
            "Current Pangram long-document start_index/end_index values are accepted only when a linebreak-removed "
            "index map reproduces the stored preview at the exact raw start and the complete raw slice reproduces "
            "the stored window word_count."
        ),
        "privacy_note": (
            "No submitted text, localized span text, UUID, private report URL, cookies, browser storage, "
            "headers, or credentials are persisted. Offsets are 0-based and end-exclusive."
        ),
    }
