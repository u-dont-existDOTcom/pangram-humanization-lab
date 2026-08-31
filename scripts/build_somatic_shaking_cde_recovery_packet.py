#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


FAMILY = Path(
    "state/experiments/"
    "somatic-r15-shaking-human-anchor-guidance-social-tail-20260831"
)
OLD_PACKET = FAMILY / "RESULT-PACKET-GUI-CDE.json"
OUTPUT = FAMILY / "RESULT-PACKET-GUI-CDE-RECOVERY-002.json"
RECOVERY = Path("state/recovery/somatic-r15-shaking-c-ambiguity-20260831")
GUI_ROOT = Path("state/gui-runs/pangram-4")
SHAS = {
    "C": "b36e1e46c06d764a080d407dce5412defe76ccb9202deb1a8a14e265acf40370",
    "D": "b27446d695044a6749a2780f7629599177160d4a619758784b915b3cdc013900",
    "E": "75fb8426a498dcedb99bb7ed84d9f5a6e1653a29b6e2b7d5ff8f61fe5fb8563f",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} is not a JSON object")
    return value


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fractions(result: dict[str, Any]) -> dict[str, float]:
    if "summary" in result:
        summary = result["summary"]
    elif "fraction_human" in result:
        summary = result
    else:
        summary = result["parsed"]["summary"]
    return {
        "human": float(summary["fraction_human"]),
        "ai": float(summary["fraction_ai"]),
        "ai_assisted": float(summary["fraction_ai_assisted"]),
    }


def delta(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
    return {
        "fraction_human": left["human"] - right["human"],
        "fraction_ai": left["ai"] - right["ai"],
        "fraction_ai_assisted": left["ai_assisted"] - right["ai_assisted"],
    }


def validate_gui(label: str, receipt: dict[str, Any]) -> None:
    sha = SHAS[label]
    identity = receipt["history_api_exact_identity"]
    summary = receipt["parsed"]["summary"]
    if not (
        receipt["status"] == "complete"
        and receipt["input_sha256"] == sha
        and receipt["detector_version"] == "4.0"
        and receipt["parsed"]["detector_stage"] == "STAGE_SUCCESS"
        and identity["authorized_text_sha256"] == sha
        and identity["stored_text_sha256"] == sha
        and identity["transport_match_mode"] == "exact_utf8"
        and identity["api_path"] == "/api/history/<uuid>/"
        and all(key in summary for key in ("fraction_human", "fraction_ai", "fraction_ai_assisted"))
    ):
        raise RuntimeError(f"{label} failed exact GUI result gates")
    serialized = json.dumps(receipt)
    if "https://www.pangram.com/history/<uuid>" not in serialized and label in {"D", "E"}:
        raise RuntimeError(f"{label} has no masked report route")
    if "https://www.pangram.com/history/" in serialized.replace(
        "https://www.pangram.com/history/<uuid>", ""
    ):
        raise RuntimeError(f"{label} contains a private History route")


def main() -> int:
    old = read_json(OLD_PACKET)
    scans = [
        read_json(RECOVERY / "scan-01-exhaustive-detail.json"),
        read_json(RECOVERY / "scan-02-exhaustive-detail.json"),
    ]
    receipts = {label: read_json(GUI_ROOT / sha / "result.json") for label, sha in SHAS.items()}
    for label, receipt in receipts.items():
        validate_gui(label, receipt)
    if receipts["C"].get("classification") != "EXACT_GUI_RESULT_EXISTS_RECOVERED_AFTER_AMBIGUITY":
        raise RuntimeError("C recovery classification mismatch")
    if receipts["C"].get("new_c_clicks") != 0:
        raise RuntimeError("C recovery click accounting mismatch")

    table = {
        "H0": fractions(old["variants"]["H0"]["result"]),
        "A": fractions(old["variants"]["A"]["result"]),
        "B": fractions(old["variants"]["B"]["result"]),
        "C": fractions(receipts["C"]),
        "D": fractions(receipts["D"]),
        "E": fractions(receipts["E"]),
    }
    requested = {
        "C_minus_H0": delta(table["C"], table["H0"]),
        "D_minus_C": delta(table["D"], table["C"]),
        "E_minus_B": delta(table["E"], table["B"]),
        "E_minus_C": delta(table["E"], table["C"]),
        "E_minus_D": delta(table["E"], table["D"]),
        "status": "COMPLETE_MATHEMATICALLY_COMPARABLE_FRACTIONS",
    }
    variants = {key: old["variants"][key] for key in ("H0", "A", "B")}
    for label in ("C", "D", "E"):
        receipt = receipts[label]
        variants[label] = {
            "classification": (
                "EXACT_GUI_RESULT_EXISTS_RECOVERED_AFTER_AMBIGUITY"
                if label == "C"
                else "EXACT_GUI_RESULT_EXISTS"
            ),
            "input_sha256": SHAS[label],
            "transport": "local_playwright_gui",
            "captured_at_utc": receipt["captured_at_utc"],
            "detector_submission_attempted": receipt["detector_submission_attempted"],
            "history_api_exact_identity": receipt["history_api_exact_identity"],
            "result": receipt["parsed"],
            "windows": receipt.get("windows"),
            "report_body_sha256": receipt.get("report_body_sha256"),
            "report_pdf_sha256": receipt.get("report_pdf_sha256"),
        }

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    packet = {
        "format": "somatic-r15-shaking-gui-cde-recovery-result-v2",
        "directive_id": "SOMATIC-R15-SHAKING-C-AMBIGUITY-RECOVERY-001",
        "family": "somatic-r15-shaking-human-anchor-guidance-social-tail-20260831",
        "family_state": "CLOSED_6_OF_6",
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "model": "pangram-4",
            "required_version": "4.0",
            "directive_starting_head": "8bc3c8ba5341158ab82b1942500932665779d51c",
            "c_recovery_materialized_head": "c1b7638e",
            "after_conditional_gui_head_before_packet": head,
        },
        "c_ambiguity_recovery": {
            "reservation_time": "2026-08-31T04:04:17.182276Z",
            "failure_capture_time": "2026-08-31T04:07:24.622478Z",
            "final_classification": "EXACT_GUI_RESULT_EXISTS_RECOVERED_AFTER_AMBIGUITY",
            "provider_or_task_identity_recovered": True,
            "original_or_restored_tab_adjudicative_state": "NO_ADJUDICATIVE_STATE",
            "original_run_artifacts": [
                {
                    "name": name,
                    "sha256": file_sha(GUI_ROOT / SHAS["C"] / name),
                }
                for name in ("failure.json", "failure.png", "reservation.json")
            ],
            "read_only_scans": [
                {
                    "scan_id": scan["scanId"],
                    "started_at": scan["startedAt"],
                    "completed_at": scan["completedAt"],
                    "minutes_after_failure": scan["minutesAfterFailure"],
                    "pages_scanned": scan["historyApi"]["pagesScanned"],
                    "candidates_scanned": scan["historyApi"]["candidatesScanned"],
                    "detail_records_inspected": scan["historyApi"]["detailRecordsInspected"],
                    "pagination_exhausted": scan["historyApi"]["paginationExhausted"],
                    "detector_submission_attempted": scan["detectorSubmissionAttempted"],
                    "exact_history_result_recovered": scan["exactHistoryResultRecovered"],
                    "restored_tab_state_before_navigation": scan["restoredTabStateBeforeNavigation"],
                }
                for scan in scans
            ],
            "history_identity": receipts["C"]["history_api_exact_identity"],
            "result": receipts["C"]["parsed"],
            "windows": receipts["C"].get("windows"),
            "privacy": "NO_PRIVATE_HISTORY_URL_UUID_CREDENTIAL_COOKIE_STORAGE_OR_UNRELATED_TEXT_PERSISTED",
        },
        "variants": variants,
        "target_fraction_table": table,
        "completed_result_deltas": {
            "A_minus_H0": delta(table["A"], table["H0"]),
            "B_minus_A": delta(table["B"], table["A"]),
            **{key: value for key, value in requested.items() if key != "status"},
        },
        "requested_gui_deltas": requested,
        "accounting": {
            "historical_ambiguous_c_gui_actions": 1,
            "read_only_recovery_scans": 2,
            "new_c_clicks": 0,
            "new_d_clicks": 1,
            "new_e_clicks": 1,
            "new_api_calls": 0,
            "whole_document_calls": 0,
            "article_mutations": 0,
            "registered_master_mutations": 0,
            "force_overrides": 0,
        },
        "article_application_performed": False,
        "final_whole_document_measurement_performed": False,
        "ci_disposition": {
            "FULL_HISTORY_FIX": "PASS",
            "REMAINING_VALIDATOR_FINDINGS": "PRE_EXISTING_UNRELATED_MERGE_DEBT",
            "HUMANIZATION_EXECUTION_BLOCKED": "NO",
            "MERGE_BLOCKED_UNTIL_RECONCILED": "YES",
        },
    }
    OUTPUT.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "family_state": packet["family_state"],
                "fractions": table,
                "detector_head": head,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
