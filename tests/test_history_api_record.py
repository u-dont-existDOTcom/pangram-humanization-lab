from __future__ import annotations

import pytest

from pangram_lab.history_api_record import (
    history_api_uuid,
    history_record_comparison_summary,
    match_exact_history_record,
    parse_history_record_result,
)


def test_history_api_url_must_be_exact_web_pangram_history_record() -> None:
    url = "https://web.pangram.com/api/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb/"
    assert history_api_uuid(url) == "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb"
    assert history_api_uuid("https://www.pangram.com/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb") is None
    assert history_api_uuid("https://web.pangram.com/api/history-list/") is None


def test_matches_only_record_containing_exact_submitted_text() -> None:
    text = "alpha beta\n\ngamma"
    url = "https://web.pangram.com/api/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb/"
    payload = {
        "uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
        "prompt": text,
        "prediction": "human",
        "prediction_prob": 0.92,
    }
    match = match_exact_history_record(url, payload, text)
    assert match is not None
    assert match.word_count == 3
    assert match.field_path == ("prompt",)
    assert match.match_mode == "exact_utf8"
    assert match.stored_text_sha256 == match.input_sha256
    assert match_exact_history_record(url, payload, text + "!") is None


def test_matches_exact_text_inside_json_encoded_response_payload() -> None:
    text = "one two three"
    url = "https://web.pangram.com/api/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb/"
    payload = {
        "uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
        "response_payload": '{"document":"one two three"}',
    }
    match = match_exact_history_record(url, payload, text)
    assert match is not None
    assert match.field_path == ("response_payload", "<decoded-json>", "document")


def test_accepts_only_bounded_transport_normalization() -> None:
    url = "https://web.pangram.com/api/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb/"

    line_endings = match_exact_history_record(
        url,
        {"uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb", "prompt": "alpha\r\nbeta"},
        "alpha\nbeta",
    )
    assert line_endings is not None
    assert line_endings.match_mode == "line_endings_normalized"

    terminal_newlines = match_exact_history_record(
        url,
        {"uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb", "prompt": "alpha\nbeta"},
        "alpha\nbeta\n",
    )
    assert terminal_newlines is not None
    assert terminal_newlines.match_mode == "terminal_newlines_normalized"

    outer_whitespace = match_exact_history_record(
        url,
        {"uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb", "prompt": "alpha\nbeta"},
        "  alpha\nbeta  ",
    )
    assert outer_whitespace is not None
    assert outer_whitespace.match_mode == "outer_whitespace_normalized"

    # Interior whitespace collapse is not an accepted identity transformation.
    assert (
        match_exact_history_record(
            url,
            {"uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb", "prompt": "alpha beta"},
            "alpha\n\nbeta",
        )
        is None
    )


def test_privacy_safe_comparison_summary_flags_but_does_not_accept_collapsed_whitespace() -> None:
    text = "alpha\n\nbeta gamma"
    payload = {
        "uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
        "prompt": "alpha beta gamma",
        "short": "do not include me",
    }
    summary = history_record_comparison_summary(payload, text)
    assert summary["authorized_word_count"] == 3
    assert len(summary["candidate_fields"]) == 1
    row = summary["candidate_fields"][0]
    assert row["field_path"] == ["prompt"]
    assert row["accepted_match_mode"] is None
    assert row["whitespace_collapsed_equal_diagnostic_only"] is True
    assert "alpha" not in str(summary)


def test_rejects_payload_uuid_mismatch_even_when_text_matches() -> None:
    text = "same text"
    url = "https://web.pangram.com/api/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb/"
    payload = {
        "uuid": "cccccccc-4444-5555-6666-dddddddddddd",
        "prompt": text,
    }
    assert match_exact_history_record(url, payload, text) is None


def test_parses_current_rendered_long_document_summary() -> None:
    text = "one two"
    url = "https://web.pangram.com/api/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb/"
    payload = {
        "uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
        "prompt": text,
        "prediction": "human",
        "prediction_prob": 0.92,
        "model_id": "pangram-4",
    }
    match = match_exact_history_record(url, payload, text)
    assert match is not None
    parsed = parse_history_record_result(
        match,
        "Overview AI 8% AI Human 92% Human Written AI-generated content appears at the start and end",
    )
    assert parsed["summary"]["fraction_ai"] == 0.08
    assert parsed["summary"]["fraction_human"] == 0.92
    assert parsed["summary_source"] == "rendered_history_report"
    assert parsed["segments"] == []
    assert parsed["history_record_identity"]["record_model_id"] == "pangram-4"
    assert parsed["history_record_identity"]["transport_match_mode"] == "exact_utf8"


def test_does_not_guess_prediction_probability_semantics() -> None:
    text = "one two"
    url = "https://web.pangram.com/api/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb/"
    payload = {
        "uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
        "prompt": text,
        "prediction": "human",
        "prediction_prob": 92,
    }
    match = match_exact_history_record(url, payload, text)
    assert match is not None
    with pytest.raises(RuntimeError, match="prediction_prob semantics"):
        parse_history_record_result(match, "no summary here")
