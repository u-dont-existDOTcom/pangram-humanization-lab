#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


FAMILY = Path(
    "state/experiments/somatic-r15-housemate-green-next-day-wake-tail-20260831"
)
OUTPUT = FAMILY / "RESULT-PACKET.json"
PRIOR = Path(
    "state/experiments/somatic-r15-housemate-human-anchor-hour-later-tail-20260831/"
    "RESULT-PACKET.json"
)
H0_SHA = "29d4af12b023c3a71ba2d16583b101e3ffe2f042652b36c4e57dce42e7d16abc"
A_SHA = "85406d364a8b65adcac9ee0d14bf0bc2e8fe82c7399dbecf235bf5717e24d34b"
B_SHA = "0c46ea5ff3fb23cd51df4df9d0c667d65836afbcaacd23df7670998eb3ab11e4"
A_DIR = Path("state/gui-runs/pangram-4") / A_SHA


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} is not a JSON object")
    return value


def old_fractions(result: dict[str, Any]) -> dict[str, float]:
    return {
        "human": float(result["fraction_human"]),
        "ai": float(result["fraction_ai"]),
        "ai_assisted": float(result["fraction_ai_assisted"]),
    }


def new_fractions(result: dict[str, Any]) -> dict[str, float]:
    summary = result["summary"]
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


def main() -> int:
    prior = read_json(PRIOR)
    h0 = prior["variants"]["D"]
    h0_result = h0["result"]
    a = read_json(A_DIR / "result.json")
    localization = read_json(FAMILY / "A-EXACT-HISTORY-LOCALIZATION.json")
    h0_values = old_fractions(h0_result)
    a_values = new_fractions(a["parsed"])
    identity = a["history_api_exact_identity"]
    if not (
        h0["input"]["sha256"] == H0_SHA
        and h0_result["version"] == "4.0"
        and h0_result["stage"] == "STAGE_SUCCESS"
        and h0_values == {"human": 1.0, "ai": 0.0, "ai_assisted": 0.0}
        and h0_result["windows"][0]["confidence"] == "High"
        and a["status"] == "complete"
        and a["input_sha256"] == A_SHA
        and a["detector_version"] == "4.0"
        and a["parsed"]["detector_stage"] == "STAGE_SUCCESS"
        and a_values == {"human": 1.0, "ai": 0.0, "ai_assisted": 0.0}
        and identity["authorized_text_sha256"] == A_SHA
        and identity["stored_text_sha256"] == A_SHA
        and identity["transport_match_mode"] == "exact_utf8"
        and localization["inputSha256"] == A_SHA
        and localization["inputWords"] == 344
        and localization["detectorSubmissionAttempted"] is False
        and localization["exactHistoryResultRecovered"] is True
        and localization["historyApi"]["paginationExhausted"] is True
        and localization["historyResultIdentity"] == identity
        and localization["result"] == a["parsed"]
        and localization["windows"][0]["confidence"] == "High"
    ):
        raise RuntimeError("housemate next-day result failed exact authority gates")
    serialized = json.dumps({"a": a, "localization": localization})
    if "https://www.pangram.com/history/" in serialized.replace(
        "https://www.pangram.com/history/<uuid>", ""
    ):
        raise RuntimeError("private History route present")

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    packet = {
        "format": "somatic-r15-housemate-next-day-wake-result-v1",
        "directive_id": "SOMATIC-R15-SURFACE-010",
        "family": "somatic-r15-housemate-green-next-day-wake-tail-20260831",
        "family_state": "CLOSED_A_HUMAN_1_0_B_NOT_SUBMITTED",
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "model": "pangram-4",
            "required_version": "4.0",
            "starting_head": "a2442fb343e43247b445d5884eaa8f7daa44a514",
            "after_measurement_before_packet": head,
        },
        "article_authority": {
            "branch": "task/somatic-r15-clean-continuation-20260830",
            "packet_head": "841e4279dc4f0b12c16d2d630d687a2317f59cf2",
            "candidate_sha256": "1e08284ce544b851b516eebdf38f3f8efb2497e477a0104270880f49aab7d81e",
            "registered_master_sha256": "1e7e94717f40e7a4de77974a896f600a1bf2769d9c1846cbe84275e136ff5202",
        },
        "variants": {
            "H0": {
                "classification": "EXACT_COMPLETED_RESULT_REUSE_ONLY",
                "input_sha256": H0_SHA,
                "input_identity": {
                    "whitespace_words": 292,
                    "unicode_characters": 1637,
                    "utf8_bytes": 1637,
                    "terminal_newline": False,
                },
                "result": h0_result,
                "cache_evidence": h0["cache_evidence"],
                "task_id": h0["task_id"],
                "result_authority_commit": "6604fb2f215e1bf3fe5df3605ba973d2d7490ebc",
            },
            "A": {
                "classification_before_action": "EXACT_GUI_NEVER_SUBMITTED",
                "classification": "EXACT_GUI_RESULT_EXISTS",
                "input_sha256": A_SHA,
                "input_identity": {
                    "whitespace_words": 344,
                    "unicode_characters": 1923,
                    "utf8_bytes": 1923,
                    "terminal_newline": False,
                },
                "detector_submission_attempted": True,
                "captured_at_utc": a["captured_at_utc"],
                "prediction": identity["record_prediction"],
                "prediction_short": a["parsed"]["prediction_short"],
                "headline": a["parsed"]["headline"],
                "confidence": localization["windows"][0]["confidence"],
                "history_api_exact_identity": identity,
                "result": a["parsed"],
                "windows": localization["windows"],
                "report_body_sha256": a["report_body_sha256"],
                "report_pdf_sha256": a["report_pdf_sha256"],
                "reservation": a["submission_reservation"],
                "read_only_history_recovery": {
                    "initial_exact_result_found": False,
                    "initial_history_candidates_inspected": 10,
                    "exhaustive_scan": {
                        "started_at": localization["startedAt"],
                        "completed_at": localization["completedAt"],
                        "pages_scanned": localization["historyApi"]["pagesScanned"],
                        "candidates_scanned": localization["historyApi"][
                            "candidatesScanned"
                        ],
                        "detail_records_inspected": localization["historyApi"][
                            "detailRecordsInspected"
                        ],
                        "pagination_exhausted": True,
                        "exact_result_recovered": True,
                        "detector_submission_attempted": False,
                    },
                },
            },
            "B": {
                "classification": "CONDITIONALLY_NOT_EXECUTED_AFTER_A_HUMAN_1_0",
                "input_sha256": B_SHA,
                "input_identity": {
                    "whitespace_words": 355,
                    "unicode_characters": 1969,
                    "utf8_bytes": 1969,
                    "terminal_newline": False,
                },
                "detector_submission_attempted": False,
                "result": None,
            },
        },
        "fraction_table": {"H0": h0_values, "A": a_values, "B": None},
        "deltas": {
            "H0_to_A": delta(a_values, h0_values),
            "H0_to_B": None,
            "A_to_B": None,
            "status": "A_COMPLETE_B_CORRECTLY_SKIPPED",
        },
        "accounting": {
            "h0_reused_results": 1,
            "a_cache_hits_before_action": 0,
            "a_read_only_history_scans": 2,
            "a_reservations": 1,
            "a_clicks": 1,
            "b_reservations": 0,
            "b_clicks": 0,
            "new_api_calls": 0,
            "new_short_gui_clicks": 1,
            "whole_document_calls": 0,
            "force_overrides": 0,
            "article_mutations": 0,
            "registered_master_mutations": 0,
        },
        "ci_disposition": {
            "FULL_HISTORY_FIX": "PASS",
            "REMAINING_VALIDATOR_FINDINGS": "PRE_EXISTING_UNRELATED_MERGE_DEBT",
            "MERGE_BLOCKED_UNTIL_RECONCILED": "YES",
        },
        "article_application_performed": False,
        "final_whole_document_measurement_performed": False,
        "privacy": "NO_PRIVATE_HISTORY_URL_UUID_CREDENTIAL_COOKIE_STORAGE_OR_UNRELATED_TEXT_PERSISTED",
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
                "a_fractions": a_values,
                "b_submitted": False,
                "head": head,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
