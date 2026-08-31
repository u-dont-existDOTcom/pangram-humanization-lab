#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from pangram_lab import gui_local as local
from pangram_lab.history_api_record import (
    exact_text_proof,
    history_record_comparison_summary,
    match_exact_history_record,
    parse_history_record_result,
)


HISTORY_LIST_URL = "https://web.pangram.com/api/history-list/"
HISTORY_API_TEMPLATE = "https://web.pangram.com/api/history/{uuid}/"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def safe_json_get(context: Any, url: str) -> tuple[Any | None, str, int]:
    attempts = 0
    while attempts < 8:
        attempts += 1
        try:
            response = context.request.get(url, timeout=15_000)
            status = int(response.status)
            if status == 429:
                time.sleep(min(20.0, 1.5 * attempts))
                continue
            if status != 200:
                return None, f"http_status:{status}", attempts
            content_type = str((response.headers or {}).get("content-type", ""))
            if "json" not in content_type.casefold():
                return None, "non_json_response", attempts
            return response.json(), "ok", attempts
        except Exception as exc:
            if attempts >= 8:
                return None, f"request_failed:{type(exc).__name__}", attempts
            time.sleep(min(10.0, float(attempts)))
    return None, "retry_exhausted", attempts


def valid_next_url(value: Any) -> str | None:
    if value is None:
        return None
    parsed = urlsplit(str(value))
    if (
        parsed.scheme == "https"
        and parsed.netloc.casefold() == "web.pangram.com"
        and parsed.path.rstrip("/") == "/api/history-list"
    ):
        return str(value)
    raise RuntimeError("History pagination returned an untrusted next URL")


def url_class(raw: str) -> str:
    parsed = urlsplit(raw)
    if parsed.scheme == "about":
        return "ABOUT_BLANK_OR_INTERNAL"
    if parsed.netloc.casefold() in {"pangram.com", "www.pangram.com"}:
        if parsed.path.startswith("/history/"):
            return "PANGRAM_HISTORY_REPORT"
        if parsed.path.rstrip("/") == "/history":
            return "PANGRAM_HISTORY_LIST"
        return "PANGRAM_DETECTOR_OR_APP"
    return "OTHER_OR_EMPTY"


def tab_state(page: Any, exact_text: str) -> dict[str, Any]:
    try:
        title = str(page.title())[:200]
    except Exception:
        title = ""
    try:
        body = str(page.locator("body").inner_text())
    except Exception:
        body = ""
    folded = " ".join(body.casefold().split())
    states = [
        name
        for name, pattern in (
            ("HUMAN_WRITTEN_VISIBLE", "human written"),
            ("AI_GENERATED_VISIBLE", "ai-generated"),
            ("INSUFFICIENT_CREDIT_VISIBLE", "insufficient credit"),
            ("ERROR_VISIBLE", "error"),
            ("PROCESSING_VISIBLE", "processing"),
        )
        if pattern in folded
    ]
    button_state = "NOT_FOUND"
    try:
        button = local.gui_core.detection_button(page)
        button_state = "VISIBLE_ENABLED" if button.is_enabled() else "VISIBLE_DISABLED"
    except Exception:
        pass
    return {
        "urlClass": url_class(str(getattr(page, "url", ""))),
        "title": title,
        "visibleStateMarkers": states,
        "detectorButtonState": button_state,
        "exactInputPresent": exact_text in body,
    }


def decoded_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None
    try:
        decoded = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return decoded if isinstance(decoded, dict) else None


def safe_windows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    response = decoded_object(payload.get("response")) or {}
    overall = decoded_object(response.get("overall")) or {}
    windows = overall.get("windows") or []
    allowed = {
        "text",
        "label",
        "confidence",
        "start_index",
        "end_index",
        "word_count",
        "token_length",
        "ai_assistance_score",
        "humanizer_score",
        "is_humanized",
    }
    return [
        {key: value for key, value in window.items() if key in allowed}
        for window in windows
        if isinstance(window, dict)
    ]


def artifact_manifest(directory: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted(candidate for candidate in directory.iterdir() if candidate.is_file()):
        raw = path.read_bytes()
        result.append({"name": path.name, "utf8Bytes": len(raw), "sha256": sha256(raw)})
    return result


def dedicated_browser_process_present() -> bool:
    completed = subprocess.run(
        ["pgrep", "-af", "--user-data-dir=.*/pangram-local-browser"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0 and bool(completed.stdout.strip())


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--input", type=Path, required=True)
    value.add_argument("--expect-sha", required=True)
    value.add_argument("--reservation-time", required=True)
    value.add_argument("--failure-time", required=True)
    value.add_argument("--scan-id", required=True)
    value.add_argument("--output", type=Path, required=True)
    value.add_argument("--original-run-dir", type=Path, required=True)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    expected_sha = str(args.expect_sha).lower()
    if not HEX64.fullmatch(expected_sha):
        raise RuntimeError("--expect-sha must be lowercase SHA-256")
    raw = args.input.read_bytes()
    text = raw.decode("utf-8")
    if sha256(raw) != expected_sha:
        raise RuntimeError("exact C input hash mismatch")
    if len(text.split()) != 293 or len(text) != 1631 or len(raw) != 1641 or text.endswith("\n"):
        raise RuntimeError("exact C input count mismatch")
    reservation_time = parse_time(args.reservation_time)
    failure_time = parse_time(args.failure_time)
    started = utc_now()
    process_before = dedicated_browser_process_present()
    original_artifacts = artifact_manifest(args.original_run_dir.resolve())

    config = local.LocalPlaywrightConfig.from_env()
    playwright = context = page = None
    restored: list[dict[str, Any]] = []
    page_statuses: dict[str, int] = {}
    pages_scanned = 0
    candidates_scanned = 0
    candidates_at_or_after_reservation = 0
    list_rows_with_exact_binding = 0
    near_matches: list[dict[str, Any]] = []
    ui_scroll_iterations = 0
    ui_history_links_observed = 0
    exact_record = None
    exact_result = None
    windows: list[dict[str, Any]] = []
    detail_status = None
    list_retry_attempts = 0
    page_counts: list[int] = []
    seen_urls: set[str] = set()
    seen_record_ids: set[str] = set()
    record_rows: list[dict[str, Any]] = []
    detail_records_inspected = 0
    detail_status_counts: dict[str, int] = {}
    try:
        playwright, context, page = local._launch_persistent_context(
            config, normalize_tabs=False
        )
        restored = [tab_state(candidate, text) for candidate in tuple(context.pages)]
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        local.wait_for_authenticated_detector_input(page)

        page.goto("https://www.pangram.com/history", wait_until="domcontentloaded")
        page.wait_for_timeout(1_800)
        stable = 0
        last_shape = None
        for _ in range(120):
            ui_scroll_iterations += 1
            try:
                links = page.locator('a[href^="/history/"]')
                link_count = int(links.count())
            except Exception:
                link_count = 0
            ui_history_links_observed = max(ui_history_links_observed, link_count)
            height = int(page.evaluate("document.documentElement.scrollHeight"))
            shape = (height, link_count)
            if shape == last_shape:
                stable += 1
            else:
                stable = 0
            last_shape = shape
            clicked = False
            for label in ("Load more", "Show more", "Next"):
                try:
                    button = page.get_by_role("button", name=label, exact=True)
                    if button.count() and button.first.is_visible() and button.first.is_enabled():
                        button.first.click()
                        clicked = True
                        break
                except Exception:
                    continue
            page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
            page.wait_for_timeout(500)
            if stable >= 4 and not clicked:
                break

        next_url: str | None = HISTORY_LIST_URL
        while next_url is not None:
            if next_url in seen_urls:
                raise RuntimeError("History pagination loop detected")
            seen_urls.add(next_url)
            payload, status, attempts = safe_json_get(context, next_url)
            list_retry_attempts += attempts
            page_statuses[status] = page_statuses.get(status, 0) + 1
            if not isinstance(payload, dict):
                raise RuntimeError(f"History pagination failed: {status}")
            rows = payload.get("results") or []
            if not isinstance(rows, list):
                raise RuntimeError("History pagination results are not a list")
            pages_scanned += 1
            page_counts.append(len(rows))
            for row_index, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                candidates_scanned += 1
                record_id = str(row.get("uuid") or "").strip().lower()
                if record_id:
                    seen_record_ids.add(record_id)
                    record_rows.append(
                        {
                            "uuid": record_id,
                            "page": pages_scanned,
                            "row": row_index,
                            "timestamp": row.get("timestamp"),
                        }
                    )
                try:
                    timestamp = parse_time(str(row.get("timestamp")))
                    if timestamp >= reservation_time:
                        candidates_at_or_after_reservation += 1
                except Exception:
                    pass
                proof = exact_text_proof(row, text)
                if proof is not None:
                    list_rows_with_exact_binding += 1
                elif len(near_matches) < 12:
                    comparison = history_record_comparison_summary(row, text, limit=4)
                    if comparison["candidate_fields"]:
                        near_matches.append(
                            {
                                "page": pages_scanned,
                                "row": row_index,
                                "comparison": comparison,
                            }
                        )
            next_url = valid_next_url(payload.get("next"))
            time.sleep(0.45)

        # History-list prompts may be truncated previews. Inspect every
        # available detail record read-only so pagination exhaustion is not
        # mistaken for complete record recovery.
        for record_row in record_rows:
            detail_url = HISTORY_API_TEMPLATE.format(uuid=record_row["uuid"])
            detail, status, attempts = safe_json_get(context, detail_url)
            list_retry_attempts += attempts
            detail_status_counts[status] = detail_status_counts.get(status, 0) + 1
            if not isinstance(detail, dict):
                time.sleep(0.5)
                continue
            detail_records_inspected += 1
            match = match_exact_history_record(detail_url, detail, text)
            if match is not None and exact_record is None:
                exact_record = match
                exact_result = parse_history_record_result(exact_record, "")
                windows = safe_windows(exact_record.payload)
                detail_status = status
            elif len(near_matches) < 12:
                comparison = history_record_comparison_summary(detail, text, limit=4)
                if comparison["candidate_fields"]:
                    near_matches.append(
                        {
                            "page": record_row["page"],
                            "row": record_row["row"],
                            "comparison": comparison,
                        }
                    )
            time.sleep(0.5)

        completed = utc_now()
        result_valid = False
        public_identity = None
        if exact_record is not None and exact_result is not None:
            summary = exact_result.get("summary") or {}
            result_valid = (
                exact_result.get("detector_stage") == "STAGE_SUCCESS"
                and exact_result.get("detector_version") == "4.0"
                and all(
                    isinstance(summary.get(key), (int, float))
                    for key in ("fraction_human", "fraction_ai", "fraction_ai_assisted")
                )
            )
            public_identity = exact_record.public_proof()
        receipt = {
            "schemaVersion": 1,
            "scanId": args.scan_id,
            "startedAt": started,
            "completedAt": completed,
            "reservationTime": args.reservation_time,
            "failureTime": args.failure_time,
            "minutesAfterFailure": round(
                (parse_time(completed) - failure_time).total_seconds() / 60.0, 3
            ),
            "inputSha256": expected_sha,
            "inputWords": 293,
            "detectorSubmissionAttempted": False,
            "dedicatedBrowserProcessPresentBeforeLaunch": process_before,
            "restoredTabStateBeforeNavigation": restored,
            "historyUi": {
                "scrollIterations": ui_scroll_iterations,
                "historyLinksObserved": ui_history_links_observed,
                "exhaustionRule": "four_stable_scroll_shapes_without_load_button",
            },
            "historyApi": {
                "pagesScanned": pages_scanned,
                "pageResultCounts": page_counts,
                "candidatesScanned": candidates_scanned,
                "uniqueRecordIdentitiesObserved": len(seen_record_ids),
                "detailRecordsInspected": detail_records_inspected,
                "detailReadStatusCounts": detail_status_counts,
                "candidatesAtOrAfterReservation": candidates_at_or_after_reservation,
                "listRowsWithExactBinding": list_rows_with_exact_binding,
                "requestStatusCounts": page_statuses,
                "requestAttempts": list_retry_attempts,
                "paginationExhausted": next_url is None,
                "reportedTotalCount": candidates_scanned,
            },
            "nearMatchDiagnostics": near_matches,
            "providerOrTaskIdentityRecovered": public_identity is not None,
            "exactHistoryResultRecovered": result_valid,
            "historyResultIdentity": public_identity,
            "result": exact_result if result_valid else None,
            "windows": windows if result_valid else [],
            "detailReadStatus": detail_status,
            "originalRunArtifacts": original_artifacts,
            "applicationMetadataInspection": "NOT_EXPORTED_NO_SUPPORTED_PRIVACY_SAFE_METADATA_SURFACE",
            "privacyNote": "No UUID, private report URL, cookie, storage value, authorization header, unrelated prompt, or raw response is persisted.",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "scanId": args.scan_id,
                    "completedAt": completed,
                    "minutesAfterFailure": receipt["minutesAfterFailure"],
                    "pagesScanned": pages_scanned,
                    "candidatesScanned": candidates_scanned,
                    "candidatesAtOrAfterReservation": candidates_at_or_after_reservation,
                    "exactHistoryResultRecovered": result_valid,
                    "output": str(args.output),
                    "detectorSubmissionAttempted": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if result_valid else 2
    finally:
        if playwright is not None and context is not None:
            local._close_local_session(playwright, context)


if __name__ == "__main__":
    raise SystemExit(main())
