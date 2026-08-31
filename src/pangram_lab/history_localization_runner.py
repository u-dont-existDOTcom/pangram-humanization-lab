from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from pangram_lab import gui_local as local
from pangram_lab.gui_local_structured import (
    _attach,
    _detach,
    _dom_history_candidates,
    _history_list_listener,
    _record_listener,
    _wait,
)
from pangram_lab.history_list_recovery import HistoryListCandidate
from pangram_lab.history_localization import localize_history_record


LOCALIZATION_NAME = "localization.json"
LOCALIZATION_FAILURE_NAME = "localization-failure.json"
_REPORT_PATH_RE = re.compile(
    r"^/history/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/?$"
)


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _validated_report_url(raw: str | None) -> str | None:
    if raw is None:
        return None
    parsed = urlsplit(str(raw).strip())
    if parsed.scheme != "https" or parsed.netloc.casefold() != "www.pangram.com":
        raise ValueError("stored Pangram report URL must use https://www.pangram.com/history/<uuid>")
    if not _REPORT_PATH_RE.fullmatch(parsed.path):
        raise ValueError("stored Pangram report URL must use /history/<uuid>")
    return f"https://www.pangram.com{parsed.path.rstrip('/')}"


def _request_direct_history_api_record(page: object, report_url: str) -> None:
    """Re-emit one known report's stored JSON when the SPA serves a cached page.

    The response listener remains the authority for exact-text binding. This
    helper only performs an authenticated, read-only GET and deliberately
    returns no private record identity or payload to the caller.
    """
    report_uuid = urlsplit(report_url).path.rstrip("/").rsplit("/", 1)[-1]
    page.evaluate(
        """async ({url}) => {
          const response = await fetch(url, {
            method: "GET",
            credentials: "include",
            cache: "no-store",
          });
          if (!response.ok) {
            throw new Error(`stored history GET failed (${response.status})`);
          }
          await response.json();
          return true;
        }""",
        {"url": f"https://web.pangram.com/api/history/{report_uuid}/"},
    )


def _failure_receipt(
    *,
    item: Mapping[str, object],
    stage: str,
    exc: Exception,
    history_candidate_count: int,
    exact_record_found: bool,
    direct_report_requested: bool,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "failed",
        "purpose": "stored_history_localization_only_not_document_score_authority",
        "input_sha256": str(item["input_sha256"]),
        "word_count": int(item["word_count"]),
        "detector_submission_attempted": False,
        "evidence_source": "stored_history_read_only_localization_failure",
        "stage": stage,
        "error_type": type(exc).__name__,
        "history_list_candidate_count": history_candidate_count,
        "exact_history_record_found": exact_record_found,
        "direct_report_requested": direct_report_requested,
        "privacy_note": (
            "Failure evidence omits submitted text, report UUID/URL, cookies, browser storage, headers, "
            "credentials, and raw exception text. No detector submission path is used."
        ),
    }


def localize_existing_report(
    config: local.LocalPlaywrightConfig,
    input_path: Path,
    *,
    output_root: Path = Path("state/gui-runs"),
    expected_sha256: str | None = None,
    evidence_callback: local.EvidenceCallback | None = None,
    max_candidates: int = 100,
    report_url: str | None = None,
    print_fn=print,
) -> dict[str, object]:
    """Localize exact stored Pangram History evidence without detector submission."""
    expected = None if expected_sha256 is None else {str(input_path): expected_sha256}
    item = local._prepare_inputs(
        [input_path],
        output_root=output_root,
        force=True,
        expected_sha256=expected,
    )[0]
    exact_text = str(item["text"])
    directory = Path(str(item["directory"]))
    localization_path = directory / LOCALIZATION_NAME
    failure_path = directory / LOCALIZATION_FAILURE_NAME
    selected_report_url = _validated_report_url(report_url)

    exact_records = []
    history_candidates: list[HistoryListCandidate] = []
    record_listener = _record_listener(exact_text, exact_records)
    list_listener = _history_list_listener(history_candidates)

    playwright = None
    context = None
    page = None
    record_attached = False
    list_attached = False
    stage = "launch_browser"
    try:
        playwright, context, page = local._launch_persistent_context(config)
        record_attached = _attach(context, record_listener)
        list_attached = _attach(context, list_listener)

        stage = "verify_authentication"
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        local.wait_for_authenticated_detector_input(page)

        # If an already-known stored report route is available, inspect it first.
        # This is read-only and avoids depending on History-list ordering.
        if selected_report_url is not None:
            stage = "direct_stored_report"
            page.goto(selected_report_url, wait_until="domcontentloaded")
            _wait(page, 1_200)
            if not exact_records:
                try:
                    page.reload(wait_until="domcontentloaded")
                    _wait(page, 800)
                except Exception:
                    pass
            if not exact_records:
                stage = "direct_stored_api_record"
                _request_direct_history_api_record(page, selected_report_url)
                _wait(page, 250)

        if not exact_records:
            stage = "scan_stored_history"
            # This path is intentionally read-only. It never locates or invokes
            # the detector action; it only traverses Pangram's stored History.
            page.goto("https://www.pangram.com/history", wait_until="domcontentloaded")
            _wait(page, 1_800)

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

        stage = "bind_exact_history_record"
        if not exact_records:
            raise RuntimeError("no exact-matching stored history record found")
        record = exact_records[0]
        if (
            record.input_sha256 != str(item["input_sha256"])
            or record.word_count != int(item["word_count"])
        ):
            raise RuntimeError("stored history record failed exact source identity gate")

        stage = "localize_stored_windows"
        result = localize_history_record(record, exact_text)
        result.update(
            {
                "transport": local.TRANSPORT_ID,
                "transport_runner_version": local.LOCAL_RUNNER_VERSION,
                "model": local.gui_core.MODEL_ID,
                "input_sha256": str(item["input_sha256"]),
                "word_count": int(item["word_count"]),
                "detector_submission_attempted": False,
                "evidence_source": "stored_history_read_only_localization",
                "history_list_candidate_count": len(history_candidates),
                "direct_report_used": selected_report_url is not None,
            }
        )
        _write_json(localization_path, result)
        try:
            failure_path.unlink()
        except FileNotFoundError:
            pass

        stage = "persist_localization"
        if evidence_callback is not None:
            evidence_callback(directory, result)
        print_fn(
            f"[pangram-local] localized sha={item['input_sha256']} "
            f"spans={result['localized_span_count']} without detector submission"
        )
        return result
    except Exception as exc:
        directory.mkdir(parents=True, exist_ok=True)
        failure = _failure_receipt(
            item=item,
            stage=stage,
            exc=exc,
            history_candidate_count=len(history_candidates),
            exact_record_found=bool(exact_records),
            direct_report_requested=selected_report_url is not None,
        )
        _write_json(failure_path, failure)
        if evidence_callback is not None:
            try:
                evidence_callback(directory, failure)
            except Exception:
                pass
        print_fn(
            f"[pangram-local] localization failed sha={item['input_sha256']} "
            f"stage={stage}; no detector submission"
        )
        raise
    finally:
        if context is not None:
            _detach(context, record_listener, record_attached)
            _detach(context, list_listener, list_attached)
        if playwright is not None and context is not None:
            local._close_local_session(playwright, context)
