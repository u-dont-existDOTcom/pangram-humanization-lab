#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


FAMILY = Path(
    "state/experiments/"
    "somatic-r15-shaking-current-anchor-residual-social-tail-20260831"
)
OUTPUT = FAMILY / "RESULT-PACKET.json"
PRIOR = Path(
    "state/experiments/"
    "somatic-r15-shaking-human-anchor-guidance-social-tail-20260831/"
    "RESULT-PACKET-GUI-CDE-RECOVERY-002.json"
)
H0_SHA = "b36e1e46c06d764a080d407dce5412defe76ccb9202deb1a8a14e265acf40370"
A_SHA = "03037241afe8827df5b1ca2b81bc877704d5e198229a9759237b76245807ecd1"
B_SHA = "fa8625ab5686641eb2c1e15b7799992a43023fe2814a68737df88f17091542b5"
A_DIR = Path("state/gui-runs/pangram-4") / A_SHA


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} is not a JSON object")
    return value


def fractions(summary: dict[str, Any]) -> dict[str, float]:
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
    a = read_json(A_DIR / "result.json")
    localization = read_json(FAMILY / "A-EXACT-HISTORY-LOCALIZATION.json")
    h0_result = prior["variants"]["C"]["result"]
    h0_summary = h0_result["summary"]
    a_summary = a["parsed"]["summary"]
    h0_fractions = fractions(h0_summary)
    a_fractions = fractions(a_summary)
    identity = a["history_api_exact_identity"]
    if not (
        prior["variants"]["C"]["classification"]
        == "EXACT_GUI_RESULT_EXISTS_RECOVERED_AFTER_AMBIGUITY"
        and prior["variants"]["C"]["input_sha256"] == H0_SHA
        and h0_fractions == {"human": 1.0, "ai": 0.0, "ai_assisted": 0.0}
        and a["status"] == "complete"
        and a["input_sha256"] == A_SHA
        and a["detector_version"] == "4.0"
        and a["parsed"]["detector_stage"] == "STAGE_SUCCESS"
        and a_fractions == {"human": 1.0, "ai": 0.0, "ai_assisted": 0.0}
        and identity["authorized_text_sha256"] == A_SHA
        and identity["stored_text_sha256"] == A_SHA
        and identity["transport_match_mode"] == "exact_utf8"
        and localization["inputSha256"] == A_SHA
        and localization["detectorSubmissionAttempted"] is False
        and localization["exactHistoryResultRecovered"] is True
        and localization["historyApi"]["paginationExhausted"] is True
        and localization["historyResultIdentity"] == identity
        and localization["result"] == a["parsed"]
    ):
        raise RuntimeError("residual-social result failed exact authority gates")
    if "https://www.pangram.com/history/" in json.dumps(
        {"a": a, "localization": localization}
    ).replace("https://www.pangram.com/history/<uuid>", ""):
        raise RuntimeError("private History route present")

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    packet = {
        "format": "somatic-r15-shaking-residual-social-result-v1",
        "directive_id": "SOMATIC-R15-SURFACE-009",
        "family": "somatic-r15-shaking-current-anchor-residual-social-tail-20260831",
        "family_state": "CLOSED_A_HUMAN_1_0_B_NOT_SUBMITTED",
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "model": "pangram-4",
            "required_version": "4.0",
            "starting_head": "d809006f58e97b352b4d790e876d06f85cbf4f8e",
            "after_measurement_and_localization_before_packet": head,
        },
        "article_authority": {
            "branch": "task/somatic-r15-clean-continuation-20260830",
            "packet_head": "011a99d88cc0ebd69d479a8ea03a426d3dc5e793",
            "candidate_sha256": "5a6226ca0056610b4492de7713a43bb152dde1079d81b5c05896c70fcf138679",
            "registered_master_sha256": "1e7e94717f40e7a4de77974a896f600a1bf2769d9c1846cbe84275e136ff5202",
        },
        "variants": {
            "H0": {
                "classification": "EXACT_GUI_RESULT_EXISTS_REUSE_ONLY",
                "input_sha256": H0_SHA,
                "input_identity": {
                    "whitespace_words": 293,
                    "unicode_characters": 1631,
                    "utf8_bytes": 1641,
                    "terminal_newline": False,
                },
                "history_api_exact_identity": prior["variants"]["C"][
                    "history_api_exact_identity"
                ],
                "result": h0_result,
                "windows": prior["variants"]["C"].get("windows"),
                "result_authority_head": "d809006f58e97b352b4d790e876d06f85cbf4f8e",
            },
            "A": {
                "classification_before_action": "EXACT_GUI_NEVER_SUBMITTED",
                "classification": "EXACT_GUI_RESULT_EXISTS",
                "input_sha256": A_SHA,
                "input_identity": {
                    "whitespace_words": 315,
                    "unicode_characters": 1758,
                    "utf8_bytes": 1768,
                    "terminal_newline": False,
                },
                "detector_submission_attempted": True,
                "captured_at_utc": a["captured_at_utc"],
                "prediction": identity["record_prediction"],
                "prediction_short": a["parsed"]["prediction_short"],
                "headline": a["parsed"]["headline"],
                "confidence": localization["windows"][0].get("confidence")
                if localization["windows"]
                else None,
                "history_api_exact_identity": identity,
                "result": a["parsed"],
                "windows": localization["windows"],
                "report_body_sha256": a["report_body_sha256"],
                "report_pdf_sha256": a["report_pdf_sha256"],
                "reservation": a["submission_reservation"],
                "read_only_history_recovery": {
                    "initial_exact_result_found": False,
                    "initial_history_candidates_inspected": 10,
                    "post_result_list_localization_found": False,
                    "post_result_list_localization_candidates_inspected": 10,
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
                    "whitespace_words": 310,
                    "unicode_characters": 1731,
                    "utf8_bytes": 1741,
                    "terminal_newline": False,
                },
                "detector_submission_attempted": False,
                "result": None,
            },
        },
        "fraction_table": {
            "H0": h0_fractions,
            "A": a_fractions,
            "B": None,
        },
        "deltas": {
            "H0_to_A": delta(a_fractions, h0_fractions),
            "H0_to_B": None,
            "A_to_B": None,
            "status": "A_COMPLETE_B_CORRECTLY_SKIPPED",
        },
        "accounting": {
            "h0_reused_results": 1,
            "a_cache_hits_before_action": 0,
            "a_read_only_history_scans": 3,
            "a_reservations": 1,
            "a_clicks": 1,
            "b_cache_hits_before_action": 0,
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
                "a_fractions": a_fractions,
                "b_submitted": False,
                "head": head,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
