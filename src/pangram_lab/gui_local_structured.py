from __future__ import annotations

import json
import re
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from pangram_lab import gui_local as local
from pangram_lab.history_api_record import (
    ExactHistoryRecord,
    history_api_uuid,
    match_exact_history_record,
    parse_history_record_result,
)
from pangram_lab.history_list_recovery import (
    HistoryListCandidate,
    extract_history_list_candidates,
)


_HISTORY_LIST_URL = "https://web.pangram.com/api/history-list/"
_HISTORY_REPORT_RE = re.compile(
    r"^https://www\.pangram\.com/history/"
    r"(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/?(?:[?#].*)?$"
)
_RESERVATION_NAME = "submission-reservation.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _response_content_type(response: Any) -> str:
    try:
        headers = getattr(response, "headers", {}) or {}
        return str(headers.get("content-type", ""))
    except Exception:
        return ""


def _record_listener(exact_text: str, records: list[ExactHistoryRecord]):
    def collect(response: Any) -> None:
        try:
            url = str(getattr(response, "url", ""))
            if history_api_uuid(url) is None:
                return
            if "json" not in _response_content_type(response).casefold():
                return
            match = match_exact_history_record(url, response.json(), exact_text)
            if match is not None and not any(existing.uuid == match.uuid for existing in records):
                records.append(match)
        except Exception:
            return

    return collect


def _history_list_listener(candidates: list[HistoryListCandidate]):
    def collect(response: Any) -> None:
        try:
            url = str(getattr(response, "url", ""))
            if url.split("?", 1)[0].rstrip("/") != _HISTORY_LIST_URL.rstrip("/"):
                return
            if "json" not in _response_content_type(response).casefold():
                return
            observed = extract_history_list_candidates(response.json())
            seen = {(item.uuid, item.created_at_utc) for item in candidates}
            for item in observed:
                identity = (item.uuid, item.created_at_utc)
                if identity not in seen:
                    candidates.append(item)
                    seen.add(identity)
        except Exception:
            return

    return collect


def _attach(context: Any, listener: Any) -> bool:
    on = getattr(context, "on", None)
    if callable(on):
        on("response", listener)
        return True
    return False


def _detach(context: Any, listener: Any, attached: bool) -> None:
    if not attached:
        return
    try:
        remove = getattr(context, "remove_listener", None)
        if callable(remove):
            remove("response", listener)
    except Exception:
        pass


def _wait(page: Any, milliseconds: int) -> None:
    if hasattr(page, "wait_for_timeout"):
        page.wait_for_timeout(milliseconds)
    else:
        time.sleep(milliseconds / 1000.0)


def _wait_for_exact_record(
    context: Any,
    page: Any,
    records: list[ExactHistoryRecord],
    *,
    timeout_ms: int,
) -> ExactHistoryRecord:
    deadline = time.monotonic() + timeout_ms / 1000.0
    retried_report_pages = False
    while True:
        if records:
            return records[0]
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(
                "Pangram submission produced no exact-matching stored history record before timeout"
            )

        # If the browser reached a report route before the response listener saw
        # its JSON, one bounded read-only reload makes Pangram reissue the record GET.
        if not retried_report_pages:
            report_pages = []
            for candidate in tuple(getattr(context, "pages", ())):
                try:
                    if _HISTORY_REPORT_RE.fullmatch(str(getattr(candidate, "url", ""))):
                        report_pages.append(candidate)
                except Exception:
                    continue
            if report_pages:
                retried_report_pages = True
                for candidate in report_pages:
                    try:
                        candidate.reload(wait_until="domcontentloaded")
                        _wait(candidate, 800)
                    except Exception:
                        continue
                    if records:
                        return records[0]

        _wait(page, min(500, max(1, int(remaining * 1000))))


def _materialize_record_report(
    context: Any,
    page: Any,
    record: ExactHistoryRecord,
) -> tuple[Any, str, dict[str, object]]:
    working = local.normalize_context_tabs(context, keep=page)
    working.goto(record.report_url, wait_until="domcontentloaded")
    _wait(working, 1_800)
    body = local.gui_core.clean_report_body_artifact(working.locator("body").inner_text())
    parsed = parse_history_record_result(record, body)
    return working, body, parsed


def _reservation_path(directory: Path) -> Path:
    return directory / _RESERVATION_NAME


def _existing_incomplete_reservation(directory: Path) -> bool:
    reservation = _reservation_path(directory)
    result = directory / "result.json"
    return reservation.is_file() and not result.is_file()


def _reserve_submission(
    directory: Path,
    item: Mapping[str, object],
    callback: local.EvidenceCallback | None,
) -> dict[str, object]:
    reservation = {
        "schema_version": 1,
        "status": "paid_gui_submission_reserved",
        "transport": local.TRANSPORT_ID,
        "transport_runner_version": local.LOCAL_RUNNER_VERSION,
        "model": local.gui_core.MODEL_ID,
        "reserved_at_utc": _utc_now_iso(),
        "input_sha256": str(item["input_sha256"]),
        "word_count": int(item["word_count"]),
        "detector_submission_attempted": False,
        "duplicate_guard": (
            "Presence of this reservation without a complete result blocks automatic repeat submission."
        ),
    }
    local._write_json(_reservation_path(directory), reservation)
    local._persist_evidence(callback, directory, reservation)
    return reservation


def run_inputs(
    config: local.LocalPlaywrightConfig,
    input_paths: Iterable[Path],
    *,
    output_root: Path = Path("state/gui-runs"),
    force: bool = False,
    report_timeout_ms: int = 180_000,
    expected_sha256: Mapping[str, str] | None = None,
    source_metadata: Mapping[str, Mapping[str, object]] | None = None,
    evidence_callback: local.EvidenceCallback | None = None,
    print_fn: Any = print,
) -> list[dict[str, object]]:
    prepared = local._prepare_inputs(
        input_paths,
        output_root=output_root,
        force=force,
        expected_sha256=expected_sha256,
    )
    blocked = [item for item in prepared if item["blocked_by_ambiguous_submission"]]
    if blocked and not force:
        identities = ", ".join(str(item["input_sha256"]) for item in blocked)
        raise RuntimeError(
            "refusing to repeat Pangram GUI input after an ambiguous prior submission: "
            f"{identities}"
        )

    for item in prepared:
        directory = Path(str(item["directory"]))
        if _existing_incomplete_reservation(directory) and not force:
            raise RuntimeError(
                "refusing to repeat Pangram GUI input because a durable paid-submission reservation "
                f"exists without a complete result: {item['input_sha256']}"
            )

    pending = [item for item in prepared if not item["skip"]]
    results: list[dict[str, object]] = [
        {
            "status": "cached",
            "transport": local.TRANSPORT_ID,
            "input_path": item["input_path"],
            "input_sha256": item["input_sha256"],
            "word_count": item["word_count"],
            "directory": item["directory"],
        }
        for item in prepared
        if item["skip"]
    ]
    if not pending:
        return results

    playwright, context, page = local._launch_persistent_context(config)
    try:
        for item in pending:
            directory = Path(str(item["directory"]))
            paths = local.gui_core.artifact_paths(directory)
            directory.mkdir(parents=True, exist_ok=True)
            source = local._source_for_item(item, source_metadata)
            stage = "navigate"
            detector_submission_attempted = False
            reservation: dict[str, object] | None = None
            report_page = page
            exact_records: list[ExactHistoryRecord] = []
            listener = _record_listener(str(item["text"]), exact_records)
            attached = False
            try:
                page.goto(config.pangram_url, wait_until="domcontentloaded")
                stage = "verify_authentication"
                field = local.wait_for_authenticated_detector_input(page)
                stage = "fill_input"
                field.fill(str(item["text"]))
                stage = "locate_detector_action"
                button = local.gui_core.detection_button(page)

                stage = "reserve_paid_submission"
                reservation = _reserve_submission(directory, item, evidence_callback)

                # Exact history capture must be active before the paid detector click.
                attached = _attach(context, listener)
                if not attached:
                    raise RuntimeError("browser context does not support response listeners")

                stage = "submit"
                detector_submission_attempted = True
                button.click()
                print_fn(
                    f"[pangram-local] submitted sha={item['input_sha256']}; "
                    "waiting for exact stored history record"
                )

                stage = "wait_exact_history_record"
                record = _wait_for_exact_record(
                    context,
                    page,
                    exact_records,
                    timeout_ms=report_timeout_ms,
                )
                if (
                    record.input_sha256 != str(item["input_sha256"])
                    or record.word_count != int(item["word_count"])
                ):
                    raise RuntimeError("stored Pangram history record failed exact source identity gate")

                stage = "capture_body"
                report_page, body, parsed = _materialize_record_report(context, page, record)
                paths["body"].write_text(body, encoding="utf-8")

                stage = "capture_pdf"
                pdf_provenance = local.capture_report_pdf(report_page, paths["pdf"])
                receipt = local.build_complete_receipt(
                    config,
                    item=item,
                    report_url=report_page.url,
                    pdf_provenance=pdf_provenance,
                    parsed=parsed,
                    body=body,
                    pdf_path=paths["pdf"],
                    source=source,
                )
                receipt["history_api_exact_identity"] = record.public_proof()
                receipt["submission_reservation"] = reservation
                local._write_json(paths["result"], receipt)
                local._remove_stale_failures(directory, paths)
                stage = "persist_evidence"
                local._persist_evidence(evidence_callback, directory, receipt)
                results.append(receipt)
                print_fn(
                    f"[pangram-local] complete sha={item['input_sha256']} "
                    f"words={item['word_count']} pdf={pdf_provenance}"
                )
                page = local.normalize_context_tabs(context, keep=report_page)
            except Exception as exc:
                if stage == "persist_evidence":
                    raise
                failure = local.build_failure_receipt(
                    config,
                    item=item,
                    stage=stage,
                    detector_submission_attempted=detector_submission_attempted,
                    error=exc,
                    source=source,
                )
                failure["submission_reservation"] = reservation
                failure["exact_history_api_record_found"] = bool(exact_records)
                local._write_json(paths["failure"], failure)
                try:
                    report_page.screenshot(path=str(paths["failure_screenshot"]), full_page=True)
                except Exception:
                    pass
                try:
                    local._persist_evidence(evidence_callback, directory, failure)
                except Exception as durability_error:
                    raise RuntimeError(
                        "Pangram GUI run failed and failure evidence could not be made durable: "
                        f"run_error={exc}; durability_error={durability_error}"
                    ) from durability_error
                raise
            finally:
                _detach(context, listener, attached)
    finally:
        local._close_local_session(playwright, context)
    return results


def _dom_history_candidates(page: Any) -> tuple[str, ...]:
    values: list[str] = []
    try:
        links = page.locator("a[href]")
        count = int(links.count())
    except Exception:
        return ()
    for index in range(count):
        try:
            href = str(links.nth(index).get_attribute("href") or "")
        except Exception:
            continue
        if href.startswith("/history/"):
            href = "https://www.pangram.com" + href
        match = _HISTORY_REPORT_RE.fullmatch(href)
        if match and href not in values:
            values.append(href)
    return tuple(values)


def recover_existing_report(
    config: local.LocalPlaywrightConfig,
    input_path: Path,
    *,
    output_root: Path = Path("state/gui-runs"),
    expected_sha256: str | None = None,
    source_metadata: Mapping[str, object] | None = None,
    evidence_callback: local.EvidenceCallback | None = None,
    max_candidates: int = 100,
    print_fn: Any = print,
) -> dict[str, object]:
    expected = None if expected_sha256 is None else {str(input_path): expected_sha256}
    item = local._prepare_inputs(
        [input_path],
        output_root=output_root,
        force=True,
        expected_sha256=expected,
    )[0]
    directory = Path(str(item["directory"]))
    paths = local.gui_core.artifact_paths(directory)
    if paths["result"].is_file():
        try:
            return json.loads(paths["result"].read_text(encoding="utf-8"))
        except Exception:
            pass

    directory.mkdir(parents=True, exist_ok=True)
    exact_text = str(item["text"])
    exact_records: list[ExactHistoryRecord] = []
    history_candidates: list[HistoryListCandidate] = []
    record_listener = _record_listener(exact_text, exact_records)
    list_listener = _history_list_listener(history_candidates)

    stage = "launch_browser"
    playwright = None
    context = None
    page = None
    report_page = None
    record_attached = False
    list_attached = False
    try:
        playwright, context, page = local._launch_persistent_context(config)
        report_page = page
        record_attached = _attach(context, record_listener)
        list_attached = _attach(context, list_listener)

        stage = "navigate_detector"
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        stage = "verify_authentication"
        local.wait_for_authenticated_detector_input(page)

        # Pangram's own application history is authoritative for stored scans.
        # Opening it is read-only and normally emits /api/history-list/.
        stage = "load_history"
        page.goto("https://www.pangram.com/history", wait_until="domcontentloaded")
        _wait(page, 1_800)

        stage = "scan_history_candidates"
        report_urls = [
            f"https://www.pangram.com/history/{candidate.uuid}"
            for candidate in history_candidates[:max_candidates]
        ]
        for url in _dom_history_candidates(page):
            if url not in report_urls:
                report_urls.append(url)

        for url in report_urls[:max_candidates]:
            try:
                page.goto(url, wait_until="domcontentloaded")
                _wait(page, 700)
            except Exception:
                continue
            if exact_records:
                break

        if not exact_records:
            raise RuntimeError(
                "no exact-matching Pangram stored history record was found; no detector submission was made"
            )
        record = exact_records[0]
        if (
            record.input_sha256 != str(item["input_sha256"])
            or record.word_count != int(item["word_count"])
        ):
            raise RuntimeError("recovered Pangram history record failed exact source identity gate")

        stage = "materialize_history_record"
        report_page, body, parsed = _materialize_record_report(context, page, record)
        paths["body"].write_text(body, encoding="utf-8")
        stage = "capture_pdf"
        pdf_provenance = local.capture_report_pdf(report_page, paths["pdf"])
        receipt = local.build_complete_receipt(
            config,
            item=item,
            report_url=report_page.url,
            pdf_provenance=pdf_provenance,
            parsed=parsed,
            body=body,
            pdf_path=paths["pdf"],
            source=source_metadata,
            evidence_source="recovered_existing_report",
            detector_submission_attempted=False,
        )
        receipt["history_api_exact_identity"] = record.public_proof()
        receipt["history_list_candidate_count"] = len(history_candidates)
        local._write_json(paths["result"], receipt)
        local._remove_stale_failures(directory, paths)
        stage = "persist_evidence"
        local._persist_evidence(evidence_callback, directory, receipt)
        print_fn(
            f"[pangram-local] recovered sha={item['input_sha256']} "
            f"words={item['word_count']} without detector submission"
        )
        return receipt
    except Exception as exc:
        if stage == "persist_evidence":
            raise
        failure = local.build_failure_receipt(
            config,
            item=item,
            stage=stage,
            detector_submission_attempted=False,
            error=exc,
            source=source_metadata,
        )
        failure["evidence_source"] = "recovered_existing_report"
        failure["read_only_recovery"] = True
        failure["exact_history_api_record_found"] = bool(exact_records)
        failure["history_list_candidate_count"] = len(history_candidates)
        local._write_json(paths["failure"], failure)
        if report_page is not None:
            try:
                report_page.screenshot(path=str(paths["failure_screenshot"]), full_page=True)
            except Exception:
                pass
        try:
            local._persist_evidence(evidence_callback, directory, failure)
        except Exception as durability_error:
            raise RuntimeError(
                "Pangram read-only History recovery failed and failure evidence could not be made durable: "
                f"recovery_error={exc}; durability_error={durability_error}"
            ) from durability_error
        raise
    finally:
        if context is not None:
            _detach(context, record_listener, record_attached)
            _detach(context, list_listener, list_attached)
            try:
                if report_page is not None:
                    local.normalize_context_tabs(context, keep=report_page)
            except Exception:
                pass
        if playwright is not None and context is not None:
            local._close_local_session(playwright, context)


# Re-export the validated low-level local-browser operations for callers.
LocalPlaywrightConfig = local.LocalPlaywrightConfig
DEFAULT_PROFILE_DIR = local.DEFAULT_PROFILE_DIR
bootstrap_login = local.bootstrap_login
verify_login_persistence = local.verify_login_persistence
launch_smoke_test = local.launch_smoke_test
environment_status = local.environment_status
input_status = local.input_status
