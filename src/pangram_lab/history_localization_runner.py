from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

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


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def localize_existing_report(
    config: local.LocalPlaywrightConfig,
    input_path: Path,
    *,
    output_root: Path = Path("state/gui-runs"),
    expected_sha256: str | None = None,
    evidence_callback: local.EvidenceCallback | None = None,
    max_candidates: int = 100,
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

    exact_records = []
    history_candidates: list[HistoryListCandidate] = []
    record_listener = _record_listener(exact_text, exact_records)
    list_listener = _history_list_listener(history_candidates)

    playwright, context, page = local._launch_persistent_context(config)
    record_attached = _attach(context, record_listener)
    list_attached = _attach(context, list_listener)
    try:
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        local.wait_for_authenticated_detector_input(page)

        # This path is intentionally read-only. It never locates or invokes the
        # detector action; it only traverses Pangram's stored History records.
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
            }
        )
        _write_json(localization_path, result)
        if evidence_callback is not None:
            evidence_callback(directory, result)
        print_fn(
            f"[pangram-local] localized sha={item['input_sha256']} "
            f"spans={result['localized_span_count']} without detector submission"
        )
        return result
    finally:
        _detach(context, record_listener, record_attached)
        _detach(context, list_listener, list_attached)
        local._close_local_session(playwright, context)
