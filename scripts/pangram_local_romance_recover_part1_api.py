#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pangram_local_romance_recover_part1 as base
import pangram_local_romance_recover_part1_history as history_ui
from pangram_lab.browser_history_recovery import discover_pangram_history_urls
from pangram_lab.history_api_record import (
    ExactHistoryRecord,
    history_api_uuid,
    history_record_comparison_summary,
    match_exact_history_record,
    parse_history_record_result,
)
from pangram_lab.history_list_recovery import (
    HistoryListCandidate,
    extract_history_list_candidates,
    paid_reservation_time_from_ledger,
    rank_by_target_time,
)

HISTORY_LIST_URL = "https://web.pangram.com/api/history-list/"
MAX_PAID_TIME_DISTANCE_SECONDS = 15 * 60


def _materialize_record_report(
    context: Any,
    page: Any,
    record: ExactHistoryRecord,
) -> tuple[Any, str, dict[str, object]]:
    working = base.local_transport.normalize_context_tabs(context, keep=page)
    working.goto(record.report_url, wait_until="domcontentloaded")
    if hasattr(working, "wait_for_timeout"):
        working.wait_for_timeout(1_800)
    body = base.gui_core.clean_report_body_artifact(working.locator("body").inner_text())
    parsed = parse_history_record_result(record, body)
    return working, body, parsed


def _ledger_path() -> Path:
    return (
        base.repository_root()
        / "state"
        / "pangram-call-ledgers"
        / f"{base.AUDIT_ID}.json"
    )


def _history_record_url(candidate: HistoryListCandidate) -> str:
    return f"https://web.pangram.com/api/history/{candidate.uuid}/"


def _history_report_url(candidate: HistoryListCandidate) -> str:
    return f"https://www.pangram.com/history/{candidate.uuid}"


def _is_history_list_url(raw_url: str) -> bool:
    return str(raw_url).split("?", 1)[0].rstrip("/") == HISTORY_LIST_URL.rstrip("/")


def _safe_response_json(response: Any) -> Any | None:
    try:
        if int(getattr(response, "status", 0) or 0) != 200:
            return None
        headers = getattr(response, "headers", {}) or {}
        if "json" not in str(headers.get("content-type", "")).casefold():
            return None
        return response.json()
    except Exception:
        return None


def _read_history_list(context: Any) -> tuple[Any | None, str]:
    request = getattr(context, "request", None)
    getter = getattr(request, "get", None)
    if not callable(getter):
        return None, "context_request_unavailable"
    try:
        response = getter(HISTORY_LIST_URL, timeout=15_000)
    except Exception as exc:
        return None, f"request_failed:{type(exc).__name__}"
    payload = _safe_response_json(response)
    if payload is None:
        return None, f"non_json_or_non_200:{int(getattr(response, 'status', 0) or 0)}"
    return payload, "direct_context_request_ok"


def _read_history_record(context: Any, candidate: HistoryListCandidate) -> tuple[Any | None, str]:
    request = getattr(context, "request", None)
    getter = getattr(request, "get", None)
    if not callable(getter):
        return None, "context_request_unavailable"
    try:
        response = getter(_history_record_url(candidate), timeout=15_000)
    except Exception as exc:
        return None, f"request_failed:{type(exc).__name__}"
    payload = _safe_response_json(response)
    if payload is None:
        return None, f"non_json_or_non_200:{int(getattr(response, 'status', 0) or 0)}"
    return payload, "direct_context_request_ok"


def main() -> int:
    config = base.local_transport.LocalPlaywrightConfig.from_env()
    chromium_candidates = discover_pangram_history_urls(config.profile_dir, limit=40)
    paid_time = paid_reservation_time_from_ledger(
        _ledger_path(),
        measurement_key=f"gui:{base.EXPECTED_SHA}",
    )
    print(
        "[pangram-local-api-recover] read-only stored-history recovery enabled; "
        f"browser candidate count={len(chromium_candidates)}; paid-call timestamp binding enabled "
        "(private URLs/UUIDs not printed)",
        flush=True,
    )

    original_find = base._find_or_open_report
    last_exact_record: ExactHistoryRecord | None = None
    observed_history_records = 0
    comparison_diagnostics: list[dict[str, object]] = []
    temporal_diagnostics: list[dict[str, object]] = []
    history_list_status = "not_attempted"
    history_list_candidate_count = 0

    def enhanced_find(
        context: Any,
        page: Any,
        exact_text: str,
    ) -> tuple[Any, str, dict[str, object]]:
        nonlocal last_exact_record, observed_history_records
        nonlocal history_list_status, history_list_candidate_count
        exact_records: list[ExactHistoryRecord] = []
        observed_uuids: set[str] = set()
        captured_history_list_payload: Any | None = None
        temporal_labels: dict[str, dict[str, object]] = {}

        def record_comparison(
            payload: Any,
            *,
            label: dict[str, object] | None = None,
        ) -> None:
            summary = history_record_comparison_summary(payload, exact_text)
            if not summary.get("candidate_fields"):
                return
            if len(comparison_diagnostics) >= 12:
                return
            comparison_diagnostics.append(
                {
                    **(label or {}),
                    **summary,
                }
            )

        def collect(response: Any) -> None:
            nonlocal observed_history_records, captured_history_list_payload
            try:
                response_url = str(getattr(response, "url", ""))
                if _is_history_list_url(response_url):
                    payload = _safe_response_json(response)
                    if payload is not None:
                        captured_history_list_payload = payload
                    return
                uuid = history_api_uuid(response_url)
                if uuid is None:
                    return
                payload = _safe_response_json(response)
                if payload is None:
                    return
                if uuid not in observed_uuids:
                    observed_uuids.add(uuid)
                    observed_history_records += 1
                    label = temporal_labels.get(uuid) or {
                        "record_index": observed_history_records,
                        "source": "browser_navigation",
                    }
                    record_comparison(payload, label=label)
                match = match_exact_history_record(response_url, payload, exact_text)
                if match is None:
                    return
                if not any(existing.uuid == match.uuid for existing in exact_records):
                    exact_records.append(match)
            except Exception:
                return

        listener_attached = False
        try:
            on = getattr(context, "on", None)
            if callable(on):
                on("response", collect)
                listener_attached = True
        except Exception:
            listener_attached = False

        working = base.local_transport.normalize_context_tabs(context, keep=page)

        def try_timestamp_bound_payload(list_payload: Any) -> tuple[Any, str, dict[str, object]] | None:
            nonlocal last_exact_record, history_list_candidate_count
            ranked = rank_by_target_time(
                extract_history_list_candidates(list_payload),
                paid_time,
            )
            history_list_candidate_count = max(history_list_candidate_count, len(ranked))
            if not temporal_diagnostics:
                temporal_diagnostics.extend(
                    candidate.public_proof(paid_time)
                    for candidate in ranked[:8]
                )
            for candidate in ranked[:8]:
                distance = candidate.distance_seconds(paid_time)
                if distance > MAX_PAID_TIME_DISTANCE_SECONDS:
                    break
                proof = candidate.public_proof(paid_time)
                proof["source"] = "paid_time_bound_history"
                temporal_labels[candidate.uuid] = proof

                payload, record_status = _read_history_record(context, candidate)
                proof["direct_record_read_status"] = record_status
                if payload is not None:
                    response_url = _history_record_url(candidate)
                    match = match_exact_history_record(response_url, payload, exact_text)
                    if match is not None:
                        last_exact_record = match
                        proof["bounded_text_identity"] = True
                        return _materialize_record_report(context, working, match)
                    proof["bounded_text_identity"] = False
                    record_comparison(payload, label=proof)
                    continue

                # Some Pangram sessions authenticate API calls with headers added
                # by the SPA rather than cookies shared with BrowserContext.request.
                # In that case navigate the existing report page read-only and let
                # the normal application issue its authenticated history-record GET.
                try:
                    working.goto(_history_report_url(candidate), wait_until="domcontentloaded")
                    if hasattr(working, "wait_for_timeout"):
                        working.wait_for_timeout(1_500)
                except Exception:
                    continue
                for exact_record in exact_records:
                    if exact_record.uuid == candidate.uuid:
                        last_exact_record = exact_record
                        proof["bounded_text_identity"] = True
                        return _materialize_record_report(context, working, exact_record)
            return None

        try:
            # First try BrowserContext.request, which shares browser cookies.
            list_payload, history_list_status = _read_history_list(context)
            if list_payload is not None:
                recovered = try_timestamp_bound_payload(list_payload)
                if recovered is not None:
                    return recovered

            # If direct request authentication is unavailable, use the actual
            # hydrated GUI. The response listener above captures the SPA's own
            # authenticated /api/history-list/ response in memory.
            if list_payload is None or history_list_candidate_count == 0:
                try:
                    gui_recovered = history_ui._try_hydrated_dashboard_history(
                        context,
                        working,
                        exact_text,
                        set(),
                    )
                    if gui_recovered is not None:
                        return gui_recovered
                except Exception:
                    pass
                if captured_history_list_payload is not None:
                    history_list_status = "captured_from_authenticated_gui"
                    recovered = try_timestamp_bound_payload(captured_history_list_payload)
                    if recovered is not None:
                        return recovered

            # Existing browser-history candidates remain a read-only fallback, but
            # only an exact/bounded text match can clear ambiguity.
            for candidate in chromium_candidates:
                try:
                    working.goto(candidate, wait_until="domcontentloaded")
                    if hasattr(working, "wait_for_timeout"):
                        working.wait_for_timeout(1_000)
                except Exception:
                    continue
                if exact_records:
                    last_exact_record = exact_records[0]
                    return _materialize_record_report(context, working, last_exact_record)

            # If the GUI was not already used above, reuse current All Checks /
            # History navigation solely to trigger stored-record GETs while the
            # exact listener is attached.
            if captured_history_list_payload is None:
                try:
                    history_ui._try_hydrated_dashboard_history(
                        context,
                        working,
                        exact_text,
                        set(),
                    )
                except Exception:
                    pass
            if exact_records:
                last_exact_record = exact_records[0]
                return _materialize_record_report(context, working, last_exact_record)

            # Preserve the older exact-DOM recovery as a final no-submit fallback.
            recovered = original_find(context, working, exact_text)
            if exact_records:
                last_exact_record = exact_records[0]
                return _materialize_record_report(context, working, last_exact_record)
            return recovered
        finally:
            if listener_attached:
                try:
                    remove = getattr(context, "remove_listener", None)
                    if callable(remove):
                        remove("response", collect)
                except Exception:
                    pass

    base._find_or_open_report = enhanced_find
    try:
        receipt = base.recover()
        if last_exact_record is not None:
            receipt["history_api_exact_identity"] = last_exact_record.public_proof()
            receipt["paid_reservation_timestamp_utc"] = paid_time.isoformat().replace("+00:00", "Z")
        base._json(receipt)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "not_recovered",
                    "detector_submission_attempted_during_recovery": False,
                    "browser_candidate_count": len(chromium_candidates),
                    "history_api_records_observed": observed_history_records,
                    "exact_history_api_record_found": last_exact_record is not None,
                    "paid_reservation_timestamp_utc": paid_time.isoformat().replace("+00:00", "Z"),
                    "history_list_status": history_list_status,
                    "history_list_candidate_count": history_list_candidate_count,
                    "history_list_nearest_candidates": temporal_diagnostics,
                    "record_comparisons": comparison_diagnostics,
                    "comparison_privacy_note": (
                        "No Pangram record text, private result UUID, cookie, storage value, or private URL is logged. "
                        "Timestamp binding and bounded text identity are independent gates."
                    ),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            flush=True,
        )
        raise
    finally:
        base._find_or_open_report = original_find
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
