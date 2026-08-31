#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT = "somatic-r15-api-gui-human-window-calibration-20260831"
VARIANTS = {
    "H1": {
        "sha256": "d9a1fcd6ed832117b32e07844300f5b30d9067884481b14a63740dcc5bfe5d3b",
        "measurement_key": f"{EXPERIMENT}-H1-gui-human-window-5",
    },
    "H2": {
        "sha256": "1d7bb2473eea7c4c42229726aaeb953fc5fb6f30c1cfc316f2673e90be56f3aa",
        "measurement_key": f"{EXPERIMENT}-H2-gui-human-window-7",
    },
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=root, text=True, encoding="utf-8"
    ).strip()


def compact_window(window: dict[str, Any], cache_path: str) -> dict[str, Any]:
    text = str(window.get("text") or "")
    return {
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
        "exact_text_pointer": f"{cache_path}#/result/windows/0/text",
    }


def main() -> int:
    root = Path.cwd().resolve()
    experiment = root / "state" / "experiments" / EXPERIMENT
    preflight_path = experiment / "PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if preflight.get("preflight") != "PASS":
        raise SystemExit("preflight is not PASS")
    observed_head = git(root, "rev-parse", "HEAD")
    if observed_head != "d021f8832cefb46dae3f92d7e1d5a638e3faefe2":
        raise SystemExit(f"unexpected detector result head: {observed_head}")

    output_variants: dict[str, Any] = {}
    human_count = 0
    for name, expected in VARIANTS.items():
        input_info = preflight["variants"][name]
        input_path = root / input_info["input_path"]
        input_raw = input_path.read_bytes()
        if digest(input_raw) != expected["sha256"]:
            raise SystemExit(f"{name}: input identity mismatch")
        cache_path = (
            Path("cache")
            / "pangram-4"
            / "4.0"
            / expected["sha256"]
            / f"{expected['measurement_key']}.json"
        )
        cache_raw = (root / cache_path).read_bytes()
        cache = json.loads(cache_raw.decode("utf-8"))
        if cache.get("text_sha256") != expected["sha256"] or cache.get("text", "").encode("utf-8") != input_raw:
            raise SystemExit(f"{name}: cache text identity mismatch")
        if cache.get("status") != "success" or not cache.get("task_id"):
            raise SystemExit(f"{name}: exact terminal task unavailable")
        result = cache.get("result") or {}
        if result.get("version") != "4.0" or result.get("stage") != "STAGE_SUCCESS":
            raise SystemExit(f"{name}: detector version/stage mismatch")
        if result.get("fraction_human") == 1.0:
            human_count += 1
        commits = git(root, "log", "--format=%H", "--", cache_path.as_posix()).splitlines()
        if len(commits) < 2:
            raise SystemExit(f"{name}: task checkpoint/result commits unavailable")
        windows = result.get("windows") or []
        output_variants[name] = {
            "input": input_info,
            "gui_prior": input_info["gui_prior"],
            "measurement_key": expected["measurement_key"],
            "cache_state_before_call": "ABSENT",
            "task_id": cache["task_id"],
            "submitted_model": cache.get("submitted_model"),
            "cache_status": cache.get("status"),
            "created_utc": cache.get("created_utc"),
            "updated_utc": cache.get("updated_utc"),
            "task_checkpoint_commit": commits[1],
            "result_commit": commits[0],
            "cache_evidence": {
                "path": cache_path.as_posix(),
                "sha256": digest(cache_raw),
            },
            "api_result": {
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
                "windows": [compact_window(item, cache_path.as_posix()) for item in windows],
            },
            "api_vs_gui_label_agreement": (
                input_info["gui_prior"]["label"] == "Human"
                and result.get("fraction_human") == 1.0
            ),
        }

    if human_count == 2:
        classification = "API_RECOGNIZES_BOTH_GUI_HUMAN_WINDOWS"
    elif human_count == 1:
        classification = "API_RECOGNIZES_ONE_GUI_HUMAN_WINDOW"
    elif human_count == 0:
        classification = "API_RECOGNIZES_NEITHER_GUI_HUMAN_WINDOW"
    else:
        classification = "INCOMPLETE_OR_AMBIGUOUS"
    value = {
        "format": "somatic-r15-api-gui-human-window-calibration-result-v1",
        "directive": {
            "id": "SOMATIC-R15-CROSS-TRANSPORT-001",
            "packet_path": "tasks/somatic-r15-clean-continuation-20260830/CHAT-CROSS-TRANSPORT-CALIBRATION-001.md",
            "packet_git_blob": "2de6157d85fa9fe329517c6066f124c9c7281865",
        },
        "article": preflight["article"],
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "starting_head": "0588d51d15dc4087c72adc4c35fd78d6be826887",
            "preflight_commit": git(root, "log", "-1", "--format=%H", "--", preflight_path.relative_to(root).as_posix()),
            "head_after_exact_results": observed_head,
            "head_before_result_packet": observed_head,
            "model": "pangram-4",
            "version": "4.0",
            "transport": "SHORT_DOCUMENT_API",
        },
        "variants": output_variants,
        "route_comparison_classification": classification,
        "accounting": {
            "exact_completed_results_reused": 0,
            "cache_hits": 0,
            "new_paid_api_calls": 2,
            "ambiguous_calls": 0,
            "detector_reservations_created": 0,
            "whole_document_calls": 0,
            "gui_actions": 0,
            "article_mutations": 0,
            "registered_master_mutations": 0,
        },
        "stable_family_state": "COMPLETE_2_OF_2",
    }
    output = experiment / "RESULT-PACKET.json"
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"classification": classification, "output": output.relative_to(root).as_posix(), "sha256": digest(output.read_bytes())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
