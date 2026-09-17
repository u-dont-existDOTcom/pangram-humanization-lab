#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT = "somatic-r15-eft-human-anchor-tail-factorial-20260831"
RESULT_HEAD = "731b0d56fc0b0555c9e37592fcfdf3669eb11a55"
E_SHA256 = "e9d2969aadbdd648ccd6b5aa36d6b7712b059a5b24a2acfcf95d29a4d458b7eb"
MEASUREMENT_KEY = f"{EXPERIMENT}-E"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


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


def main() -> int:
    root = Path.cwd().resolve()
    allowed_dirty = ["?? scripts/build_somatic_r15_eft_candidate_e_result.py"]
    if git(root, "rev-parse", "HEAD") != RESULT_HEAD or git(root, "status", "--porcelain").splitlines() != allowed_dirty:
        raise SystemExit("unexpected result head/worktree")
    experiment = root / "state" / "experiments" / EXPERIMENT
    preflight_path = experiment / "PREFLIGHT-E.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if not (
        preflight.get("preflight") == "PASS"
        and preflight.get("mechanical_source_assertions") == "PASS"
        and preflight.get("preservation", {}).get("overall") == "PASS"
        and preflight.get("candidate_e", {}).get("sha256") == E_SHA256
        and preflight.get("candidate_e", {}).get("pre_submission_classification") == "EXACT_API_NEVER_SUBMITTED"
    ):
        raise SystemExit("Candidate E preflight mismatch")

    input_path = root / preflight["candidate_e"]["input_path"]
    input_raw = input_path.read_bytes()
    if digest(input_raw) != E_SHA256:
        raise SystemExit("Candidate E input mismatch")
    cache_rel = Path("cache") / "pangram-4" / "4.0" / E_SHA256 / f"{MEASUREMENT_KEY}.json"
    cache_raw = (root / cache_rel).read_bytes()
    cache = json.loads(cache_raw.decode("utf-8"))
    if not (
        cache.get("text_sha256") == E_SHA256
        and cache.get("text", "").encode("utf-8") == input_raw
        and cache.get("measurement_key") == MEASUREMENT_KEY
        and cache.get("submitted_model") == "pangram-4"
        and cache.get("status") == "success"
        and cache.get("task_id")
    ):
        raise SystemExit("Candidate E cache/task binding mismatch")
    e_result = compact_result(cache.get("result") or {}, cache_rel.as_posix())
    if not (e_result.get("stage") == "STAGE_SUCCESS" and e_result.get("version") == "4.0"):
        raise SystemExit("Candidate E result version/stage mismatch")
    commits = git(root, "log", "--format=%H", "--", cache_rel.as_posix()).splitlines()
    if len(commits) < 2 or commits[0] != RESULT_HEAD:
        raise SystemExit("Candidate E checkpoint/result commits missing")

    family_packet_path = experiment / "RESULT-PACKET.json"
    family_packet = json.loads(family_packet_path.read_text(encoding="utf-8"))
    vectors = {name: vector(family_packet["variants"][name]["result"]) for name in ("H0", "A", "C", "D")}
    vectors["E"] = vector(e_result)
    deltas = {
        "E_minus_H0": subtract(vectors["E"], vectors["H0"]),
        "E_minus_A": subtract(vectors["E"], vectors["A"]),
        "E_minus_C": subtract(vectors["E"], vectors["C"]),
        "E_minus_D": subtract(vectors["E"], vectors["D"]),
    }
    packet = {
        "format": "somatic-r15-eft-candidate-e-result-v1",
        "directive": preflight["directive"],
        "article": preflight["article"],
        "detector": {
            **preflight["detector"],
            "preflight_commit": git(root, "log", "-1", "--format=%H", "--", preflight_path.relative_to(root).as_posix()),
            "task_checkpoint_commit": commits[1],
            "result_commit": commits[0],
            "head_before_result_packet": RESULT_HEAD,
        },
        "candidate_e": preflight["candidate_e"],
        "mechanical_source_assertions": preflight["mechanical_source_assertions"],
        "preservation": preflight["preservation"],
        "result_e": {
            "task_id": cache["task_id"],
            "submitted_model": cache["submitted_model"],
            "cache_status": cache["status"],
            "created_utc": cache.get("created_utc"),
            "updated_utc": cache.get("updated_utc"),
            "cache_evidence": {"path": cache_rel.as_posix(), "sha256": digest(cache_raw)},
            "result": e_result,
        },
        "raw_result_deltas": deltas,
        "accounting": {
            "completed_family_calls_before_e": 5,
            "new_paid_api_calls_for_e": 1,
            "stable_family_call_cap": 6,
            "stable_family_calls_used": 6,
            "cache_hits_for_e": 0,
            "ambiguous_calls": 0,
            "detector_reservations_created": 0,
            "article_mutations": 0,
            "registered_master_mutations": 0,
            "gui_actions": 0,
            "whole_document_calls": 0,
        },
        "stable_family_state": "CLOSED_6_OF_6",
    }
    output = experiment / "RESULT-PACKET-E.json"
    output.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": output.relative_to(root).as_posix(), "sha256": digest(output.read_bytes()), "result": e_result, "raw_result_deltas": deltas}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
