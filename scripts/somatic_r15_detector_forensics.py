#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


FAMILY = "somatic-r15-surface-calibration-building-safety-visible-20260831"
HEADINGS = {
    "Building Enough Safety to Stay Present",
    "Somatic Experiencing",
    "Trauma-Sensitive / Restorative Yoga",
    "Gentle Shaking / TRE",
}
VARIANTS = {
    "A": {
        "sha256": "11c553978685e355af6ef89b3de42380e724b4b0bb6eafef4fe6362ca26ef233",
        "measurement": f"{FAMILY}-A-visible-control",
        "input": "inputs/A-visible-control.txt",
    },
    "B": {
        "sha256": "cf67cc5760b7282caa4aaa13e06b6ec7d86c0885fb3e9b7eaaa52e1d79f72b97",
        "measurement": f"{FAMILY}-B-visible-chat-replacement",
        "input": "inputs/B-visible-chat-replacement.txt",
    },
    "C": {
        "sha256": "4717688560a3b08056da9eb77638186d0ae353861f024a4c24a65837a6d8a2a1",
        "measurement": f"{FAMILY}-C-visible-chat-replacement",
        "input": "inputs/C-visible-chat-replacement.txt",
    },
    "D": {
        "sha256": "58bd3babc5467fb4cba3792defd02624eb65366b69e9f65a6a2b7a8ba2f5db02",
        "measurement": f"{FAMILY}-D-visible-chat-replacement",
        "input": "inputs/D-visible-chat-replacement.txt",
    },
}
FIRST_PERSON = {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves"}
SECOND_PERSON = {"you", "your", "yours", "yourself", "yourselves"}
STATUS_STRING_KEYS = {
    "status",
    "stage",
    "version",
    "model",
    "expected_version",
    "prediction_short",
    "headline",
    "label",
    "confidence",
    "task_id",
    "measurement_key",
    "created_utc",
    "updated_utc",
}
FINE_SIGNAL_KEY = re.compile(
    r"sentence|token|paragraph|chunk|probab|logit|feature|attribution|span|window",
    re.IGNORECASE,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=root, text=True, encoding="utf-8"
    ).strip()


def json_pointer(parts: list[str]) -> str:
    if not parts:
        return ""
    return "/" + "/".join(part.replace("~", "~0").replace("/", "~1") for part in parts)


def schema_inventory(value: Any, parts: list[str] | None = None) -> list[dict[str, Any]]:
    parts = parts or []
    pointer = json_pointer(parts)
    if isinstance(value, dict):
        rows = [{"pointer": pointer, "type": "object", "key_count": len(value)}]
        for key in sorted(value):
            rows.extend(schema_inventory(value[key], [*parts, str(key)]))
        return rows
    if isinstance(value, list):
        rows = [{"pointer": pointer, "type": "array", "length": len(value)}]
        for index, item in enumerate(value):
            rows.extend(schema_inventory(item, [*parts, str(index)]))
        return rows
    if value is None:
        return [{"pointer": pointer, "type": "null"}]
    if isinstance(value, bool):
        return [{"pointer": pointer, "type": "boolean", "value": value}]
    if isinstance(value, (int, float)):
        return [{"pointer": pointer, "type": "number", "value": value}]
    key = parts[-1] if parts else ""
    row: dict[str, Any] = {
        "pointer": pointer,
        "type": "string",
        "unicode_characters": len(value),
        "utf8_bytes": len(value.encode("utf-8")),
        "sha256": sha256_text(value),
    }
    if key in STATUS_STRING_KEYS and len(value) <= 200:
        row["value"] = value
    return [row]


def paragraphs(text: str) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for match in re.finditer(r"\S(?:.*?\S)?(?=\n\n|\Z)", text, re.DOTALL):
        value = match.group(0)
        units.append(
            {
                "index": len(units),
                "start": match.start(),
                "end": match.end(),
                "text": value,
                "sha256": sha256_text(value),
                "characters": len(value),
                "words": len(value.split()),
                "is_heading_label": value in HEADINGS,
            }
        )
    return units


def sentence_units(text: str, paragraph_units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for paragraph in paragraph_units:
        value = paragraph["text"]
        base = paragraph["start"]
        if paragraph["is_heading_label"]:
            spans = [(0, len(value))]
        else:
            spans = []
            start = 0
            for match in re.finditer(r"[.!?](?:[”’\"']?)(?=\s|$)", value):
                end = match.end()
                spans.append((start, end))
                start = end
                while start < len(value) and value[start].isspace():
                    start += 1
            if start < len(value):
                spans.append((start, len(value)))
        for local_start, local_end in spans:
            while local_start < local_end and value[local_start].isspace():
                local_start += 1
            while local_end > local_start and value[local_end - 1].isspace():
                local_end -= 1
            if local_start == local_end:
                continue
            sentence = value[local_start:local_end]
            units.append(
                {
                    "index": len(units),
                    "paragraph_index": paragraph["index"],
                    "start": base + local_start,
                    "end": base + local_end,
                    "text": sentence,
                    "sha256": sha256_text(sentence),
                    "characters": len(sentence),
                    "words": len(sentence.split()),
                    "is_heading_label": paragraph["is_heading_label"],
                }
            )
    return units


def map_detector_span_to_input(detector_text: str, input_text: str, start: int, end: int) -> dict[str, Any]:
    matcher = SequenceMatcher(None, detector_text, input_text, autojunk=False)
    matched: list[tuple[int, int]] = []
    for a_start, b_start, size in matcher.get_matching_blocks():
        overlap_start = max(start, a_start)
        overlap_end = min(end, a_start + size)
        if overlap_start < overlap_end:
            matched.append((b_start + overlap_start - a_start, b_start + overlap_end - a_start))
    if not matched:
        return {
            "mapping_status": "NO_EQUAL_CHARACTER_MAPPING",
            "input_start": None,
            "input_end": None,
            "matched_characters": 0,
        }
    return {
        "mapping_status": "SEQUENCE_MATCHER_EQUAL_BLOCKS",
        "input_start": min(item[0] for item in matched),
        "input_end": max(item[1] for item in matched),
        "matched_characters": sum(item[1] - item[0] for item in matched),
        "detector_span_characters": end - start,
        "unmapped_detector_characters": end - start - sum(item[1] - item[0] for item in matched),
    }


def overlap_rows(span_start: int, span_end: int, units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for unit in units:
        overlap = max(0, min(span_end, unit["end"]) - max(span_start, unit["start"]))
        if not overlap:
            continue
        rows.append(
            {
                "index": unit["index"],
                "start": unit["start"],
                "end": unit["end"],
                "sha256": unit["sha256"],
                "overlap_characters": overlap,
                "overlap_percent": round(100 * overlap / max(1, unit["end"] - unit["start"]), 9),
                "is_heading_label": unit["is_heading_label"],
            }
        )
    return rows


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[’'][A-Za-zÀ-ÖØ-öø-ÿ]+)?", text.lower())


def structure_metrics(text: str, para: list[dict[str, Any]], sent: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = words(text)
    sentence_initials: dict[str, list[dict[str, Any]]] = {}
    for size in range(1, 5):
        counter: Counter[tuple[str, ...]] = Counter()
        for unit in sent:
            if unit["is_heading_label"]:
                continue
            candidate = tuple(words(unit["text"])[:size])
            if len(candidate) == size:
                counter[candidate] += 1
        sentence_initials[str(size)] = [
            {"tokens": list(key), "count": count}
            for key, count in sorted(counter.items())
            if count > 1
        ]
    repeated_ngrams: dict[str, list[dict[str, Any]]] = {}
    for size in range(3, 9):
        positions: dict[tuple[str, ...], list[int]] = {}
        for index in range(0, len(tokens) - size + 1):
            key = tuple(tokens[index : index + size])
            positions.setdefault(key, []).append(index)
        repeated_ngrams[str(size)] = [
            {"tokens": list(key), "count": len(indices), "word_offsets": indices}
            for key, indices in sorted(positions.items())
            if len(indices) > 1
        ]
    return {
        "unicode_characters": len(text),
        "utf8_bytes": len(text.encode("utf-8")),
        "whitespace_words": len(text.split()),
        "tokenized_words": len(tokens),
        "paragraph_count": len(para),
        "paragraph_character_lengths": [item["characters"] for item in para],
        "paragraph_word_lengths": [item["words"] for item in para],
        "sentence_count_including_heading_labels": len(sent),
        "sentence_count_excluding_heading_labels": sum(not item["is_heading_label"] for item in sent),
        "sentence_character_lengths": [item["characters"] for item in sent],
        "sentence_word_lengths": [item["words"] for item in sent],
        "punctuation_counts": {
            "question_mark": text.count("?"),
            "left_parenthesis": text.count("("),
            "right_parenthesis": text.count(")"),
            "colon": text.count(":"),
            "semicolon": text.count(";"),
            "dash_total": sum(text.count(mark) for mark in ("-", "–", "—")),
            "hyphen": text.count("-"),
            "en_dash": text.count("–"),
            "em_dash": text.count("—"),
            "ellipsis_character": text.count("…"),
            "three_period_ellipsis": text.count("..."),
            "curly_double_quotation_marks": text.count("“") + text.count("”"),
            "straight_double_quotation_marks": text.count('"'),
        },
        "contractions": {
            "count": len(re.findall(r"\b[A-Za-z]+[’'][A-Za-z]+\b", text)),
            "forms": dict(sorted(Counter(re.findall(r"\b[A-Za-z]+[’'][A-Za-z]+\b", text.lower())).items())),
        },
        "pronouns": {
            "first_person": sum(token in FIRST_PERSON for token in tokens),
            "second_person": sum(token in SECOND_PERSON for token in tokens),
        },
        "line_counts": {
            "total": len(text.splitlines()),
            "nonempty": sum(bool(line.strip()) for line in text.splitlines()),
            "blank": sum(not line.strip() for line in text.splitlines()),
            "heading_label": sum(line in HEADINGS for line in text.splitlines()),
            "markdown_list": sum(bool(re.match(r"^\s*[-*+]\s+", line)) for line in text.splitlines()),
        },
        "repeated_sentence_initial_token_sequences": sentence_initials,
        "repeated_contiguous_word_ngrams": repeated_ngrams,
    }


def diff_map(source: str, target: str) -> list[dict[str, Any]]:
    rows = []
    for tag, a_start, a_end, b_start, b_end in SequenceMatcher(
        None, source, target, autojunk=False
    ).get_opcodes():
        a_text = source[a_start:a_end]
        b_text = target[b_start:b_end]
        rows.append(
            {
                "operation": tag.upper(),
                "A_start": a_start,
                "A_end": a_end,
                "target_start": b_start,
                "target_end": b_end,
                "A_text": a_text,
                "target_text": b_text,
                "A_sha256": sha256_text(a_text),
                "target_sha256": sha256_text(b_text),
            }
        )
    return rows


def historical_cache_versions(root: Path, cache_path: Path) -> list[dict[str, Any]]:
    relative = cache_path.relative_to(root).as_posix()
    commits = git(root, "log", "--all", "--format=%H", "--", relative).splitlines()
    versions = []
    seen = set()
    for commit in commits:
        try:
            raw = subprocess.check_output(
                ["git", "show", f"{commit}:{relative}"], cwd=root
            )
            value = json.loads(raw.decode("utf-8"))
        except (subprocess.CalledProcessError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        digest = sha256_bytes(raw)
        if digest in seen:
            continue
        seen.add(digest)
        inventory = schema_inventory(value)
        versions.append(
            {
                "commit": commit,
                "sha256": digest,
                "status": value.get("status"),
                "top_level_keys": sorted(value),
                "schema_pointer_count": len(inventory),
                "has_result": isinstance(value.get("result"), dict),
            }
        )
    return versions


def response_nodes(
    value: Any,
    parts: list[str] | None = None,
    inherited_input_sha256: str | None = None,
) -> list[dict[str, Any]]:
    """Inventory embedded detector-response objects without assuming one packet shape."""
    parts = parts or []
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        bound_input_sha256 = inherited_input_sha256
        if isinstance(value.get("input_sha256"), str):
            bound_input_sha256 = value["input_sha256"]
        elif isinstance(value.get("input"), dict) and isinstance(value["input"].get("sha256"), str):
            bound_input_sha256 = value["input"]["sha256"]
        elif not parts and isinstance(value.get("text_sha256"), str):
            bound_input_sha256 = value["text_sha256"]
        keys = set(value)
        if "windows" in keys and ({"fraction_ai", "headline", "prediction"} & keys):
            node_inventory = schema_inventory(value)
            rows.append(
                {
                    "pointer": json_pointer(parts),
                    "bound_input_sha256": bound_input_sha256,
                    "schema_pointer_count": len(node_inventory),
                    "field_pointers": sorted(row["pointer"] for row in node_inventory),
                    "keys": sorted(value),
                    "window_count": len(value.get("windows") or []),
                }
            )
        for key in sorted(value):
            rows.extend(
                response_nodes(value[key], [*parts, str(key)], bound_input_sha256)
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            rows.extend(
                response_nodes(item, [*parts, str(index)], inherited_input_sha256)
            )
    return rows


def matching_persisted_json(
    root: Path,
    output: Path,
    expected_sha: str,
    task_id: str,
    measurement_key: str,
) -> list[dict[str, Any]]:
    """Find exact-task JSON evidence under the repository's durable state surfaces."""
    rows: list[dict[str, Any]] = []
    needles = (expected_sha, task_id, measurement_key)
    for base_name in ("cache", "state", "tasks", "reservations"):
        base = root / base_name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.json")):
            if output == path or output in path.parents:
                continue
            raw = path.read_bytes()
            decoded = raw.decode("utf-8")
            matches = [needle for needle in needles if needle and needle in decoded]
            if not matches:
                continue
            try:
                value = json.loads(decoded)
            except json.JSONDecodeError:
                continue
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256_bytes(raw),
                    "bytes": len(raw),
                    "matched_identities": matches,
                    "schema_pointer_count": len(schema_inventory(value)),
                    "embedded_detector_responses": response_nodes(value),
                }
            )
    return rows


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    experiment = root / "state" / "experiments" / FAMILY
    output = experiment / "forensics"
    output.mkdir(parents=True, exist_ok=True)

    records: dict[str, dict[str, Any]] = {}
    schema_output: dict[str, Any] = {
        "format": "somatic-r15-detector-raw-schema-v1",
        "family": FAMILY,
        "variants": {},
    }
    span_output: dict[str, Any] = {
        "format": "somatic-r15-detector-span-offset-map-v1",
        "family": FAMILY,
        "sentence_rule": "Within each blank-line paragraph, end a sentence at . ! or ?, including one immediately following closing quotation mark, when followed by whitespace or paragraph end; headings are separate label units.",
        "variants": {},
    }
    metrics_output: dict[str, Any] = {
        "format": "somatic-r15-text-structure-metrics-v1",
        "family": FAMILY,
        "variants": {},
    }

    any_finer_signal = False
    any_fuller_raw = False
    for name, expected in VARIANTS.items():
        input_path = experiment / expected["input"]
        input_bytes = input_path.read_bytes()
        input_text = input_bytes.decode("utf-8")
        observed = sha256_bytes(input_bytes)
        if observed != expected["sha256"]:
            raise SystemExit(f"{name}: input hash mismatch: {observed}")
        cache_path = (
            root
            / "cache"
            / "pangram-4"
            / "4.0"
            / expected["sha256"]
            / f"{expected['measurement']}.json"
        )
        cache_raw = cache_path.read_bytes()
        cache = json.loads(cache_raw.decode("utf-8"))
        if sha256_text(cache.get("text", "")) != expected["sha256"]:
            raise SystemExit(f"{name}: cache stored text identity mismatch")
        result = cache.get("result") or {}
        detector_text = result.get("text", "")
        windows = result.get("windows") or []
        para = paragraphs(input_text)
        sent = sentence_units(input_text, para)
        inventory = schema_inventory(cache)
        historical = historical_cache_versions(root, cache_path)
        persisted = matching_persisted_json(
            root,
            output,
            expected["sha256"],
            str(cache.get("task_id") or ""),
            expected["measurement"],
        )
        normalized_response_pointer_count = len(schema_inventory(result))
        normalized_response_pointers = {
            row["pointer"] for row in schema_inventory(result)
        }
        fuller = [
            {
                "path": item["path"],
                "pointer": node["pointer"],
                "schema_pointer_count": node["schema_pointer_count"],
            }
            for item in persisted
            for node in item["embedded_detector_responses"]
            if node["bound_input_sha256"] == expected["sha256"]
            and set(node["field_pointers"]) > normalized_response_pointers
        ]
        any_fuller_raw = any_fuller_raw or bool(fuller)

        fine_candidates = [
            row
            for row in inventory
            if FINE_SIGNAL_KEY.search(row["pointer"])
            and row["pointer"] not in {"/result/windows", "/result/windows/0"}
        ]
        finer_signal = False
        if len(windows) > 1:
            finer_signal = True
        for row in fine_candidates:
            pointer = row["pointer"]
            if "/result/windows/0/" in pointer:
                continue
            if pointer.startswith("/result/windows/"):
                continue
            finer_signal = True
        any_finer_signal = any_finer_signal or finer_signal

        window_maps = []
        for index, window in enumerate(windows):
            start = int(window.get("start_index", 0))
            end = int(window.get("end_index", 0))
            window_text = window.get("text", "")
            mapping = map_detector_span_to_input(detector_text, input_text, start, end)
            input_start = mapping.get("input_start")
            input_end = mapping.get("input_end")
            overlaps = {"paragraphs": [], "sentences": []}
            if isinstance(input_start, int) and isinstance(input_end, int):
                overlaps = {
                    "paragraphs": overlap_rows(input_start, input_end, para),
                    "sentences": overlap_rows(input_start, input_end, sent),
                }
            window_maps.append(
                {
                    "window_index": index,
                    "detector_start": start,
                    "detector_end": end,
                    "detector_text_sha256": sha256_text(window_text),
                    "detector_text_characters": len(window_text),
                    "matches_result_text_slice": window_text == detector_text[start:end],
                    "input_mapping": mapping,
                    "overlap": overlaps,
                }
            )

        schema_output["variants"][name] = {
            "input_sha256": observed,
            "cache_path": cache_path.relative_to(root).as_posix(),
            "cache_sha256": sha256_bytes(cache_raw),
            "task_id": cache.get("task_id"),
            "inventory": inventory,
            "historical_cache_versions": historical,
            "matching_persisted_json": persisted,
            "normalized_response_schema_pointer_count": normalized_response_pointer_count,
            "fuller_embedded_detector_responses": fuller,
            "more_complete_raw_than_current_cache": bool(fuller),
            "finer_grained_signal_present": finer_signal,
            "finer_signal_schema_candidates": fine_candidates,
            "finer_signal_disposition": (
                "FINER_GRAINED_DETECTOR_SIGNAL_PRESENT"
                if finer_signal
                else "NO_FINER_GRAINED_DETECTOR_SIGNAL_PRESENT"
            ),
        }
        span_output["variants"][name] = {
            "input_sha256": observed,
            "input_characters": len(input_text),
            "detector_result_text_sha256": sha256_text(detector_text),
            "detector_result_text_characters": len(detector_text),
            "paragraphs": para,
            "sentences": sent,
            "windows": window_maps,
        }
        metrics_output["variants"][name] = structure_metrics(input_text, para, sent)
        records[name] = {"input": input_text, "paragraphs": para, "sentences": sent}

    diff_output: dict[str, Any] = {
        "format": "somatic-r15-a-b-c-d-diff-map-v1",
        "family": FAMILY,
        "source_variant": "A",
        "comparisons": {},
    }
    source = records["A"]["input"]
    for target_name in ("B", "C", "D"):
        target = records[target_name]["input"]
        diff_output["comparisons"][f"A_to_{target_name}"] = {
            "source_sha256": sha256_text(source),
            "target_sha256": sha256_text(target),
            "character_opcodes": diff_map(source, target),
            "paragraph_count_delta": len(records[target_name]["paragraphs"]) - len(records["A"]["paragraphs"]),
            "sentence_count_delta": len(records[target_name]["sentences"]) - len(records["A"]["sentences"]),
        }

    write_json(output / "RAW-SCHEMA.json", schema_output)
    write_json(output / "SPAN-OFFSET-MAP.json", span_output)
    write_json(output / "TEXT-STRUCTURE-METRICS.json", metrics_output)
    write_json(output / "A-B-C-D-DIFF-MAP.json", diff_output)
    summary = {
        "family": FAMILY,
        "more_complete_raw_response_existed": any_fuller_raw,
        "finer_grained_detector_signal_existed": any_finer_signal,
        "finer_signal_disposition": (
            "FINER_GRAINED_DETECTOR_SIGNAL_PRESENT"
            if any_finer_signal
            else "NO_FINER_GRAINED_DETECTOR_SIGNAL_PRESENT"
        ),
        "outputs": {
            path.name: {
                "sha256": sha256_bytes(path.read_bytes()),
                "bytes": path.stat().st_size,
            }
            for path in sorted(output.glob("*.json"))
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
