#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


FAMILY = Path(
    "state/experiments/somatic-r15-housemate-nextday-green-research-tail-20260831"
)
OUTPUT = FAMILY / "RESULT-PACKET.json"
H0_PACKET = Path(
    "state/experiments/somatic-r15-housemate-green-next-day-wake-tail-20260831/"
    "RESULT-PACKET.json"
)
H0_SHA = "85406d364a8b65adcac9ee0d14bf0bc2e8fe82c7399dbecf235bf5717e24d34b"
A_SHA = "c47bb1a7406c05c528463c3743fd62130a6f6c4758831a16323c7e4a6db7cfd7"
B_SHA = "22475e89b5bdedbd5de0dd69d566c8efd04329af2d87834a9b5cc5a0cb87dac1"
GUI_ROOT = Path("state/gui-runs/pangram-4")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} is not a JSON object")
    return value


def fractions(result: dict[str, Any]) -> dict[str, float]:
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


def a_window_metadata(localization: dict[str, Any]) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for shape in localization["unresolved_candidate_shapes"]:
        path = shape.get("field_path")
        if not (
            isinstance(path, list)
            and len(path) == 4
            and path[:3] == ["response", "in_page", "windows"]
        ):
            continue
        metadata = shape.get("scalar_metadata")
        if not isinstance(metadata, dict) or "window_index" not in metadata:
            continue
        windows.append(
            {
                **metadata,
                "text_persisted": False,
                "text_field_length": int(shape["text_field_lengths"]["text"]),
                "transport_binding": shape["reason"],
            }
        )
    windows.sort(key=lambda item: int(item["window_index"]))
    return windows


def main() -> int:
    h0_packet = read_json(H0_PACKET)
    h0 = h0_packet["variants"]["A"]
    a = read_json(GUI_ROOT / A_SHA / "result.json")
    b = read_json(GUI_ROOT / B_SHA / "result.json")
    a_localization = read_json(GUI_ROOT / A_SHA / "localization.json")
    b_localization = read_json(FAMILY / "B-EXACT-HISTORY-LOCALIZATION.json")
    a_result = a["parsed"]
    b_result = b["parsed"]
    h0_values = fractions(h0["result"])
    a_values = fractions(a_result)
    b_values = fractions(b_result)
    a_identity = a["history_api_exact_identity"]
    b_identity = b["history_api_exact_identity"]
    a_windows = a_window_metadata(a_localization)
    b_windows = b_localization["windows"]

    if not (
        h0["input_sha256"] == H0_SHA
        and h0["result"]["detector_version"] == "4.0"
        and h0["result"]["detector_stage"] == "STAGE_SUCCESS"
        and h0_values == {"human": 1.0, "ai": 0.0, "ai_assisted": 0.0}
        and h0["confidence"] == "High"
        and a["status"] == "complete"
        and a["input_sha256"] == A_SHA
        and a_result["detector_version"] == "4.0"
        and a_result["detector_stage"] == "STAGE_SUCCESS"
        and a_values
        == {"human": 0.6725773215, "ai": 0.3274226785, "ai_assisted": 0.0}
        and a_identity["authorized_text_sha256"] == A_SHA
        and a_identity["stored_text_sha256"] == A_SHA
        and a_identity["transport_match_mode"] == "exact_utf8"
        and a_localization["input_sha256"] == A_SHA
        and a_localization["detector_submission_attempted"] is False
        and [window["window_index"] for window in a_windows] == [0, 1, 2]
        and [(window["start_index"], window["end_index"]) for window in a_windows]
        == [(0, 224), (224, 1855), (1855, 2425)]
        and b["status"] == "complete"
        and b["input_sha256"] == B_SHA
        and b_result["detector_version"] == "4.0"
        and b_result["detector_stage"] == "STAGE_SUCCESS"
        and b_values
        == {"human": 0.7833614945, "ai": 0.2166385204, "ai_assisted": 0.0}
        and b_identity["authorized_text_sha256"] == B_SHA
        and b_identity["stored_text_sha256"] == B_SHA
        and b_identity["transport_match_mode"] == "exact_utf8"
        and b_localization["inputSha256"] == B_SHA
        and b_localization["inputWords"] == 418
        and b_localization["detectorSubmissionAttempted"] is False
        and b_localization["exactHistoryResultRecovered"] is True
        and b_localization["historyApi"]["paginationExhausted"] is True
        and b_localization["historyResultIdentity"] == b_identity
        and b_localization["result"] == b_result
        and [(window["start_index"], window["end_index"]) for window in b_windows]
        == [(0, 1855), (1855, 2368)]
    ):
        raise RuntimeError("housemate research result failed exact authority gates")

    serialized = json.dumps(
        {"a": a, "b": b, "a_localization": a_localization, "b_localization": b_localization}
    )
    if "https://www.pangram.com/history/" in serialized.replace(
        "https://www.pangram.com/history/<uuid>", ""
    ):
        raise RuntimeError("private History route present")

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    packet = {
        "format": "somatic-r15-housemate-research-result-v1",
        "directive_id": "SOMATIC-R15-SURFACE-011",
        "family": "somatic-r15-housemate-nextday-green-research-tail-20260831",
        "family_state": "CLOSED_A_AND_B_COMPLETE_BELOW_HUMAN_1_0",
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "model": "pangram-4",
            "required_version": "4.0",
            "starting_head": "d0a56ae76cd57ee29b5e091c18144e31d8b310ec",
            "after_measurements_before_packet": head,
        },
        "article_authority": {
            "branch": "task/somatic-r15-clean-continuation-20260830",
            "packet_head": "f999e40c5d53c6283ec638d89788726561b0cd9c",
            "candidate_sha256": "1e08284ce544b851b516eebdf38f3f8efb2497e477a0104270880f49aab7d81e",
            "registered_master_sha256": "1e7e94717f40e7a4de77974a896f600a1bf2769d9c1846cbe84275e136ff5202",
        },
        "variants": {
            "H0": {
                "classification": "EXACT_COMPLETED_RESULT_REUSE_ONLY",
                "input_sha256": H0_SHA,
                "input_identity": {
                    "whitespace_words": 344,
                    "unicode_characters": 1923,
                    "utf8_bytes": 1923,
                    "terminal_newline": False,
                },
                "result": h0["result"],
                "confidence": h0["confidence"],
                "result_authority_commit": "d0a56ae76cd57ee29b5e091c18144e31d8b310ec",
            },
            "A": {
                "classification_before_action": "EXACT_GUI_NEVER_SUBMITTED",
                "classification": "EXACT_GUI_RESULT_EXISTS",
                "input_sha256": A_SHA,
                "input_identity": {
                    "whitespace_words": 429,
                    "unicode_characters": 2434,
                    "utf8_bytes": 2434,
                    "terminal_newline": False,
                },
                "detector_submission_attempted": True,
                "captured_at_utc": a["captured_at_utc"],
                "prediction": a_identity["record_prediction"],
                "prediction_short": a_result["prediction_short"],
                "headline": a_result["headline"],
                "history_api_exact_identity": a_identity,
                "result": a_result,
                "window_metadata": a_windows,
                "localization": {
                    "status": a_localization["status"],
                    "localized_span_count": a_localization["localized_span_count"],
                    "localized_spans": a_localization["spans"],
                    "all_window_offsets_recovered": True,
                    "full_window_text_persisted": False,
                    "detector_submission_attempted": False,
                },
                "report_body_sha256": a["report_body_sha256"],
                "report_pdf_sha256": a["report_pdf_sha256"],
                "reservation": a["submission_reservation"],
            },
            "B": {
                "classification_before_action": "EXACT_GUI_NEVER_SUBMITTED",
                "classification": "EXACT_GUI_RESULT_EXISTS",
                "input_sha256": B_SHA,
                "input_identity": {
                    "whitespace_words": 418,
                    "unicode_characters": 2377,
                    "utf8_bytes": 2377,
                    "terminal_newline": False,
                },
                "detector_submission_attempted": True,
                "captured_at_utc": b["captured_at_utc"],
                "prediction": b_identity["record_prediction"],
                "prediction_short": b_result["prediction_short"],
                "headline": b_result["headline"],
                "history_api_exact_identity": b_identity,
                "result": b_result,
                "windows": b_windows,
                "read_only_exhaustive_history_localization": {
                    "started_at": b_localization["startedAt"],
                    "completed_at": b_localization["completedAt"],
                    "pages_scanned": b_localization["historyApi"]["pagesScanned"],
                    "candidates_scanned": b_localization["historyApi"]["candidatesScanned"],
                    "detail_records_inspected": b_localization["historyApi"]["detailRecordsInspected"],
                    "pagination_exhausted": True,
                    "exact_result_recovered": True,
                    "detector_submission_attempted": False,
                },
                "report_body_sha256": b["report_body_sha256"],
                "report_pdf_sha256": b["report_pdf_sha256"],
                "reservation": b["submission_reservation"],
            },
        },
        "fraction_table": {"H0": h0_values, "A": a_values, "B": b_values},
        "deltas": {
            "H0_to_A": delta(a_values, h0_values),
            "H0_to_B": delta(b_values, h0_values),
            "A_to_B": delta(b_values, a_values),
            "status": "A_AND_B_COMPLETE_BELOW_HUMAN_1_0",
        },
        "accounting": {
            "h0_reused_results": 1,
            "a_cache_hits_before_action": 0,
            "a_recent_history_candidates_inspected_before_action": 10,
            "a_reservations": 1,
            "a_clicks": 1,
            "a_read_only_localizations": 1,
            "b_cache_hits_before_action": 0,
            "b_recent_history_candidates_inspected_before_action": 10,
            "b_reservations": 1,
            "b_clicks": 1,
            "b_read_only_short_history_localization_attempts": 2,
            "b_read_only_exhaustive_history_scans": 1,
            "new_api_calls": 0,
            "new_short_gui_clicks": 2,
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
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
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
                "b_fractions": b_values,
                "head": head,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
