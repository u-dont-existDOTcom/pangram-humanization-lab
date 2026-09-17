#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT = "somatic-r15-shaking-human-anchor-guidance-social-tail-20260831"
EXPECTED_HEAD = "8e070e67df06b5a26ce837aa235090966c7448e0"
SHA = {
    "H0": "d9a1fcd6ed832117b32e07844300f5b30d9067884481b14a63740dcc5bfe5d3b",
    "A": "683a76b075325bcacdf2d8a92b835add258964890a27764f96d1072922035119",
    "B": "fcdc545d9d14ebe588755e705a5ea185f7508b9d465f5851a1ca3c47523297fd",
    "C": "b36e1e46c06d764a080d407dce5412defe76ccb9202deb1a8a14e265acf40370",
    "D": "b27446d695044a6749a2780f7629599177160d4a619758784b915b3cdc013900",
    "E": "75fb8426a498dcedb99bb7ed84d9f5a6e1653a29b6e2b7d5ff8f61fe5fb8563f",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def fraction(result: dict[str, Any], key: str) -> float:
    return float(result[key])


def delta(left: dict[str, Any], right: dict[str, Any]) -> dict[str, float]:
    return {
        "fraction_human": fraction(left, "fraction_human") - fraction(right, "fraction_human"),
        "fraction_ai": fraction(left, "fraction_ai") - fraction(right, "fraction_ai"),
        "fraction_ai_assisted": fraction(left, "fraction_ai_assisted") - fraction(right, "fraction_ai_assisted"),
    }


def main() -> int:
    root = Path.cwd().resolve()
    if git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise SystemExit("detector head mismatch")
    experiment = root / "state" / "experiments" / EXPERIMENT
    preflight = read_json(experiment / "GUI-CDE-PREFLIGHT.json")
    if preflight.get("preflight") != "PASS":
        raise SystemExit("GUI preflight is not PASS")

    prior = read_json(
        root
        / "state/experiments/somatic-r15-api-gui-human-window-calibration-20260831/RESULT-PACKET.json"
    )["variants"]["H1"]
    h0 = prior["api_result"]
    if not (
        prior["input"]["sha256"] == SHA["H0"]
        and prior["task_id"] == "8ce5a703-e012-40f6-a260-9517a40eeb74"
        and h0["version"] == "4.0"
        and h0["fraction_human"] == 1.0
    ):
        raise SystemExit("H0 reuse mismatch")

    completed: dict[str, dict[str, Any]] = {}
    for name in ("A", "B"):
        path = root / "cache" / "pangram-4" / "4.0" / SHA[name] / f"{EXPERIMENT}-{name}.json"
        record = read_json(path)
        result = record.get("result") or {}
        if not (
            record.get("status") == "success"
            and record.get("text_sha256") == SHA[name]
            and result.get("version") == "4.0"
            and result.get("stage") == "STAGE_SUCCESS"
        ):
            raise SystemExit(f"{name} API result mismatch")
        completed[name] = record

    gui_root = root / "state" / "gui-runs" / "pangram-4"
    c_dir = gui_root / SHA["C"]
    reservation = read_json(c_dir / "reservation.json")
    failure = read_json(c_dir / "failure.json")
    recovery = read_json(experiment / "gui-preflight" / "C-post-click-history-probe.json")
    if not (
        reservation.get("status") == "reserved"
        and reservation.get("input_sha256") == SHA["C"]
        and reservation.get("detector_submission_attempted") is False
        and failure.get("status") == "failed"
        and failure.get("input_sha256") == SHA["C"]
        and failure.get("detector_submission_attempted") is True
        and failure.get("stage") == "wait_report"
        and recovery.get("status") == "not_found"
        and recovery.get("current_exact_history_record_found") is False
        and recovery.get("detector_submission_attempted") is False
        and recovery.get("browser_history_candidates_inspected") == 62
        and not (c_dir / "result.json").exists()
    ):
        raise SystemExit("C ambiguous/recovery evidence mismatch")
    for name in ("D", "E"):
        directory = gui_root / SHA[name]
        if any((directory / filename).exists() for filename in ("reservation.json", "failure.json", "result.json")):
            raise SystemExit(f"{name} unexpectedly has GUI action evidence")

    variants: dict[str, Any] = {
        "H0": {
            "input_sha256": SHA["H0"],
            "transport": "api_reuse",
            "classification": "EXACT_COMPLETED_RESULT_REUSE",
            "task_id": prior["task_id"],
            "result": h0,
        },
        "A": {
            "input_sha256": SHA["A"],
            "transport": "short_api",
            "classification": "EXACT_COMPLETED_RESULT",
            "task_id": completed["A"]["task_id"],
            "result": completed["A"]["result"],
        },
        "B": {
            "input_sha256": SHA["B"],
            "transport": "short_api",
            "classification": "EXACT_COMPLETED_RESULT",
            "task_id": completed["B"]["task_id"],
            "result": completed["B"]["result"],
        },
        "C": {
            "input_sha256": SHA["C"],
            "transport": "local_playwright_gui",
            "classification": "EXACT_GUI_ACTION_AMBIGUOUS_HISTORY_NOT_FOUND",
            "reserved_at_utc": reservation["reserved_at_utc"],
            "failure_captured_at_utc": failure["captured_at_utc"],
            "failure_stage": failure["stage"],
            "detector_submission_attempted": True,
            "exact_history_result_found": False,
            "history_candidates_inspected": recovery["browser_history_candidates_inspected"],
            "history_api_records_observed": recovery["history_api_records_observed"],
            "result": None,
        },
        "D": {
            "input_sha256": SHA["D"],
            "transport": "local_playwright_gui",
            "classification": "EXACT_GUI_NEVER_SUBMITTED_NOT_ATTEMPTED_AFTER_PRIOR_AMBIGUITY",
            "result": None,
        },
        "E": {
            "input_sha256": SHA["E"],
            "transport": "local_playwright_gui",
            "classification": "EXACT_GUI_NEVER_SUBMITTED_NOT_ATTEMPTED_AFTER_PRIOR_AMBIGUITY",
            "result": None,
        },
    }
    a_result = completed["A"]["result"]
    b_result = completed["B"]["result"]
    packet = {
        "format": "somatic-r15-shaking-gui-cde-result-v1",
        "directive_id": "SOMATIC-R15-SHAKING-GUI-COMPLETION-001",
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "starting_head": EXPECTED_HEAD,
            "model": "pangram-4",
            "required_version": "4.0",
        },
        "variants": variants,
        "completed_result_deltas": {
            "A_minus_H0": delta(a_result, h0),
            "B_minus_A": delta(b_result, a_result),
        },
        "requested_gui_deltas": {
            "C_minus_H0": None,
            "D_minus_C": None,
            "E_minus_C": None,
            "E_minus_D": None,
            "E_minus_B": None,
            "status": "NOT_MATHEMATICALLY_COMPARABLE_WITHOUT_C_D_E_RESULTS",
        },
        "target_fraction_table": {
            "H0": {"human": h0["fraction_human"], "ai": h0["fraction_ai"], "ai_assisted": h0["fraction_ai_assisted"]},
            "A": {"human": a_result["fraction_human"], "ai": a_result["fraction_ai"], "ai_assisted": a_result["fraction_ai_assisted"]},
            "B": {"human": b_result["fraction_human"], "ai": b_result["fraction_ai"], "ai_assisted": b_result["fraction_ai_assisted"]},
            "C": None,
            "D": None,
            "E": None,
        },
        "accounting": {
            "new_api_calls": 0,
            "new_short_gui_clicks": 1,
            "new_short_gui_completed_results": 0,
            "ambiguous_short_gui_actions": 1,
            "history_recovery_scans_after_click": 1,
            "whole_document_calls": 0,
            "article_mutations": 0,
            "registered_master_mutations": 0,
        },
        "ci_disposition": {
            "FULL_HISTORY_FIX": "PASS",
            "REMAINING_VALIDATOR_FINDINGS": "PRE_EXISTING_UNRELATED_MERGE_DEBT",
            "HUMANIZATION_EXECUTION_BLOCKED": "NO",
            "MERGE_BLOCKED_UNTIL_RECONCILED": "YES",
        },
        "family_state": "UNRESOLVED_C_GUI_ACTION_AMBIGUOUS_3_OF_6",
        "article_application_performed": False,
        "final_whole_document_measurement_performed": False,
    }
    output = experiment / "RESULT-PACKET-GUI-CDE.json"
    output.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "family_state": packet["family_state"],
                "C": variants["C"]["classification"],
                "D": variants["D"]["classification"],
                "E": variants["E"]["classification"],
                "accounting": packet["accounting"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
