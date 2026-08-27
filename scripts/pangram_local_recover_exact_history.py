#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pangram_lab import gui_browserbase as gui_core
from pangram_lab import gui_local as local_transport
from pangram_lab.exact_history_recovery import (
    HISTORY_LIST_URL,
    context_get_json,
    find_exact_history_record,
)
from pangram_lab.history_api_record import parse_history_record_result
from pangram_lab.history_list_recovery import parse_timestamp
from pangram_lab.local_cli import GitEvidenceDurability, _resolve_output_root, repository_root


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), flush=True)


def _expected_mapping(input_path: Path, digest: str) -> dict[str, str]:
    return {str(input_path): digest}


def _source(args: argparse.Namespace) -> dict[str, object] | None:
    supplied = (
        args.source_repository,
        args.source_branch,
        args.source_commit,
        args.source_path,
    )
    if not any(supplied):
        return None
    if not all(supplied):
        raise RuntimeError(
            "source provenance requires --source-repository, --source-branch, "
            "--source-commit, and --source-path together"
        )
    result: dict[str, object] = {
        "repository": args.source_repository,
        "source_branch": args.source_branch,
        "source_commit": args.source_commit,
        "source_path": args.source_path,
    }
    if args.source_file_sha256:
        result["source_file_sha256"] = args.source_file_sha256
    return result


def _target_time(directory: Path, explicit: str | None = None) -> Any | None:
    if explicit is not None:
        parsed = parse_timestamp(explicit)
        if parsed is None:
            raise RuntimeError("--target-time-utc is not a valid timestamp")
        return parsed
    failure_path = directory / "failure.json"
    if not failure_path.is_file():
        return None
    try:
        payload = json.loads(failure_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if payload.get("detector_submission_attempted") is not True:
        return None
    return parse_timestamp(payload.get("captured_at_utc"))


def recover(args: argparse.Namespace) -> dict[str, object]:
    repo_root = repository_root()
    output_root = _resolve_output_root(repo_root, args.output_root)
    input_path = args.input.expanduser().resolve(strict=True)
    expected = _expected_mapping(input_path, args.expect_sha.lower())
    prepared = local_transport._prepare_inputs(
        [input_path],
        output_root=output_root,
        force=True,
        expected_sha256=expected,
    )[0]
    digest = str(prepared["input_sha256"])
    if digest != args.expect_sha.lower():
        raise RuntimeError(
            f"exact input SHA-256 changed: expected={args.expect_sha.lower()} actual={digest}"
        )

    directory = Path(str(prepared["directory"]))
    paths = gui_core.artifact_paths(directory)
    source = _source(args)
    target_time = _target_time(directory, args.target_time_utc)
    if args.require_unique_target_match and target_time is None:
        raise RuntimeError("unique target recovery requires --target-time-utc")
    durability = GitEvidenceDurability(repo_root, output_root)
    durability.preflight({input_path: digest})

    config = local_transport.LocalPlaywrightConfig.from_env()
    playwright, context, page = local_transport._launch_persistent_context(
        config,
        normalize_tabs=False,
    )
    stage = "navigate"
    try:
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        stage = "verify_authentication"
        local_transport.wait_for_authenticated_detector_input(page)
        stage = "read_history_list"
        history_list, history_status = context_get_json(context, HISTORY_LIST_URL)
        if history_list is None:
            raise RuntimeError(
                "authenticated Pangram History list was unavailable read-only: " + history_status
            )

        stage = "bind_exact_history_record"
        record, recovery_proof = find_exact_history_record(
            context,
            history_list,
            str(prepared["text"]),
            target_time=target_time,
            require_unique_match=args.require_unique_target_match,
        )
        if record is None:
            raise RuntimeError(
                "no exact/bounded Pangram History record matched the authorized input; "
                "recovery_proof=" + json.dumps(recovery_proof, sort_keys=True)
            )

        stage = "render_exact_history_record"
        report_page = local_transport.normalize_context_tabs(context, keep=page)
        report_page.goto(record.report_url, wait_until="domcontentloaded")
        if hasattr(report_page, "wait_for_timeout"):
            report_page.wait_for_timeout(1_800)
        body = gui_core.clean_report_body_artifact(report_page.locator("body").inner_text())
        parsed = parse_history_record_result(record, body)
        directory.mkdir(parents=True, exist_ok=True)
        paths["body"].write_text(body, encoding="utf-8")

        stage = "capture_exact_report"
        pdf_provenance = local_transport.capture_report_pdf(report_page, paths["pdf"])
        receipt = local_transport.build_complete_receipt(
            config,
            item=prepared,
            report_url="https://www.pangram.com/history/<uuid>",
            pdf_provenance=pdf_provenance,
            parsed=parsed,
            body=body,
            pdf_path=paths["pdf"],
            source=source,
            evidence_source="recovered_exact_history_record",
            detector_submission_attempted=False,
        )
        receipt["history_api_exact_identity"] = record.public_proof()
        receipt["history_recovery_proof"] = recovery_proof
        if parsed.get("detector_version"):
            receipt["detector_version"] = parsed["detector_version"]
        local_transport._write_json(paths["result"], receipt)
        local_transport._remove_stale_failures(directory, paths)
        stage = "persist_evidence"
        durability(directory, receipt)
        return receipt
    except Exception as exc:
        if stage == "persist_evidence":
            raise
        directory.mkdir(parents=True, exist_ok=True)
        failure = local_transport.build_failure_receipt(
            config,
            item=prepared,
            stage=stage,
            detector_submission_attempted=False,
            error=exc,
            source=source,
            evidence_source="exact_history_recovery",
        )
        local_transport._write_json(directory / "recovery-failure.json", failure)
        try:
            page.screenshot(path=str(directory / "recovery-failure.png"), full_page=True)
        except Exception:
            pass
        durability(directory, failure)
        raise
    finally:
        local_transport._close_local_session(playwright, context)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recover an already-submitted exact Pangram GUI result from authenticated History."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--expect-sha", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("state/gui-runs"))
    parser.add_argument("--source-repository")
    parser.add_argument("--source-branch")
    parser.add_argument("--source-commit")
    parser.add_argument("--source-path")
    parser.add_argument("--source-file-sha256")
    parser.add_argument("--target-time-utc")
    parser.add_argument("--require-unique-target-match", action="store_true")
    args = parser.parse_args()
    if len(args.expect_sha) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in args.expect_sha):
        parser.error("--expect-sha must be a 64-character hexadecimal SHA-256")
    _json(recover(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
