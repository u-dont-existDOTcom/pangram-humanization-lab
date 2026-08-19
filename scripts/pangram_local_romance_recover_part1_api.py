#!/usr/bin/env python3
from __future__ import annotations

import json
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


def main() -> int:
    config = base.local_transport.LocalPlaywrightConfig.from_env()
    chromium_candidates = discover_pangram_history_urls(config.profile_dir, limit=40)
    print(
        "[pangram-local-api-recover] read-only exact history API binding enabled; "
        f"browser candidate count={len(chromium_candidates)} (private URLs not printed)",
        flush=True,
    )

    original_find = base._find_or_open_report
    last_exact_record: ExactHistoryRecord | None = None
    observed_history_records = 0
    comparison_diagnostics: list[dict[str, object]] = []

    def enhanced_find(
        context: Any,
        page: Any,
        exact_text: str,
    ) -> tuple[Any, str, dict[str, object]]:
        nonlocal last_exact_record, observed_history_records
        exact_records: list[ExactHistoryRecord] = []
        observed_uuids: set[str] = set()

        def collect(response: Any) -> None:
            nonlocal observed_history_records
            try:
                response_url = str(getattr(response, "url", ""))
                uuid = history_api_uuid(response_url)
                if uuid is None:
                    return
                headers = getattr(response, "headers", {}) or {}
                if "json" not in str(headers.get("content-type", "")).casefold():
                    return
                payload = response.json()
                if uuid not in observed_uuids:
                    observed_uuids.add(uuid)
                    observed_history_records += 1
                    summary = history_record_comparison_summary(payload, exact_text)
                    if summary.get("candidate_fields") and len(comparison_diagnostics) < 12:
                        comparison_diagnostics.append(
                            {
                                "record_index": observed_history_records,
                                **summary,
                            }
                        )
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
        try:
            # Visiting a stored report route issues GET /api/history/<uuid>/.
            # Revisit only existing candidates; this is read-only and cannot submit.
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

            # If browser history lacks the exact record, reuse the current
            # All Checks / History navigation solely to trigger stored-record
            # GETs while this exact API listener is attached.
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
                    "record_comparisons": comparison_diagnostics,
                    "comparison_privacy_note": (
                        "No Pangram record text, private result UUID, cookie, storage value, or private URL is logged. "
                        "Whitespace-collapsed equality is diagnostic only and cannot clear ambiguity."
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
