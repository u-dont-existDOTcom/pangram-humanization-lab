#!/usr/bin/env python3
"""Read-only exact-hash probe for older Pangram records in the dedicated profile.

This task-scoped recovery tool has no detector fill or submission path. It reads
only Pangram ``/history/<uuid>`` routes already present in the dedicated local
automation profile, inspects their authenticated record responses in memory,
and persists a privacy-safe hash/difference receipt without report identifiers
or stored document text.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

from pangram_lab import gui_local as local
from pangram_lab.history_api_record import (
    ExactHistoryRecord,
    history_api_uuid,
    match_exact_history_record,
    parse_history_record_result,
)


_HISTORY_PATH_RE = re.compile(
    r"^/history/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/?$"
)
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_report_url(raw: str) -> str | None:
    try:
        parsed = urlsplit(str(raw))
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.netloc.casefold() not in {
        "pangram.com",
        "www.pangram.com",
    }:
        return None
    if not _HISTORY_PATH_RE.fullmatch(parsed.path):
        return None
    return "https://www.pangram.com" + parsed.path.rstrip("/")


def _history_databases(profile_dir: Path) -> tuple[Path, ...]:
    root = profile_dir.expanduser().resolve(strict=False)
    candidates = [root / "History"]
    try:
        candidates.extend(child / "History" for child in root.iterdir() if child.is_dir())
    except OSError:
        pass
    result: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            result.append(resolved)
    return tuple(result)


def _query_history(database: Path, limit: int) -> tuple[str, ...]:
    with tempfile.TemporaryDirectory(prefix="pangram-exact-history-probe-") as temporary:
        snapshot = Path(temporary) / "History"
        try:
            shutil.copy2(database, snapshot)
            for suffix in ("-wal", "-shm"):
                sidecar = Path(str(database) + suffix)
                if sidecar.is_file():
                    shutil.copy2(sidecar, Path(str(snapshot) + suffix))
        except OSError:
            return ()
        try:
            connection = sqlite3.connect(f"file:{snapshot}?mode=ro", uri=True)
            rows = connection.execute(
                "SELECT url FROM urls "
                "WHERE url LIKE 'https://www.pangram.com/history/%' "
                "OR url LIKE 'https://pangram.com/history/%' "
                "ORDER BY last_visit_time DESC LIMIT ?",
                (limit,),
            ).fetchall()
        except sqlite3.Error:
            return ()
        finally:
            try:
                connection.close()
            except UnboundLocalError:
                pass
    return tuple(str(row[0]) for row in rows if row and row[0])


def discover_report_urls(profile_dir: Path, limit: int) -> tuple[str, ...]:
    """Return only canonical Pangram report routes; callers must not print them."""
    result: list[str] = []
    seen: set[str] = set()
    for database in _history_databases(profile_dir):
        for raw in _query_history(database, limit):
            canonical = _canonical_report_url(raw)
            if canonical is None or canonical in seen:
                continue
            seen.add(canonical)
            result.append(canonical)
            if len(result) >= limit:
                return tuple(result)
    return tuple(result)


def _iter_strings(
    value: Any,
    *,
    ancestry: tuple[str, ...] = (),
    depth: int = 0,
) -> Iterable[tuple[tuple[str, ...], str]]:
    if depth > 10:
        return
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _iter_strings(child, ancestry=(*ancestry, str(key)), depth=depth + 1)
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _iter_strings(child, ancestry=(*ancestry, f"[{index}]"), depth=depth + 1)
        return
    if isinstance(value, str):
        yield ancestry, value


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


def _whitespace_escape(value: str) -> str | None:
    if value and not value.isspace():
        return None
    return value.encode("unicode_escape").decode("ascii")


def difference_summary(current: str, stored: str) -> dict[str, object]:
    operations: list[dict[str, object]] = []
    matcher = difflib.SequenceMatcher(a=current, b=stored, autojunk=False)
    for tag, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        if tag == "equal":
            continue
        current_value = current[a_start:a_end]
        stored_value = stored[b_start:b_end]
        operations.append(
            {
                "operation": tag,
                "current_character_range": [a_start, a_end],
                "stored_character_range": [b_start, b_end],
                "current_length": len(current_value),
                "stored_length": len(stored_value),
                "current_sha256": _sha256(current_value),
                "stored_sha256": _sha256(stored_value),
                "current_whitespace_escape": _whitespace_escape(current_value),
                "stored_whitespace_escape": _whitespace_escape(stored_value),
            }
        )
    return {
        "current_character_count": len(current),
        "stored_character_count": len(stored),
        "current_utf8_bytes": len(current.encode("utf-8")),
        "stored_utf8_bytes": len(stored.encode("utf-8")),
        "current_word_count": len(current.split()),
        "stored_word_count": len(stored.split()),
        "whitespace_collapsed_equal": " ".join(current.split()) == " ".join(stored.split()),
        "non_whitespace_sequence_equal": re.sub(r"\s+", "", current)
        == re.sub(r"\s+", "", stored),
        "difference_operation_count": len(operations),
        "difference_operations": operations,
    }


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expect-sha", required=True)
    parser.add_argument("--target-stored-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile-dir", type=Path, default=local.DEFAULT_PROFILE_DIR)
    parser.add_argument("--browser-executable", type=Path)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--max-candidates", type=int, default=200)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    expected_sha = str(args.expect_sha).lower()
    target_sha = str(args.target_stored_sha).lower()
    if not _HEX64_RE.fullmatch(expected_sha) or not _HEX64_RE.fullmatch(target_sha):
        raise RuntimeError("--expect-sha and --target-stored-sha must be lowercase SHA-256 values")
    if args.max_candidates < 1:
        raise RuntimeError("--max-candidates must be positive")

    current_text = args.input.expanduser().read_text(encoding="utf-8")
    current_sha = _sha256(current_text)
    if current_sha != expected_sha:
        raise RuntimeError(f"exact input SHA-256 changed: expected={expected_sha} actual={current_sha}")

    config = local.LocalPlaywrightConfig.from_env(
        profile_dir=args.profile_dir,
        browser_executable=args.browser_executable,
        headed=not args.headless,
    )
    report_urls = discover_report_urls(config.profile_dir, args.max_candidates)
    receipt: dict[str, object] = {
        "schema_version": 1,
        "status": "not_found",
        "purpose": "read_only_exact_history_hash_reconciliation",
        "transport": local.TRANSPORT_ID,
        "transport_runner_version": local.LOCAL_RUNNER_VERSION,
        "detector_submission_attempted": False,
        "current_input_sha256": current_sha,
        "target_stored_sha256": target_sha,
        "browser_history_candidate_count": len(report_urls),
        "browser_history_candidates_inspected": 0,
        "history_api_records_observed": 0,
        "direct_request_status_counts": {},
        "current_exact_history_record_found": False,
        "target_history_record_found": False,
        "privacy_note": (
            "No report UUID/URL, stored prompt, cookie, browser storage value, credential, "
            "unrelated browsing-history entry, or raw response is persisted."
        ),
    }

    playwright = None
    context = None
    page = None
    found_record: ExactHistoryRecord | None = None
    found_text: str | None = None
    observed_record_ids: set[str] = set()
    direct_status_counts: dict[str, int] = {}

    def inspect_payload(response_url: str, payload: Any) -> None:
        nonlocal found_record, found_text
        record_id = history_api_uuid(response_url)
        if record_id is None or not isinstance(payload, dict):
            return
        if record_id not in observed_record_ids:
            observed_record_ids.add(record_id)
            receipt["history_api_records_observed"] = len(observed_record_ids)

        current_match = match_exact_history_record(response_url, payload, current_text)
        if current_match is not None:
            receipt["current_exact_history_record_found"] = True

        for field_path, candidate in _iter_strings(payload):
            if len(candidate) < 32 or _sha256(candidate) != target_sha:
                continue
            record = match_exact_history_record(response_url, payload, candidate)
            if record is None or tuple(field_path) != record.field_path:
                continue
            found_record = record
            found_text = candidate
            return

    def collect(response: Any) -> None:
        response_url = str(getattr(response, "url", ""))
        if history_api_uuid(response_url) is None:
            return
        payload = _safe_response_json(response)
        inspect_payload(response_url, payload)

    try:
        playwright, context, page = local._launch_persistent_context(config)
        context.on("response", collect)
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        local.wait_for_authenticated_detector_input(page)

        direct_requests_available = True
        for index, report_url in enumerate(report_urls, start=1):
            record_id = report_url.rsplit("/", 1)[-1]
            api_url = f"https://web.pangram.com/api/history/{record_id}/"
            if direct_requests_available:
                try:
                    response = context.request.get(api_url, timeout=3_000)
                    status = int(getattr(response, "status", 0) or 0)
                    payload = _safe_response_json(response)
                    key = (
                        "ok_json"
                        if isinstance(payload, dict)
                        else f"non_json_or_status_{status}"
                    )
                    direct_status_counts[key] = direct_status_counts.get(key, 0) + 1
                    inspect_payload(api_url, payload)
                    if not isinstance(payload, dict):
                        direct_requests_available = False
                except Exception as exc:
                    key = f"request_failed_{type(exc).__name__}"
                    direct_status_counts[key] = direct_status_counts.get(key, 0) + 1
                    direct_requests_available = False

            if found_record is None:
                page.goto(report_url, wait_until="domcontentloaded")
                if hasattr(page, "wait_for_timeout"):
                    page.wait_for_timeout(900)
            receipt["browser_history_candidates_inspected"] = index
            if found_record is not None:
                break

        receipt["direct_request_status_counts"] = dict(sorted(direct_status_counts.items()))

        if found_record is not None and found_text is not None:
            parsed = parse_history_record_result(found_record, "")
            receipt.update(
                {
                    "status": "target_found",
                    "target_history_record_found": True,
                    "target_public_identity": found_record.public_proof(),
                    "comparison_to_current_input": difference_summary(current_text, found_text),
                    "detector": {
                        "stage": parsed.get("detector_stage"),
                        "version": parsed.get("detector_version"),
                        "headline": parsed.get("headline"),
                        "prediction_short": parsed.get("prediction_short"),
                        "summary": parsed.get("summary"),
                        "structured_result_field_path": parsed.get(
                            "structured_result_field_path"
                        ),
                    },
                }
            )
    finally:
        if context is not None:
            try:
                context.remove_listener("response", collect)
            except Exception:
                pass
        if playwright is not None and context is not None:
            local._close_local_session(playwright, context)

    _write_json(args.output, receipt)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "detector_submission_attempted": False,
                "browser_history_candidate_count": receipt["browser_history_candidate_count"],
                "browser_history_candidates_inspected": receipt[
                    "browser_history_candidates_inspected"
                ],
                "current_exact_history_record_found": receipt[
                    "current_exact_history_record_found"
                ],
                "target_history_record_found": receipt["target_history_record_found"],
                "output": str(args.output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if found_record is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
