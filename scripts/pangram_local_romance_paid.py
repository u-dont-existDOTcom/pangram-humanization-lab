#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from pangram_lab import gui_browserbase as gui_core
from pangram_lab import gui_local as local_transport
from pangram_lab import gui_local_legacy as local_core
from pangram_lab.call_budget import PangramCallLedger, SectionCallCapReached
from pangram_lab.git_sync import GitSync
from pangram_lab.local_cli import (
    CURRENT_ROMANCE_PARTS,
    DEFAULT_OUTPUT_ROOT,
    GitEvidenceDurability,
    _input_digests,
    _resolve_output_root,
    materialize_current_romance_inputs,
    repository_root,
)

AUDIT_ID = "romance-current-20496-pangram-gui-20260818"
EXPECTED_VERSION = "4.0"
SECTION_IDS = {
    1: "romance-current-part-1",
    2: "romance-current-part-2",
}


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), flush=True)


def _source_for(
    source_metadata: Mapping[str, Mapping[str, object]] | None,
    path: Path,
) -> Mapping[str, object] | None:
    if source_metadata is None:
        return None
    return source_metadata.get(str(path)) or source_metadata.get(path.name)


def _section_for(path: Path) -> tuple[int, str]:
    for part in CURRENT_ROMANCE_PARTS:
        if path.name == str(part["name"]):
            number = int(part["number"])
            return number, SECTION_IDS[number]
    raise RuntimeError(f"unexpected current Romance input: {path}")


def _reservation_exists(
    ledger: PangramCallLedger,
    *,
    section_id: str,
    measurement_key: str,
) -> bool:
    for section in ledger.state.get("sections", {}).values():
        if (
            section.get("section_id") == section_id
            and section.get("model") == gui_core.MODEL_ID
            and section.get("version") == EXPECTED_VERSION
        ):
            for event in section.get("events", []):
                if (
                    event.get("type") == "paid_post_reserved"
                    and event.get("measurement_key") == measurement_key
                ):
                    return True
    return False


def _prepared_item(path: Path, output_root: Path, expected_digest: str) -> dict[str, object]:
    item = gui_core.prepare_measurement(path, output_root=output_root, force=False)
    actual = str(item["input_sha256"])
    if actual != expected_digest:
        raise RuntimeError(
            f"refusing paid Pangram work because exact SHA-256 changed for {path}: "
            f"expected={expected_digest} actual={actual}"
        )
    if item["blocked_by_ambiguous_submission"]:
        raise RuntimeError(
            "refusing paid Pangram work after an ambiguous prior submission for "
            f"sha={actual}; use History/recovery before any repeat"
        )
    return item


def _status_receipt(
    prepared: Any,
    output_root: Path,
    ledger: PangramCallLedger,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    expected = prepared.expected_sha256 or {}
    for path in prepared.paths:
        digest = expected.get(str(path)) or expected.get(path.name)
        if digest is None:
            raise RuntimeError(f"missing exact SHA gate for {path}")
        item = _prepared_item(path, output_root, digest)
        number, section_id = _section_for(path)
        measurement_key = f"gui:{digest}"
        reserved = _reservation_exists(
            ledger,
            section_id=section_id,
            measurement_key=measurement_key,
        )
        if reserved and not item["skip"]:
            raise RuntimeError(
                "a durable paid-call reservation already exists without a completed cache result for "
                f"section={section_id} sha={digest}; treat this as ambiguous and inspect Pangram History "
                "before any repeat"
            )
        rows.append(
            {
                "part": number,
                "section_id": section_id,
                "input_sha256": digest,
                "word_count": int(item["word_count"]),
                "result_cached": bool(item["skip"]),
                "ambiguous_submission_block": bool(item["blocked_by_ambiguous_submission"]),
                "paid_reservation_exists": reserved,
            }
        )
    return {
        "audit_id": AUDIT_ID,
        "source": prepared.source_receipt,
        "inputs": rows,
        "call_accounting": ledger.audit_summary(),
    }


def preflight() -> dict[str, object]:
    repo_root = repository_root()
    output_root = _resolve_output_root(repo_root, DEFAULT_OUTPUT_ROOT)
    prepared = materialize_current_romance_inputs(repo_root, no_fetch=False)
    digests = _input_digests(prepared.paths, prepared.expected_sha256)
    durability = GitEvidenceDurability(repo_root, output_root)
    durability.preflight(digests)

    config = local_transport.LocalPlaywrightConfig.from_env()
    auth = local_transport.verify_login_persistence(config)
    ledger = PangramCallLedger(repo_root, AUDIT_ID)
    status = _status_receipt(prepared, output_root, ledger)
    return {
        "status": "ready",
        "authentication": auth,
        **status,
    }


def execute() -> dict[str, object]:
    repo_root = repository_root()
    output_root = _resolve_output_root(repo_root, DEFAULT_OUTPUT_ROOT)
    prepared = materialize_current_romance_inputs(repo_root, no_fetch=False)
    digests = _input_digests(prepared.paths, prepared.expected_sha256)
    durability = GitEvidenceDurability(repo_root, output_root)
    durability.preflight(digests)

    config = local_transport.LocalPlaywrightConfig.from_env()
    local_transport.verify_login_persistence(config)

    ledger = PangramCallLedger(repo_root, AUDIT_ID)
    pre_status = _status_receipt(prepared, output_root, ledger)
    expected = prepared.expected_sha256 or {}
    pending: list[tuple[Path, dict[str, object], int, str, str]] = []
    results: list[dict[str, object]] = []

    for path in prepared.paths:
        digest = expected.get(str(path)) or expected.get(path.name)
        if digest is None:
            raise RuntimeError(f"missing exact SHA gate for {path}")
        item = _prepared_item(path, output_root, digest)
        number, section_id = _section_for(path)
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
            "audit_id": AUDIT_ID,
            "source": prepared.source_receipt,
            "preflight": pre_status,
            "results": results,
            "call_accounting": ledger.audit_summary(),
        }

    git = GitSync(repo_root, require_remote=True)
    playwright, context, page = local_transport._launch_persistent_context(config)
    try:
        for path, item, number, section_id, digest in pending:
            directory = Path(str(item["directory"]))
            paths = gui_core.artifact_paths(directory)
            directory.mkdir(parents=True, exist_ok=True)
            source = _source_for(prepared.source_metadata, path)
            stage = "navigate"
            detector_submission_attempted = False
            measurement_key = f"gui:{digest}"
            call_summary: dict[str, object] | None = None
            try:
                page.goto(config.pangram_url, wait_until="domcontentloaded")
                stage = "verify_authentication"
                field = local_transport.wait_for_authenticated_detector_input(page)
                stage = "fill_input"
                field.fill(str(item["text"]))

                # Resolve the exact bounded action before reserving a paid call.
                stage = "locate_detector_action"
                button = gui_core.detection_button(page)

                stage = "reserve_paid_call"
                try:
                    call_summary = ledger.reserve_paid_call(
                        section_id=section_id,
                        model=gui_core.MODEL_ID,
                        version=EXPECTED_VERSION,
                        measurement_key=measurement_key,
                        text_sha256=digest,
                        word_count=int(item["word_count"]),
                    )
                except SectionCallCapReached:
                    handoff = ledger.write_handoff(
                        section_id,
                        gui_core.MODEL_ID,
                        EXPECTED_VERSION,
                        results,
                    )
                    git.sync_paths(
                        [ledger.path, handoff],
                        f"pangram local call-cap handoff {AUDIT_ID} {section_id}",
                    )
                    raise

                # The reservation must be durable before the UI action that may spend credits.
                git.sync_paths(
                    [ledger.path],
                    f"reserve Pangram paid call {AUDIT_ID} {section_id} {digest[:16]}",
                )

                stage = "submit"
                detector_submission_attempted = True
                button.click()
                print(
                    f"[pangram-local-paid] submitted part={number} sha={digest}; waiting for report",
                    flush=True,
                )

                stage = "wait_report"
                gui_core.wait_for_report(page, timeout_ms=180_000)
                stage = "capture_body"
                body = gui_core.clean_report_body_artifact(page.locator("body").inner_text())
                paths["body"].write_text(body, encoding="utf-8")
                parsed = gui_core.parse_report_for_exact_input(
                    body,
                    str(item["text"]),
                    expected_word_count=int(item["word_count"]),
                )
                segments = list(parsed["segments"])
                if not segments:
                    raise RuntimeError(
                        "Pangram report became visible but no analyzed segments could be parsed"
                    )
                parsed_word_count = sum(int(segment["word_count"]) for segment in segments)
                if parsed_word_count != int(item["word_count"]):
                    raise RuntimeError(
                        "Pangram report word count does not match exact input: "
                        f"report={parsed_word_count} input={item['word_count']}"
                    )

                stage = "capture_pdf"
                pdf_provenance = local_transport.capture_report_pdf(page, paths["pdf"])
                receipt = local_core.build_complete_receipt(
                    config,
                    item=item,
                    report_url=page.url,
                    pdf_provenance=pdf_provenance,
                    parsed=parsed,
                    body=body,
                    pdf_path=paths["pdf"],
                    source=source,
                )
                receipt.update(
                    {
                        "audit_id": AUDIT_ID,
                        "section_id": section_id,
                        "measurement_key": measurement_key,
                        "call_accounting": call_summary,
                    }
                )
                local_core._write_json(paths["result"], receipt)
                local_core._remove_stale_failures(directory, paths)
                stage = "persist_evidence"
                durability(directory, receipt)
                results.append(receipt)
                print(
                    f"[pangram-local-paid] complete part={number} sha={digest} pdf={pdf_provenance}",
                    flush=True,
                )
            except Exception as exc:
                if stage == "persist_evidence":
                    raise
                failure = local_core.build_failure_receipt(
                    config,
                    item=item,
                    stage=stage,
                    detector_submission_attempted=detector_submission_attempted,
                    error=exc,
                    source=source,
                )
                failure.update(
                    {
                        "audit_id": AUDIT_ID,
                        "section_id": section_id,
                        "measurement_key": measurement_key,
                        "call_accounting": call_summary
                        or ledger.section_summary(
                            section_id,
                            gui_core.MODEL_ID,
                            EXPECTED_VERSION,
                        ),
                    }
                )
                local_core._write_json(paths["failure"], failure)
                try:
                    page.screenshot(path=str(paths["failure_screenshot"]), full_page=True)
                except Exception:
                    pass
                try:
                    durability(directory, failure)
                except Exception as durability_error:
                    raise RuntimeError(
                        "Pangram paid run failed and the saved failure evidence could not be pushed "
                        f"durably: run_error={exc}; durability_error={durability_error}"
                    ) from durability_error
                raise
    finally:
        local_core._close_local_session(playwright, context)

    return {
        "status": "complete",
        "audit_id": AUDIT_ID,
        "source": prepared.source_receipt,
        "preflight": pre_status,
        "results": results,
        "call_accounting": ledger.audit_summary(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Budgeted exact-current Romance Pangram GUI run on the local persistent profile."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    result = preflight() if args.preflight_only else execute()
    _json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
