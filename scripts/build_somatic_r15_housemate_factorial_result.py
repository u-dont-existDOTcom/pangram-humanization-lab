#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT = "somatic-r15-housemate-human-anchor-hour-later-tail-20260831"
RESULT_HEAD = "e8c431c71855bc4485c02dc43214055cb1a784f8"


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
    windows = result.get("windows") or []
    # The comparison requested by Chat binds latent scores to the final returned
    # window when a result has multiple segments, which is the tested tail window.
    window = windows[-1] if windows else {}
    return {
        "fraction_human": float(result["fraction_human"]),
        "fraction_ai": float(result["fraction_ai"]),
        "fraction_ai_assisted": float(result["fraction_ai_assisted"]),
        "last_window_ai_assistance_score": float(window["ai_assistance_score"]),
        "last_window_humanizer_score": float(window["humanizer_score"]),
    }


def subtract(target: dict[str, float], source: dict[str, float]) -> dict[str, float]:
    return {key: target[key] - source[key] for key in target}


def main() -> int:
    root = Path.cwd().resolve()
    allowed = [
        "?? scripts/build_somatic_r15_housemate_factorial_result.py",
        f"?? state/experiments/{EXPERIMENT}/RESULT-PACKET.json",
    ]
    if git(root, "rev-parse", "HEAD") != RESULT_HEAD or git(root, "status", "--porcelain").splitlines() != allowed:
        raise SystemExit("unexpected exact-results head/worktree")
    experiment = root / "state" / "experiments" / EXPERIMENT
    preflight_path = experiment / "PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if not (
        preflight.get("preflight") == "PASS"
        and preflight.get("mechanical_source_assertions") == "PASS"
        and preflight.get("direct_tail", {}).get("preservation", {}).get("overall") == "PASS"
    ):
        raise SystemExit("preflight/preservation mismatch")

    variants: dict[str, Any] = {}
    vectors: dict[str, dict[str, float]] = {}
    h0_identity = preflight["variants"]["H0"]
    h0_cache_rel = Path(h0_identity["cache_records"][0]["path"])
    h0_cache_raw = (root / h0_cache_rel).read_bytes()
    h0_cache = json.loads(h0_cache_raw.decode("utf-8"))
    h0_input_raw = (root / h0_identity["input_path"]).read_bytes()
    if not (
        digest(h0_input_raw) == h0_identity["sha256"]
        and h0_cache.get("text", "").encode("utf-8") == h0_input_raw
        and h0_cache.get("task_id") == preflight["h0_reuse"]["task_id"]
        and h0_cache.get("status") == "success"
    ):
        raise SystemExit("H0 reuse binding mismatch")
    h0_result = compact_result(h0_cache["result"], h0_cache_rel.as_posix())
    if h0_result != preflight["h0_reuse"]["result"]:
        # Preflight stores the already compacted prior result, so exact equality
        # is expected except for its path pointers, which were preserved.
        raise SystemExit("H0 prior result mismatch")
    variants["H0"] = {
        "input": h0_identity,
        "reuse": "EXACT_COMPLETED_RESULT_REUSED",
        "task_id": h0_cache["task_id"],
        "cache_evidence": {"path": h0_cache_rel.as_posix(), "sha256": digest(h0_cache_raw)},
        "result": h0_result,
    }
    vectors["H0"] = vector(h0_result)

    for name in ("A", "B", "C", "D", "E"):
        identity = preflight["variants"][name]
        input_raw = (root / identity["input_path"]).read_bytes()
        if digest(input_raw) != identity["sha256"]:
            raise SystemExit(f"{name}: input mismatch")
        cache_rel = Path("cache") / "pangram-4" / "4.0" / identity["sha256"] / f"{identity['measurement_key']}.json"
        cache_raw = (root / cache_rel).read_bytes()
        cache = json.loads(cache_raw.decode("utf-8"))
        if not (
            cache.get("text_sha256") == identity["sha256"]
            and cache.get("text", "").encode("utf-8") == input_raw
            and cache.get("status") == "success"
            and cache.get("task_id")
            and cache.get("submitted_model") == "pangram-4"
        ):
            raise SystemExit(f"{name}: cache/task binding mismatch")
        compact = compact_result(cache["result"], cache_rel.as_posix())
        if compact.get("stage") != "STAGE_SUCCESS" or compact.get("version") != "4.0":
            raise SystemExit(f"{name}: detector version/stage mismatch")
        commits = git(root, "log", "--format=%H", "--", cache_rel.as_posix()).splitlines()
        if len(commits) < 2:
            raise SystemExit(f"{name}: checkpoint/result commits missing")
        variants[name] = {
            "input": identity,
            "cache_state_before_call": "ABSENT",
            "task_id": cache["task_id"],
            "submitted_model": cache["submitted_model"],
            "cache_status": cache["status"],
            "created_utc": cache.get("created_utc"),
            "updated_utc": cache.get("updated_utc"),
            "task_checkpoint_commit": commits[1],
            "result_commit": commits[0],
            "cache_evidence": {"path": cache_rel.as_posix(), "sha256": digest(cache_raw)},
            "result": compact,
        }
        vectors[name] = vector(compact)

    deltas = {
        "A_minus_H0": subtract(vectors["A"], vectors["H0"]),
        "B_minus_A": subtract(vectors["B"], vectors["A"]),
        "C_minus_H0": subtract(vectors["C"], vectors["H0"]),
        "D_minus_C": subtract(vectors["D"], vectors["C"]),
        "E_minus_C": subtract(vectors["E"], vectors["C"]),
        "E_minus_D": subtract(vectors["E"], vectors["D"]),
        "E_minus_B": subtract(vectors["E"], vectors["B"]),
    }
    table = [
        {
            "variant": name,
            "fraction_human": vectors[name]["fraction_human"],
            "fraction_ai": vectors[name]["fraction_ai"],
            "fraction_ai_assisted": vectors[name]["fraction_ai_assisted"],
        }
        for name in ("H0", "A", "B", "C", "D", "E")
    ]
    packet = {
        "format": "somatic-r15-housemate-factorial-result-v1",
        "directive": preflight["directive"],
        "article": preflight["article"],
        "detector": {**preflight["detector"], "preflight_commit": git(root, "log", "-1", "--format=%H", "--", preflight_path.relative_to(root).as_posix()), "head_after_exact_results": RESULT_HEAD, "head_before_result_packet": RESULT_HEAD},
        "mechanical_source_assertions": preflight["mechanical_source_assertions"],
        "direct_tail": preflight["direct_tail"],
        "variants": variants,
        "raw_result_deltas": deltas,
        "target_fraction_table": table,
        "accounting": {"exact_completed_results_reused": 1, "new_paid_api_calls": 5, "cache_hits_for_new_variants": 0, "ambiguous_calls": 0, "stable_family_result_cap": 6, "stable_family_results_complete": 6, "article_mutations": 0, "registered_master_mutations": 0, "detector_reservations_created": 0, "gui_actions": 0, "whole_document_calls": 0},
        "stable_family_state": "CLOSED_6_OF_6",
    }
    output = experiment / "RESULT-PACKET.json"
    output.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": output.relative_to(root).as_posix(), "sha256": digest(output.read_bytes()), "target_fraction_table": table, "raw_result_deltas": deltas}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
