#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT = "somatic-r15-eft-human-anchor-tail-factorial-20260831"
RESULT_HEAD = "623a520962cfb5fa9ea01130714e6f30f1fbcec3"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def compact_result(result: dict[str, Any], cache_path: str) -> dict[str, Any]:
    windows = []
    for index, window in enumerate(result.get("windows") or []):
        text = str(window.get("text") or "")
        windows.append(
            {
                "label": window.get("label"),
                "confidence": window.get("confidence"),
                "start_index": window.get("start_index"),
                "end_index": window.get("end_index"),
                "word_count": window.get("word_count"),
                "token_length": window.get("token_length"),
                "is_humanized": window.get("is_humanized"),
                "ai_assistance_score": window.get("ai_assistance_score"),
                "humanizer_score": window.get("humanizer_score"),
                "text_sha256": digest(text.encode("utf-8")),
                "text_unicode_characters": len(text),
                "text_utf8_bytes": len(text.encode("utf-8")),
                "exact_text_pointer": f"{cache_path}#/result/windows/{index}/text",
            }
        )
    return {
        "stage": result.get("stage"),
        "version": result.get("version"),
        "prediction": result.get("prediction"),
        "prediction_short": result.get("prediction_short"),
        "headline": result.get("headline"),
        "fraction_human": result.get("fraction_human"),
        "fraction_ai": result.get("fraction_ai"),
        "fraction_ai_assisted": result.get("fraction_ai_assisted"),
        "num_human_segments": result.get("num_human_segments"),
        "num_ai_segments": result.get("num_ai_segments"),
        "num_ai_assisted_segments": result.get("num_ai_assisted_segments"),
        "windows": windows,
    }


def vector(result: dict[str, Any]) -> dict[str, float]:
    window = (result.get("windows") or [{}])[0]
    return {
        "fraction_human": float(result["fraction_human"]),
        "fraction_ai": float(result["fraction_ai"]),
        "fraction_ai_assisted": float(result["fraction_ai_assisted"]),
        "window_0_ai_assistance_score": float(window["ai_assistance_score"]),
        "window_0_humanizer_score": float(window["humanizer_score"]),
    }


def subtract(target: dict[str, float], source: dict[str, float]) -> dict[str, float]:
    return {key: target[key] - source[key] for key in target}


def main() -> int:
    root = Path.cwd().resolve()
    if git(root, "rev-parse", "HEAD") != RESULT_HEAD:
        raise SystemExit("unexpected exact-results head")
    experiment = root / "state" / "experiments" / EXPERIMENT
    preflight_path = experiment / "PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text())
    if preflight.get("preflight") != "PASS" or preflight["direct_tail_preservation"]["overall"] != "PASS":
        raise SystemExit("preflight/preservation gate not PASS")
    variants: dict[str, Any] = {}
    vectors: dict[str, dict[str, float]] = {}
    for name in ("H0", "A", "B", "C", "D"):
        identity = preflight["variants"][name]
        input_path = root / identity["input_path"]
        raw = input_path.read_bytes()
        if digest(raw) != identity["sha256"]:
            raise SystemExit(f"{name}: input identity mismatch")
        cache_rel = (
            Path("cache")
            / "pangram-4"
            / "4.0"
            / identity["sha256"]
            / f"{identity['measurement_key']}.json"
        )
        cache_raw = (root / cache_rel).read_bytes()
        cache = json.loads(cache_raw.decode("utf-8"))
        if cache.get("text_sha256") != identity["sha256"] or cache.get("text", "").encode("utf-8") != raw:
            raise SystemExit(f"{name}: cache text mismatch")
        result = cache.get("result") or {}
        if cache.get("status") != "success" or not cache.get("task_id"):
            raise SystemExit(f"{name}: terminal cache/task missing")
        if result.get("version") != "4.0" or result.get("stage") != "STAGE_SUCCESS":
            raise SystemExit(f"{name}: detector version/stage mismatch")
        commits = git(root, "log", "--format=%H", "--", cache_rel.as_posix()).splitlines()
        if len(commits) < 2:
            raise SystemExit(f"{name}: checkpoint/result commits missing")
        compact = compact_result(result, cache_rel.as_posix())
        variants[name] = {
            "input": identity,
            "cache_state_before_call": "ABSENT",
            "task_id": cache["task_id"],
            "submitted_model": cache.get("submitted_model"),
            "cache_status": cache.get("status"),
            "created_utc": cache.get("created_utc"),
            "updated_utc": cache.get("updated_utc"),
            "task_checkpoint_commit": commits[1],
            "result_commit": commits[0],
            "cache_evidence": {"path": cache_rel.as_posix(), "sha256": digest(cache_raw)},
            "result": compact,
        }
        vectors[name] = vector(compact)
    comparisons = {
        "A_minus_H0": subtract(vectors["A"], vectors["H0"]),
        "B_minus_A": subtract(vectors["B"], vectors["A"]),
        "C_minus_A": subtract(vectors["C"], vectors["A"]),
        "D_minus_A": subtract(vectors["D"], vectors["A"]),
        "D_minus_B": subtract(vectors["D"], vectors["B"]),
        "D_minus_C": subtract(vectors["D"], vectors["C"]),
    }
    table = [
        {
            "variant": name,
            "paragraph_boundary": preflight["variants"][name]["paragraph_boundary"],
            "tail_realization": preflight["variants"][name]["tail_realization"],
            "fraction_human": vectors[name]["fraction_human"],
            "fraction_ai": vectors[name]["fraction_ai"],
            "fraction_ai_assisted": vectors[name]["fraction_ai_assisted"],
        }
        for name in ("A", "B", "C", "D")
    ]
    packet = {
        "format": "somatic-r15-eft-human-anchor-tail-factorial-result-v1",
        "directive": preflight["directive"],
        "article": preflight["article"],
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "starting_head": "57db7a082636ebaca56c5618d7f654b675cdbce1",
            "preflight_commit": git(root, "log", "-1", "--format=%H", "--", preflight_path.relative_to(root).as_posix()),
            "head_after_exact_results": RESULT_HEAD,
            "head_before_result_packet": RESULT_HEAD,
            "model": "pangram-4",
            "version": "4.0",
            "transport": "SHORT_DOCUMENT_API",
        },
        "variants": variants,
        "raw_result_deltas": comparisons,
        "factorial_target_fraction_table": table,
        "accounting": {
            "exact_completed_results_reused": 0,
            "cache_hits": 0,
            "new_paid_api_calls": 5,
            "ambiguous_calls": 0,
            "detector_reservations_created": 0,
            "stable_family_call_cap": 6,
            "stable_family_calls_used": 5,
            "reserved_slot_left_unused": 1,
            "article_mutations": 0,
            "registered_master_mutations": 0,
            "gui_actions": 0,
            "whole_document_calls": 0,
        },
        "stable_family_state": "COMPLETE_5_OF_6_RESERVED_SLOT_UNUSED",
    }
    output = experiment / "RESULT-PACKET.json"
    output.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": output.relative_to(root).as_posix(), "sha256": digest(output.read_bytes()), "target_fraction_table": table}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
