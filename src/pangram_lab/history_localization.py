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
_WINDOW_INDEX_RE = re.compile(r"^\[(\d+)\]$")


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
    """Map Pangram's observed linebreak-stripped character indices to raw text."""
    return [index for index, char in enumerate(exact_text) if char not in "\r\n"]


def _linebreak_run_collapsed_terminal_trimmed_starts(exact_text: str) -> list[int]:
    """Map indices after collapsing linebreak runs and trimming the final run."""
    starts: list[int] = []
    in_linebreak_run = False
    for index, char in enumerate(exact_text):
        if char in "\r\n":
            if not in_linebreak_run:
                starts.append(index)
            in_linebreak_run = True
        else:
            starts.append(index)
            in_linebreak_run = False
    while starts and exact_text[starts[-1]] in "\r\n":
        starts.pop()
    return starts


def _raw_boundary_from_linebreak_removed(starts: list[int], exact_text: str, index: int) -> int | None:
    if index < 0 or index > len(starts):
        return None
    if index == len(starts):
        return len(exact_text)
    return starts[index]


def _validated_overall_window_bindings(
    root: Mapping[str, Any], exact_text: str
) -> dict[int, BoundSpan]:
    """Bind a complete Pangram `overall.windows` collection as one proven coordinate system.

    Current long-document History records may store only a short preview in each
    window's `text` field. The reliable proof is collection-wide: the windows
    cover the full Pangram coordinate space contiguously, and *every* stored
    preview must begin exactly at the raw position produced by the observed
    linebreak-stripped index map. This does not assume Pangram's `word_count`
    uses Python whitespace tokenization.
    """
    windows = root.get("windows")
    if not isinstance(windows, list) or not windows:
        return {}

    coordinate_maps = (
        (
            "pangram_linebreak_removed_contiguous_windows+all_previews",
            _linebreak_removed_starts(exact_text),
        ),
        (
            "pangram_linebreak_run_collapsed_terminal_trimmed_contiguous_windows+all_previews",
            _linebreak_run_collapsed_terminal_trimmed_starts(exact_text),
        ),
    )
    for binding_mode, index_map in coordinate_maps:
        coordinate_text = "".join(exact_text[raw_index] for raw_index in index_map)
        bindings: dict[int, BoundSpan] = {}
        previous_end: int | None = None
        for position, window in enumerate(windows):
            if not isinstance(window, dict):
                bindings = {}
                break
            start = _safe_int(window.get("start_index"))
            end = _safe_int(window.get("end_index"))
            selected = _selected_text(window, exact_text)
            if selected is None or start is None or end is None or start < 0 or end <= start:
                bindings = {}
                break
            if position == 0 and start != 0:
                bindings = {}
                break
            if previous_end is not None and start != previous_end:
                bindings = {}
                break

            raw_start = _raw_boundary_from_linebreak_removed(index_map, exact_text, start)
            raw_end = _raw_boundary_from_linebreak_removed(index_map, exact_text, end)
            if raw_start is None or raw_end is None or raw_end <= raw_start:
                bindings = {}
                break

            text_key, preview = selected
            if not coordinate_text.startswith(preview, start):
                bindings = {}
                break

            raw_window = exact_text[raw_start:raw_end]
            bindings[position] = BoundSpan(
                start=raw_start,
                end=raw_end,
                text_key=text_key,
                text=raw_window,
                binding_mode=binding_mode,
            )
            previous_end = end

        if bindings and len(bindings) == len(windows) and previous_end == len(index_map):
            return bindings
    return {}


def _window_index_from_path(path: tuple[str, ...]) -> int | None:
    if len(path) < 2 or path[-2] != "windows":
        return None
    match = _WINDOW_INDEX_RE.fullmatch(path[-1])
    return None if match is None else int(match.group(1))


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
    selected = _selected_text(mapping, exact_text)
    if selected is None:
        return None
    selected_key, selected_text = selected

    # For layouts that provide genuine raw offsets, accept them only when the
    # associated text proves the exact slice. Pangram long-document overall
    # windows are handled separately as a collection above.
    for start_key, end_key in _OFFSET_PAIRS:
        if (start_key, end_key) == ("start_index", "end_index"):
            continue
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
    full_overall_bindings: dict[int, dict[int, BoundSpan]] = {
        id(root): _validated_overall_window_bindings(root, exact_text)
        for root_path, root in roots
        if root_path[-1] == "overall"
    }
    dedup: dict[tuple[int, int, str], dict[str, object]] = {}
    unresolved: list[dict[str, object]] = []
    scanned_objects = 0

    for root_path, root in roots:
        overall_bindings = full_overall_bindings.get(id(root), {})
        for relative_path, mapping in _walk(root):
            scanned_objects += 1
            full_path = (*root_path, *relative_path)
            if not _is_span_candidate(relative_path, mapping):
                continue

            span: BoundSpan | None = None
            window_index = _window_index_from_path(relative_path)
            if root_path[-1] == "overall" and window_index is not None:
                span = overall_bindings.get(window_index)
            if span is None:
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
    full_window_count = sum(
        1
        for item in spans
        if any(
            str(evidence.get("binding_mode", "")).startswith("pangram_linebreak_")
            and str(evidence.get("binding_mode", "")).endswith(
                "_contiguous_windows+all_previews"
            )
            for evidence in item.get("evidence", [])
            if isinstance(evidence, dict)
        )
    )
    return {
        "schema_version": 3,
        "status": "localized" if spans else "no_bound_spans",
        "purpose": "stored_history_localization_only_not_document_score_authority",
        "authorized_text_sha256": record.input_sha256,
        "authorized_word_count": record.word_count,
        "history_record_identity": record.public_proof(),
        "source_roots_scanned": [".".join(path) for path, _ in roots],
        "objects_scanned": scanned_objects,
        "localized_span_count": len(spans),
        "validated_full_overall_window_count": full_window_count,
        "spans": spans,
        "unresolved_candidate_shapes": unresolved,
        "transport_index_note": (
            "Current long-document response.overall.windows are accepted as full windows only when the entire "
            "collection covers one observed Pangram linebreak-normalized coordinate space contiguously and every "
            "stored preview matches exactly at its mapped raw start. Supported proven transforms remove linebreaks "
            "or collapse each linebreak run and trim the terminal run. Pangram window word_count is preserved as "
            "metadata but is not assumed to use Python whitespace tokenization."
        ),
        "privacy_note": (
            "No submitted text, localized span text, UUID, private report URL, cookies, browser storage, "
            "headers, or credentials are persisted. Offsets are 0-based and end-exclusive."
        ),
    }
