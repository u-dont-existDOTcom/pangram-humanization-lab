from __future__ import annotations

from pangram_lab.history_api_record import (
    history_api_uuid,
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
    assert parsed["segments"] == []
    assert parsed["history_record_identity"]["record_model_id"] == "pangram-4"


def test_prediction_probability_is_bounded_fallback() -> None:
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
    parsed = parse_history_record_result(match, "no summary here")
    assert parsed["summary_source"] == "history_api_prediction"
    assert parsed["summary"]["fraction_human"] == 0.92
    assert parsed["summary"]["fraction_ai"] == 0.08
