from __future__ import annotations

import json

import pytest

from pangram_lab.history_localization_runner import (
    _failure_receipt,
    _request_direct_history_api_record,
    _validated_report_url,
)


REPORT = "https://www.pangram.com/history/58db9b2b-9a3d-43cf-8970-2e2b7410a0e8"


def test_validated_report_url_accepts_only_pangram_history_route_and_strips_query() -> None:
    assert _validated_report_url(REPORT + "?private=yes") == REPORT
    with pytest.raises(ValueError):
        _validated_report_url("https://example.com/history/58db9b2b-9a3d-43cf-8970-2e2b7410a0e8")
    with pytest.raises(ValueError):
        _validated_report_url("https://www.pangram.com/dashboard")


def test_failure_receipt_omits_private_url_and_raw_exception_text() -> None:
    secretish = "private report " + REPORT
    receipt = _failure_receipt(
        item={"input_sha256": "a" * 64, "word_count": 100},
        stage="direct_stored_report",
        exc=RuntimeError(secretish),
        history_candidate_count=3,
        exact_record_found=False,
        direct_report_requested=True,
    )
    rendered = json.dumps(receipt)
    assert receipt["detector_submission_attempted"] is False
    assert receipt["stage"] == "direct_stored_report"
    assert receipt["error_type"] == "RuntimeError"
    assert REPORT not in rendered
    assert secretish not in rendered


def test_direct_history_api_request_is_read_only_and_cache_resistant() -> None:
    calls = []

    class Page:
        def evaluate(self, script, argument):
            calls.append((script, argument))

    _request_direct_history_api_record(Page(), REPORT)

    assert len(calls) == 1
    script, argument = calls[0]
    assert 'method: "GET"' in script
    assert 'cache: "no-store"' in script
    assert "response.json()" in script
    assert argument == {
        "url": "https://web.pangram.com/api/history/58db9b2b-9a3d-43cf-8970-2e2b7410a0e8/"
    }
