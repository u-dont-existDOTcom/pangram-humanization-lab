#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pangram_lab import gui_browserbase as gui_core
from pangram_lab import gui_local as local_transport
from pangram_lab import gui_local_legacy as local_core
from pangram_lab.call_budget import PangramCallLedger
from pangram_lab.local_cli import (
    DEFAULT_OUTPUT_ROOT,
    GitEvidenceDurability,
    _resolve_output_root,
    materialize_current_romance_inputs,
    repository_root,
)

AUDIT_ID = "romance-current-20496-pangram-gui-20260818"
SECTION_ID = "romance-current-part-1"
EXPECTED_VERSION = "4.0"
EXPECTED_SHA = "ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8"
EXPECTED_WORDS = 10_236


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), flush=True)


def _visible_control(page: Any, role: str, pattern: re.Pattern[str]) -> Any | None:
    try:
        locator = page.get_by_role(role, name=pattern)
        count = int(locator.count())
    except Exception:
        return None
    for index in range(count):
        candidate = locator.nth(index)
        try:
            if candidate.is_visible() and (not hasattr(candidate, "is_enabled") or candidate.is_enabled()):
                return candidate
        except Exception:
            continue
    return None


def _try_open_history(page: Any) -> bool:
    pattern = re.compile(r"^(?:history|scan history|my scans|recent scans|reports)$", re.IGNORECASE)
    for role in ("link", "button"):
        control = _visible_control(page, role, pattern)
        if control is not None:
            control.click()
            try:
                page.wait_for_timeout(1_500)
            except Exception:
                pass
            return True
    return False


def _try_open_exact_preview(context: Any, exact_text: str) -> bool:
    # If History shows a text preview, click only a unique leading-anchor match.
    # This is non-paid navigation and never touches the detector action.
    anchor = " ".join(exact_text.split()[:10])
    if not anchor:
        return False
    pattern = re.compile(re.escape(anchor), re.IGNORECASE)
    for page in reversed(tuple(getattr(context, "pages", ()))):
        try:
            locator = page.get_by_text(pattern, exact=False)
            count = int(locator.count())
        except Exception:
            continue
        visible: list[Any] = []
        for index in range(count):
            candidate = locator.nth(index)
            try:
                if candidate.is_visible():
                    visible.append(candidate)
            except Exception:
                continue
        if len(visible) == 1:
            try:
                visible[0].click()
                page.wait_for_timeout(1_500)
                return True
            except Exception:
                continue
    return False


def _find_or_open_report(context: Any, page: Any, exact_text: str) -> tuple[Any, str, dict[str, object]]:
    # First exploit the persistent-profile tab state. The failed paid run may
    # have left the actual result in another tab even though it parsed the
    # dashboard tab.
    try:
        return local_transport.wait_for_exact_report_page(
            context,
            exact_text,
            expected_word_count=EXPECTED_WORDS,
            timeout_ms=12_000,
            poll_ms=500,
        )
    except RuntimeError:
        pass

    # If the result tab was not restored, use bounded non-paid History
    # navigation and look for the exact result again. Never click a detector
    # action here.
    page = local_transport.normalize_context_tabs(context, keep=page)
    page.goto(local_transport.DEFAULT_PANGRAM_GUI_URL, wait_until="domcontentloaded")
    local_transport.wait_for_authenticated_detector_input(page)
    opened_history = _try_open_history(page)
    if opened_history:
        try:
            return local_transport.wait_for_exact_report_page(
                context,
                exact_text,
                expected_word_count=EXPECTED_WORDS,
                timeout_ms=8_000,
                poll_ms=500,
            )
        except RuntimeError:
            pass
        if _try_open_exact_preview(context, exact_text):
            return local_transport.wait_for_exact_report_page(
                context,
                exact_text,
                expected_word_count=EXPECTED_WORDS,
                timeout_ms=12_000,
                poll_ms=500,
            )

    diagnostic = local_transport.report_surface_diagnostic(context)
    raise RuntimeError(
        "Part 1 is paid/ambiguous but its exact report could not be recovered automatically; "
        "no repeat submission was made. report_surface="
        + json.dumps(diagnostic, ensure_ascii=False, sort_keys=True)
    )


def recover() -> dict[str, object]:
    repo_root = repository_root()
    output_root = _resolve_output_root(repo_root, DEFAULT_OUTPUT_ROOT)
    prepared = materialize_current_romance_inputs(repo_root, no_fetch=False)
    part_path = prepared.paths[0]
    exact_text = part_path.read_text(encoding="utf-8")
    actual_sha = gui_core.sha256_text(exact_text)
    if actual_sha != EXPECTED_SHA or len(exact_text.split()) != EXPECTED_WORDS:
        raise RuntimeError("Part 1 no longer matches the paid ambiguous exact boundary")

    directory = gui_core.measurement_dir(output_root, EXPECTED_SHA)
    paths = gui_core.artifact_paths(directory)
    if paths["result"].is_file():
        return {
            "status": "already_recovered",
            "input_sha256": EXPECTED_SHA,
            "result_path": str(paths["result"]),
        }
    if not paths["failure"].is_file():
        raise RuntimeError("Part 1 has no saved ambiguous failure to recover")
    failure = json.loads(paths["failure"].read_text(encoding="utf-8"))
    if failure.get("detector_submission_attempted") is not True:
        raise RuntimeError("Part 1 failure is not marked as a possible paid submission")

    ledger = PangramCallLedger(repo_root, AUDIT_ID)
    call_accounting = ledger.section_summary(
        SECTION_ID,
        gui_core.MODEL_ID,
        EXPECTED_VERSION,
    )
    if int(call_accounting.get("paid_api_calls", 0)) < 1:
        raise RuntimeError("Part 1 call ledger has no durable paid reservation")

    config = local_transport.LocalPlaywrightConfig.from_env()
    # Deliberately do not normalize tabs at launch: the already-paid report may
    # be one of the restored tabs we need to recover. Cleanup happens after
    # recovery in the finally block.
    playwright, context, page = local_transport._launch_persistent_context(
        config,
        normalize_tabs=False,
    )
    report_page = page
    try:
        report_page, body, parsed = _find_or_open_report(context, page, exact_text)
        directory.mkdir(parents=True, exist_ok=True)
        paths["body"].write_text(body, encoding="utf-8")
        pdf_provenance = local_transport.capture_report_pdf(report_page, paths["pdf"])
        item = gui_core.prepare_measurement(part_path, output_root=output_root, force=True)
        source = None
        if prepared.source_metadata is not None:
            source = prepared.source_metadata.get(str(part_path)) or prepared.source_metadata.get(part_path.name)
        receipt = local_core.build_complete_receipt(
            config,
            item=item,
            report_url=report_page.url,
            pdf_provenance=pdf_provenance,
            parsed=parsed,
            body=body,
            pdf_path=paths["pdf"],
            source=source,
            evidence_source="recovered_existing_report",
            detector_submission_attempted=False,
        )
        receipt.update(
            {
                "audit_id": AUDIT_ID,
                "section_id": SECTION_ID,
                "measurement_key": f"gui:{EXPECTED_SHA}",
                "call_accounting": call_accounting,
                "recovered_from_ambiguous_paid_submission": True,
            }
        )
        local_core._write_json(paths["result"], receipt)
        local_core._remove_stale_failures(directory, paths)
        durability = GitEvidenceDurability(repo_root, output_root)
        durability(directory, receipt)
        return {
            "status": "recovered",
            "input_sha256": EXPECTED_SHA,
            "word_count": EXPECTED_WORDS,
            "report_url": report_page.url,
            "parsed": parsed,
            "call_accounting": call_accounting,
            "detector_submission_attempted_during_recovery": False,
        }
    finally:
        # Persist a clean one-tab state for every future launch.
        try:
            local_transport.normalize_context_tabs(context, keep=report_page)
        except Exception:
            pass
        local_transport._close_local_session(playwright, context)


if __name__ == "__main__":
    _json(recover())
