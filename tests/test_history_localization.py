from __future__ import annotations

import json

from pangram_lab.history_api_record import match_exact_history_record
from pangram_lab.history_localization import localize_history_record


URL = "https://web.pangram.com/api/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb/"
UUID = "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb"
TEXT = "alpha beta gamma. delta epsilon zeta. eta theta iota."


def _record(payload: dict):
    record = match_exact_history_record(URL, {"uuid": UUID, "prompt": TEXT, **payload}, TEXT)
    assert record is not None
    return record


def test_localizes_unique_overall_window_without_persisting_text() -> None:
    window_text = "delta epsilon zeta."
    record = _record(
        {
            "model_id": "pangram-4",
            "response": {
                "overall": {
                    "stage": "STAGE_SUCCESS",
                    "version": "4.0",
                    "windows": [
                        {
                            "text": window_text,
                            "prediction": "AI",
                            "score": 0.91,
                        }
                    ],
                }
            },
        }
    )
    result = localize_history_record(record, TEXT)
    assert result["status"] == "localized"
    assert result["localized_span_count"] == 1
    span = result["spans"][0]
    assert TEXT[span["char_start_0"] : span["char_end_0_exclusive"]] == window_text
    assert span["word_count"] == 3
    assert span["evidence"][0]["scalar_metadata"]["prediction"] == "AI"
    rendered = json.dumps(result, ensure_ascii=False)
    assert window_text not in rendered
    assert UUID not in rendered


def test_binds_complete_window_from_linebreak_removed_indices_and_short_preview() -> None:
    text = "alpha beta.\n\ngamma delta epsilon.\n\nzeta eta."
    normalized = text.replace("\n", "")
    start = normalized.index("gamma")
    end = normalized.index("zeta")
    payload = {
        "uuid": UUID,
        "prompt": text,
        "model_id": "pangram-4",
        "response": {
            "overall": {
                "windows": [
                    {
                        "text": "gamma delta",
                        "start_index": start,
                        "end_index": end,
                        "word_count": 3,
                        "window_index": 1,
                        "label": "AI-Generated",
                        "ai_likelihood": 0.81,
                    }
                ]
            }
        },
    }
    record = match_exact_history_record(URL, payload, text)
    assert record is not None
    result = localize_history_record(record, text)
    assert result["schema_version"] == 2
    assert result["localized_span_count"] == 1
    span = result["spans"][0]
    raw = text[span["char_start_0"] : span["char_end_0_exclusive"]]
    assert raw == "gamma delta epsilon.\n\n"
    assert span["word_count"] == 3
    assert len(raw) > len("gamma delta")
    assert span["evidence"][0]["binding_mode"].startswith("pangram_linebreak_removed_indices")
    assert span["evidence"][0]["scalar_metadata"]["label"] == "AI-Generated"
    assert raw not in json.dumps(result)


def test_index_binding_resolves_repeated_preview_without_guessing() -> None:
    text = "repeat here.\n\nmiddle words.\n\nrepeat here. final words.\n\nend."
    normalized = text.replace("\n", "")
    second_start = normalized.rindex("repeat here.")
    end = normalized.index("end.")
    payload = {
        "uuid": UUID,
        "prompt": text,
        "model_id": "pangram-4",
        "response": {
            "overall": {
                "windows": [
                    {
                        "text": "repeat here.",
                        "start_index": second_start,
                        "end_index": end,
                        "word_count": 4,
                        "window_index": 2,
                        "label": "AI-Generated",
                    }
                ]
            }
        },
    }
    record = match_exact_history_record(URL, payload, text)
    assert record is not None
    result = localize_history_record(record, text)
    assert result["localized_span_count"] == 1
    span = result["spans"][0]
    assert text[span["char_start_0"] : span["char_end_0_exclusive"]] == "repeat here. final words.\n\n"
    assert span["word_count"] == 4


def test_index_binding_fails_closed_when_word_count_does_not_validate() -> None:
    text = "alpha beta.\n\ngamma delta epsilon.\n\nzeta eta."
    normalized = text.replace("\n", "")
    payload = {
        "uuid": UUID,
        "prompt": text,
        "model_id": "pangram-4",
        "response": {
            "overall": {
                "windows": [
                    {
                        "text": "gamma delta",
                        "start_index": normalized.index("gamma"),
                        "end_index": normalized.index("zeta"),
                        "word_count": 999,
                        "window_index": 1,
                        "label": "AI-Generated",
                    }
                ]
            }
        },
    }
    record = match_exact_history_record(URL, payload, text)
    assert record is not None
    result = localize_history_record(record, text)
    # The preview is unique, so the conservative fallback may localize the
    # preview itself, but it must not claim the complete indexed window.
    assert result["localized_span_count"] == 1
    evidence = result["spans"][0]["evidence"][0]
    assert evidence["binding_mode"] == "unique_exact_substring"
    assert result["spans"][0]["word_count"] == 2


def test_prefers_valid_explicit_offsets_when_text_repeats() -> None:
    text = "repeat here. other words. repeat here."
    payload = {
        "uuid": UUID,
        "prompt": text,
        "model_id": "pangram-4",
        "response": {
            "in_page": {
                "highlights": [
                    {
                        "text": "repeat here.",
                        "start": 26,
                        "end": 38,
                        "classification": "AI",
                    }
                ]
            }
        },
    }
    record = match_exact_history_record(URL, payload, text)
    assert record is not None
    result = localize_history_record(record, text)
    assert result["localized_span_count"] == 1
    span = result["spans"][0]
    assert span["char_start_0"] == 26
    assert span["char_end_0_exclusive"] == 38


def test_rejects_repeated_text_without_verified_offsets() -> None:
    text = "repeat here. other words. repeat here."
    payload = {
        "uuid": UUID,
        "prompt": text,
        "model_id": "pangram-4",
        "response": {
            "overall": {
                "windows": [
                    {
                        "text": "repeat here.",
                        "prediction": "AI",
                    }
                ]
            }
        },
    }
    record = match_exact_history_record(URL, payload, text)
    assert record is not None
    result = localize_history_record(record, text)
    assert result["status"] == "no_bound_spans"
    assert result["localized_span_count"] == 0
    assert result["unresolved_candidate_shapes"]
    assert "repeat here." not in json.dumps(result)


def test_deduplicates_same_span_from_overall_and_in_page() -> None:
    window_text = "alpha beta gamma."
    window = {"text": window_text, "prediction": "AI", "score": 0.75}
    record = _record(
        {
            "model_id": "pangram-4",
            "response": {
                "overall": {"windows": [window]},
                "in_page": {"windows": [window]},
            },
        }
    )
    result = localize_history_record(record, TEXT)
    assert result["localized_span_count"] == 1
    assert len(result["spans"][0]["evidence"]) == 2
    roots = {item["root"] for item in result["spans"][0]["evidence"]}
    assert roots == {"response.overall", "response.in_page"}


def test_response_payload_json_string_is_supported() -> None:
    record = _record(
        {
            "model_id": "pangram-4",
            "response_payload": json.dumps(
                {
                    "overall": {
                        "windows": [
                            {
                                "text": "eta theta iota.",
                                "fraction_ai": 0.82,
                            }
                        ]
                    }
                }
            ),
        }
    )
    result = localize_history_record(record, TEXT)
    assert result["localized_span_count"] == 1
    assert result["spans"][0]["evidence"][0]["root"] == "response_payload.overall"
