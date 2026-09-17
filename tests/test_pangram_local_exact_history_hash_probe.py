from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "pangram_local_exact_history_hash_probe.py"
SPEC = importlib.util.spec_from_file_location("pangram_local_exact_history_hash_probe", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_difference_summary_reports_only_inserted_whitespace() -> None:
    result = MODULE.difference_summary("alpha\n\nbeta\n", "alpha\n\n\nbeta\n\n")

    assert result["whitespace_collapsed_equal"] is True
    assert result["non_whitespace_sequence_equal"] is True
    assert result["stored_utf8_bytes"] - result["current_utf8_bytes"] == 2
    assert result["difference_operation_count"] == 2
    assert all(
        operation["stored_whitespace_escape"] == "\\n"
        for operation in result["difference_operations"]
    )
    assert all(
        operation["current_whitespace_escape"] == ""
        for operation in result["difference_operations"]
    )


def test_canonical_report_url_rejects_non_pangram_and_non_uuid_routes() -> None:
    assert MODULE._canonical_report_url("https://example.com/history/a") is None
    assert MODULE._canonical_report_url("https://www.pangram.com/history/not-a-uuid") is None
    assert MODULE._canonical_report_url(
        "https://www.pangram.com/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb?private=x"
    ) == "https://www.pangram.com/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb"
