#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT = "somatic-r15-api-gui-human-window-calibration-20260831"
ARTICLE_HEAD = "bd10ea9c8fbec4c081f02461b9f28ca96a27043f"
ARTICLE_PREVIOUS_HEAD = "be021d494ffcff90507184deb3fa744a7004e0cd"
SOURCE_REL = "articles/somatic-therapies/experiments/R15-WHOLE-ARTICLE-PANGRAM-BOUNDARY-20260830.txt"
SOURCE_BLOB = "542012646469032eb836865b0e89b8fa368a1d0b"
SOURCE_SHA256 = "9a81bd04252a2ee851dd111040c600837bdf0a7bbf71c42c293e3b763c99a707"
PACKET_REL = "tasks/somatic-r15-clean-continuation-20260830/CHAT-CROSS-TRANSPORT-CALIBRATION-001.md"
PACKET_BLOB = "2de6157d85fa9fe329517c6066f124c9c7281865"
LOCALIZATION_REL = "state/recovery/somatic-r15-clean-continuation-20260830/exact-result-window-map.json"
VARIANTS = {
    "H1": {
        "start": 9284,
        "end": 10502,
        "characters": 1218,
        "sha256": "d9a1fcd6ed832117b32e07844300f5b30d9067884481b14a63740dcc5bfe5d3b",
        "window_index": 5,
        "label": "Human",
        "confidence": "High",
        "ai_likelihood": 0.14797909557819366,
        "filename": "H1-gui-human-window-5.txt",
        "measurement_key": f"{EXPERIMENT}-H1-gui-human-window-5",
    },
    "H2": {
        "start": 17379,
        "end": 18571,
        "characters": 1192,
        "sha256": "1d7bb2473eea7c4c42229726aaeb953fc5fb6f30c1cfc316f2673e90be56f3aa",
        "window_index": 7,
        "label": "Human",
        "confidence": "High",
        "ai_likelihood": 0.219383105635643,
        "filename": "H2-gui-human-window-7.txt",
        "measurement_key": f"{EXPERIMENT}-H2-gui-human-window-7",
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=root, text=True, encoding="utf-8"
    ).strip()


def matching_json_paths(root: Path, needles: list[str], output: Path) -> list[str]:
    matches: list[str] = []
    for base_name in ("cache", "state", "tasks", "reservations"):
        base = root / base_name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.json")):
            if output == path or output in path.parents:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(needle in text for needle in needles):
                matches.append(path.relative_to(root).as_posix())
    return matches


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--detector-root", type=Path, default=Path.cwd())
    parser.add_argument("--article-root", type=Path, required=True)
    args = parser.parse_args()
    detector = args.detector_root.resolve()
    article = args.article_root.resolve()
    if git(detector, "rev-parse", "HEAD") != "0588d51d15dc4087c72adc4c35fd78d6be826887":
        raise SystemExit("detector starting head mismatch")
    if git(article, "rev-parse", "HEAD") != ARTICLE_HEAD:
        raise SystemExit("article head mismatch")
    if git(article, "status", "--porcelain"):
        raise SystemExit("article worktree is not clean")
    changed = git(article, "diff", "--name-only", ARTICLE_PREVIOUS_HEAD, ARTICLE_HEAD).splitlines()
    if changed != [PACKET_REL]:
        raise SystemExit(f"unexpected article changes since prior checkpoint: {changed}")
    packet = article / PACKET_REL
    if git(article, "hash-object", PACKET_REL) != PACKET_BLOB:
        raise SystemExit("packet blob mismatch")

    source = article / SOURCE_REL
    source_raw = source.read_bytes()
    source_text = source_raw.decode("utf-8")
    if git(article, "hash-object", SOURCE_REL) != SOURCE_BLOB:
        raise SystemExit("source blob mismatch")
    if sha256(source_raw) != SOURCE_SHA256:
        raise SystemExit("source sha256 mismatch")

    localization_path = detector / LOCALIZATION_REL
    localization = json.loads(localization_path.read_text(encoding="utf-8"))
    windows = {int(item["window_index"]): item for item in localization["windows"]}
    experiment = detector / "state" / "experiments" / EXPERIMENT
    inputs = experiment / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    records: dict[str, Any] = {}
    for name, expected in VARIANTS.items():
        value = source_text[expected["start"] : expected["end"]]
        raw = value.encode("utf-8")
        if len(value) != expected["characters"]:
            raise SystemExit(f"{name}: character count mismatch")
        if sha256(raw) != expected["sha256"]:
            raise SystemExit(f"{name}: slice sha256 mismatch")
        if source_text.count(value) != 1:
            raise SystemExit(f"{name}: slice is not a unique exact source substring")
        window = windows[expected["window_index"]]
        checks = {
            "raw_start": expected["start"],
            "raw_end": expected["end"],
            "raw_span_sha256": expected["sha256"],
            "label": expected["label"],
            "confidence": expected["confidence"],
            "ai_likelihood": expected["ai_likelihood"],
        }
        for field, wanted in checks.items():
            if window.get(field) != wanted:
                raise SystemExit(f"{name}: GUI localization mismatch for {field}")
        output_path = inputs / expected["filename"]
        output_path.write_bytes(raw)
        cache_dir = detector / "cache" / "pangram-4" / "4.0" / expected["sha256"]
        cache_records = []
        if cache_dir.exists():
            for path in sorted(cache_dir.glob("*.json")):
                value_json = json.loads(path.read_text(encoding="utf-8"))
                cache_records.append(
                    {
                        "path": path.relative_to(detector).as_posix(),
                        "measurement_key": value_json.get("measurement_key"),
                        "status": value_json.get("status"),
                        "task_id": value_json.get("task_id"),
                    }
                )
        matching = matching_json_paths(
            detector,
            [expected["sha256"], expected["measurement_key"]],
            experiment,
        )
        if cache_records:
            statuses = {str(item.get("status")) for item in cache_records}
            if "submit_ambiguous" in statuses:
                classification = "EXACT_API_ACTION_AMBIGUOUS"
            elif "pending" in statuses:
                classification = "EXACT_API_TASK_PENDING"
            elif "success" in statuses:
                classification = "EXACT_API_RESULT_EXISTS"
            else:
                classification = "EXACT_API_PRIOR_NONTERMINAL_STATE"
        else:
            classification = "EXACT_API_NEVER_SUBMITTED"
        records[name] = {
            "input_path": output_path.relative_to(detector).as_posix(),
            "measurement_key": expected["measurement_key"],
            "source_offsets": {"start": expected["start"], "end": expected["end"]},
            "unicode_characters": len(value),
            "utf8_bytes": len(raw),
            "whitespace_words": len(value.split()),
            "terminal_newline": value.endswith("\n"),
            "sha256": sha256(raw),
            "exact_source_substring_count": source_text.count(value),
            "gui_prior": window,
            "cache_records": cache_records,
            "matching_durable_json_outside_experiment": matching,
            "pre_submission_classification": classification,
        }
    preflight = {
        "format": "somatic-r15-api-gui-human-window-calibration-preflight-v1",
        "directive": {
            "id": "SOMATIC-R15-CROSS-TRANSPORT-001",
            "packet_path": PACKET_REL,
            "packet_git_blob": PACKET_BLOB,
        },
        "article": {
            "branch": "task/somatic-r15-clean-continuation-20260830",
            "head": ARTICLE_HEAD,
            "source_path": SOURCE_REL,
            "source_git_blob": SOURCE_BLOB,
            "source_sha256": sha256(source_raw),
            "source_unicode_characters": len(source_text),
            "source_utf8_bytes": len(source_raw),
            "article_candidate_mutations": 0,
            "registered_master_mutations": 0,
        },
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "starting_head": "0588d51d15dc4087c72adc4c35fd78d6be826887",
            "model": "pangram-4",
            "required_version": "4.0",
            "transport": "SHORT_DOCUMENT_API",
        },
        "localization_map": {
            "path": LOCALIZATION_REL,
            "sha256": sha256(localization_path.read_bytes()),
        },
        "variants": records,
        "accounting_before_execution": {
            "new_paid_api_calls": 0,
            "detector_reservations_created": 0,
            "whole_document_calls": 0,
            "gui_actions": 0,
        },
        "preflight": "PASS",
    }
    write_json(experiment / "PREFLIGHT.json", preflight)
    print(json.dumps({"preflight": "PASS", "variants": records}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
