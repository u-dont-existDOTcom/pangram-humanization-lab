#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SHA = "b36e1e46c06d764a080d407dce5412defe76ccb9202deb1a8a14e265acf40370"
FAILURE_TIME = "2026-08-31T04:07:24.622478Z"
SCAN_ROOT = Path("state/recovery/somatic-r15-shaking-c-ambiguity-20260831")
SCAN_ONE = SCAN_ROOT / "scan-01-exhaustive-detail.json"
SCAN_TWO = SCAN_ROOT / "scan-02-exhaustive-detail.json"
ORIGINAL_RUN = Path("state/gui-runs/pangram-4") / SHA
RESULT_PATH = ORIGINAL_RUN / "result.json"
EXPECTED_ARTIFACTS = {
    "failure.json": "b7520674a9263dac4d03dac06de7ba9533013aadc9c6f34e81273cc1238db3f4",
    "failure.png": "192c5257225e853a51e83981c108cc785b6d44d0b3053815af13051d6f0c677d",
    "reservation.json": "ab293bad9dbc43b46235cd9a1b77714869440964683b4a9ea2a12bf204d0d713",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} is not a JSON object")
    return value


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_scan(scan: dict[str, Any]) -> None:
    history = scan["historyApi"]
    result = scan["result"]
    summary = result["summary"]
    identity = scan["historyResultIdentity"]
    if not (
        scan["inputSha256"] == SHA
        and scan["detectorSubmissionAttempted"] is False
        and scan["exactHistoryResultRecovered"] is True
        and scan["providerOrTaskIdentityRecovered"] is True
        and history["paginationExhausted"] is True
        and history["pagesScanned"] >= 27
        and history["candidatesScanned"] >= 270
        and history["detailRecordsInspected"] == history["candidatesScanned"]
        and result["detector_stage"] == "STAGE_SUCCESS"
        and result["detector_version"] == "4.0"
        and result["headline"] == "Human Written"
        and summary["fraction_human"] == 1.0
        and summary["fraction_ai"] == 0.0
        and summary["fraction_ai_assisted"] == 0.0
        and identity["authorized_text_sha256"] == SHA
        and identity["stored_text_sha256"] == SHA
        and identity["transport_match_mode"] == "exact_utf8"
        and identity["api_path"] == "/api/history/<uuid>/"
    ):
        raise RuntimeError(f"scan {scan.get('scanId')} failed exact recovery gates")


def main() -> int:
    if RESULT_PATH.exists():
        raise RuntimeError("refusing to overwrite an existing C result")
    for name, expected in EXPECTED_ARTIFACTS.items():
        path = ORIGINAL_RUN / name
        if not path.is_file() or file_sha(path) != expected:
            raise RuntimeError(f"original C artifact changed: {name}")
    first = read_json(SCAN_ONE)
    second = read_json(SCAN_TWO)
    validate_scan(first)
    validate_scan(second)
    first_completed = parse_time(first["completedAt"])
    second_started = parse_time(second["startedAt"])
    second_completed = parse_time(second["completedAt"])
    failure = parse_time(FAILURE_TIME)
    if (second_started - first_completed).total_seconds() < 600:
        raise RuntimeError("second exhaustive scan started less than 10 minutes later")
    if (second_completed - failure).total_seconds() < 1800:
        raise RuntimeError("final exhaustive scan completed before the 30-minute gate")
    if first["result"] != second["result"]:
        raise RuntimeError("recovered C result changed between scans")
    if first["historyResultIdentity"] != second["historyResultIdentity"]:
        raise RuntimeError("recovered C History identity changed between scans")

    receipt = {
        "schema_version": 1,
        "status": "complete",
        "transport": "local_playwright",
        "transport_runner_version": "pangram-gui-local-playwright-v1",
        "model": "pangram-4",
        "detector_version": "4.0",
        "captured_at_utc": second["completedAt"],
        "input_path": "state/experiments/somatic-r15-shaking-human-anchor-guidance-social-tail-20260831/inputs/C-current-anchor.txt",
        "input_sha256": SHA,
        "word_count": 293,
        "evidence_source": "recovered_existing_report_after_ambiguous_gui_action",
        "detector_submission_attempted": False,
        "classification": "EXACT_GUI_RESULT_EXISTS_RECOVERED_AFTER_AMBIGUITY",
        "history_api_exact_identity": second["historyResultIdentity"],
        "parsed": second["result"],
        "windows": second["windows"],
        "recovery_scans": [
            {
                "scanId": first["scanId"],
                "startedAt": first["startedAt"],
                "completedAt": first["completedAt"],
                "pagesScanned": first["historyApi"]["pagesScanned"],
                "candidatesScanned": first["historyApi"]["candidatesScanned"],
                "detailRecordsInspected": first["historyApi"]["detailRecordsInspected"],
            },
            {
                "scanId": second["scanId"],
                "startedAt": second["startedAt"],
                "completedAt": second["completedAt"],
                "pagesScanned": second["historyApi"]["pagesScanned"],
                "candidatesScanned": second["historyApi"]["candidatesScanned"],
                "detailRecordsInspected": second["historyApi"]["detailRecordsInspected"],
            },
        ],
        "original_run_artifacts": [
            {"name": name, "sha256": digest}
            for name, digest in sorted(EXPECTED_ARTIFACTS.items())
        ],
        "failure_screenshot_observation": {
            "artifact_sha256": EXPECTED_ARTIFACTS["failure.png"],
            "exact_C_text_visible": True,
            "visible_detector": "Pangram 4.0",
            "visible_headline": "Human Written",
            "visible_human_percent": 100,
            "authority": "corroborating_visible_state_only; exact History binding above is result authority",
        },
        "private_history_route_persisted": False,
        "new_c_clicks": 0,
        "force_overrides": 0,
    }
    RESULT_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "classification": receipt["classification"],
                "result_path": str(RESULT_PATH),
                "fraction_human": receipt["parsed"]["summary"]["fraction_human"],
                "final_scan_completed_at": second["completedAt"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
