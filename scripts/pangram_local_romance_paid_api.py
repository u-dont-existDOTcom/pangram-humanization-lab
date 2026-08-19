#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import pangram_local_romance_paid as base
from pangram_lab.history_api_record import (
    ExactHistoryRecord,
    history_api_uuid,
    match_exact_history_record,
    parse_history_record_result,
)


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), flush=True)


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


def _record_listener(exact_text: str, records: list[ExactHistoryRecord]):
    def collect(response: Any) -> None:
        try:
            if history_api_uuid(str(getattr(response, "url", ""))) is None:
                return
            headers = getattr(response, "headers", {}) or {}
            if "json" not in str(headers.get("content-type", "")).casefold():
                return
            payload = response.json()
            match = match_exact_history_record(response.url, payload, exact_text)
            if match is None:
                return
            if not any(existing.uuid == match.uuid for existing in records):
                records.append(match)
        except Exception:
            return

    return collect


def _wait_for_exact_record(
    context: Any,
    page: Any,
    records: list[ExactHistoryRecord],
    *,
    timeout_ms: int,
) -> ExactHistoryRecord:
    deadline = time.monotonic() + timeout_ms / 1000.0
    retried_open_pages = False
    while True:
        if records:
            return records[0]
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(
                "Pangram submission produced no exact-matching stored history API record before timeout"
            )

        # Once a report route appears, revisiting it is a read-only way to make
        # Pangram re-issue GET /api/history/<uuid>/ if the original response was
        # missed by browser timing. Do this at most once per open report page.
        if not retried_open_pages:
            report_pages = []
            for candidate in tuple(getattr(context, "pages", ())):
                try:
                    if "/history/" in str(getattr(candidate, "url", "")):
                        report_pages.append(candidate)
                except Exception:
                    continue
            if report_pages:
                retried_open_pages = True
                for candidate in report_pages:
                    try:
                        candidate.reload(wait_until="domcontentloaded")
                        if hasattr(candidate, "wait_for_timeout"):
                            candidate.wait_for_timeout(800)
                    except Exception:
                        continue
                    if records:
                        return records[0]

        sleep_ms = min(500, max(1, int(remaining * 1000)))
        pages = tuple(getattr(context, "pages", ()))
        waiter = pages[-1] if pages else page
        if hasattr(waiter, "wait_for_timeout"):
            waiter.wait_for_timeout(sleep_ms)
        else:
            time.sleep(sleep_ms / 1000.0)


def execute() -> dict[str, object]:
    repo_root = base.repository_root()
    output_root = base._resolve_output_root(repo_root, base.DEFAULT_OUTPUT_ROOT)
    prepared = base.materialize_current_romance_inputs(repo_root, no_fetch=False)
    digests = base._input_digests(prepared.paths, prepared.expected_sha256)
    durability = base.GitEvidenceDurability(repo_root, output_root)
    durability.preflight(digests)

    config = base.local_transport.LocalPlaywrightConfig.from_env()
    base.local_transport.verify_login_persistence(config)

    ledger = base.PangramCallLedger(repo_root, base.AUDIT_ID)
    pre_status = base._status_receipt(prepared, output_root, ledger)
    expected = prepared.expected_sha256 or {}
    pending: list[tuple[Path, dict[str, object], int, str, str]] = []
    results: list[dict[str, object]] = []

    for path in prepared.paths:
        digest = expected.get(str(path)) or expected.get(path.name)
        if digest is None:
            raise RuntimeError(f"missing exact SHA gate for {path}")
        item = base._prepared_item(path, output_root, digest)
        number, section_id = base._section_for(path)
        if item["skip"]:
            results.append(
                {
                    "status": "cached",
                    "part": number,
                    "section_id": section_id,
                    "input_sha256": digest,
                    "word_count": int(item["word_count"]),
                }
            )
            continue
        pending.append((path, item, number, section_id, digest))

    if not pending:
        return {
            "status": "all_cached",
            "audit_id": base.AUDIT_ID,
            "source": prepared.source_receipt,
            "preflight": pre_status,
            "results": results,
            "call_accounting": ledger.audit_summary(),
        }

    git = base.GitSync(repo_root, require_remote=True)
    playwright, context, page = base.local_transport._launch_persistent_context(config)
    try:
        for path, item, number, section_id, digest in pending:
            directory = Path(str(item["directory"]))
            paths = base.gui_core.artifact_paths(directory)
            directory.mkdir(parents=True, exist_ok=True)
            source = base._source_for(prepared.source_metadata, path)
            stage = "navigate"
            detector_submission_attempted = False
            measurement_key = f"gui:{digest}"
            call_summary: dict[str, object] | None = None
            report_page = page
            exact_records: list[ExactHistoryRecord] = []
            listener = _record_listener(str(item["text"]), exact_records)
            listener_attached = False
            try:
                page.goto(config.pangram_url, wait_until="domcontentloaded")
                stage = "verify_authentication"
                field = base.local_transport.wait_for_authenticated_detector_input(page)
                stage = "fill_input"
                field.fill(str(item["text"]))
                stage = "locate_detector_action"
                button = base.gui_core.detection_button(page)

                stage = "reserve_paid_call"
                try:
                    call_summary = ledger.reserve_paid_call(
                        section_id=section_id,
                        model=base.gui_core.MODEL_ID,
                        version=base.EXPECTED_VERSION,
                        measurement_key=measurement_key,
                        text_sha256=digest,
                        word_count=int(item["word_count"]),
                    )
                except base.SectionCallCapReached:
                    handoff = ledger.write_handoff(
                        section_id,
                        base.gui_core.MODEL_ID,
                        base.EXPECTED_VERSION,
                        results,
                    )
                    git.sync_paths(
                        [ledger.path, handoff],
                        f"pangram local call-cap handoff {base.AUDIT_ID} {section_id}",
                    )
                    raise

                git.sync_paths(
                    [ledger.path],
                    f"reserve Pangram paid call {base.AUDIT_ID} {section_id} {digest[:16]}",
                )

                # Attach exact stored-record capture before the paid click.
                on = getattr(context, "on", None)
                if callable(on):
                    on("response", listener)
                    listener_attached = True

                stage = "submit"
                detector_submission_attempted = True
                button.click()
                print(
                    f"[pangram-local-paid-api] submitted part={number} sha={digest}; waiting for exact stored record",
                    flush=True,
                )

                stage = "wait_exact_history_record"
                record = _wait_for_exact_record(
                    context,
                    page,
                    exact_records,
                    timeout_ms=180_000,
                )
                if record.input_sha256 != digest or record.word_count != int(item["word_count"]):
                    raise RuntimeError("stored Pangram history record failed exact source identity gate")

                stage = "capture_body"
                report_page, body, parsed = _materialize_record_report(context, page, record)
                paths["body"].write_text(body, encoding="utf-8")

                stage = "capture_pdf"
                pdf_provenance = base.local_transport.capture_report_pdf(report_page, paths["pdf"])
                receipt = base.local_core.build_complete_receipt(
                    config,
                    item=item,
                    report_url=report_page.url,
                    pdf_provenance=pdf_provenance,
                    parsed=parsed,
                    body=body,
                    pdf_path=paths["pdf"],
                    source=source,
                )
                receipt.update(
                    {
                        "audit_id": base.AUDIT_ID,
                        "section_id": section_id,
                        "measurement_key": measurement_key,
                        "call_accounting": call_summary,
                        "history_api_exact_identity": record.public_proof(),
                    }
                )
                base.local_core._write_json(paths["result"], receipt)
                base.local_core._remove_stale_failures(directory, paths)
                stage = "persist_evidence"
                durability(directory, receipt)
                results.append(receipt)
                print(
                    f"[pangram-local-paid-api] complete part={number} sha={digest} pdf={pdf_provenance}",
                    flush=True,
                )
                page = base.local_transport.normalize_context_tabs(context, keep=report_page)
            except Exception as exc:
                if stage == "persist_evidence":
                    raise
                failure = base.local_core.build_failure_receipt(
                    config,
                    item=item,
                    stage=stage,
                    detector_submission_attempted=detector_submission_attempted,
                    error=exc,
                    source=source,
                )
                failure.update(
                    {
                        "audit_id": base.AUDIT_ID,
                        "section_id": section_id,
                        "measurement_key": measurement_key,
                        "call_accounting": call_summary
                        or ledger.section_summary(
                            section_id,
                            base.gui_core.MODEL_ID,
                            base.EXPECTED_VERSION,
                        ),
                        "exact_history_api_record_found": bool(exact_records),
                    }
                )
                base.local_core._write_json(paths["failure"], failure)
                try:
                    report_page.screenshot(path=str(paths["failure_screenshot"]), full_page=True)
                except Exception:
                    pass
                try:
                    durability(directory, failure)
                except Exception as durability_error:
                    raise RuntimeError(
                        "Pangram paid run failed and saved failure evidence could not be pushed durably: "
                        f"run_error={exc}; durability_error={durability_error}"
                    ) from durability_error
                raise
            finally:
                if listener_attached:
                    try:
                        remove = getattr(context, "remove_listener", None)
                        if callable(remove):
                            remove("response", listener)
                    except Exception:
                        pass
    finally:
        base.local_transport._close_local_session(playwright, context)

    return {
        "status": "complete",
        "audit_id": base.AUDIT_ID,
        "source": prepared.source_receipt,
        "preflight": pre_status,
        "results": results,
        "call_accounting": ledger.audit_summary(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Budgeted Romance Pangram GUI run with exact stored-history-record binding."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    result = base.preflight() if args.preflight_only else execute()
    _json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
