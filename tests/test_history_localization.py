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


def test_binds_complete_contiguous_overall_windows_even_when_pangram_word_count_differs() -> None:
    text = "alpha beta.\n\ngamma delta epsilon.\n\nzeta eta."
    normalized = text.replace("\n", "")
    gamma = normalized.index("gamma")
    zeta = normalized.index("zeta")
    payload = {
        "uuid": UUID,
        "prompt": text,
        "model_id": "pangram-4",
        "response": {
            "overall": {
                "windows": [
                    {
                        "text": "alpha beta.",
                        "start_index": 0,
                        "end_index": gamma,
                        "word_count": 999,
                        "window_index": 0,
                        "label": "Human",
                    },
                    {
                        "text": "gamma delta",
                        "start_index": gamma,
                        "end_index": zeta,
                        "word_count": 777,
                        "window_index": 1,
                        "label": "AI-Generated",
                    },
                    {
                        "text": "zeta eta.",
                        "start_index": zeta,
                        "end_index": len(normalized),
                        "word_count": 555,
                        "window_index": 2,
                        "label": "Human",
                    },
                ]
            }
        },
    }
    record = match_exact_history_record(URL, payload, text)
    assert record is not None
    result = localize_history_record(record, text)
    assert result["schema_version"] == 3
    assert result["validated_full_overall_window_count"] == 3
    windows = [
        span
        for span in result["spans"]
        if any(
            evidence["binding_mode"]
            == "pangram_linebreak_removed_contiguous_windows+all_previews"
            for evidence in span["evidence"]
        )
    ]
    assert len(windows) == 3
    middle = windows[1]
    raw = text[middle["char_start_0"] : middle["char_end_0_exclusive"]]
    assert raw == "gamma delta epsilon.\n\n"
    assert middle["word_count"] == 3
    assert middle["evidence"][0]["scalar_metadata"]["word_count"] == 777
    assert raw not in json.dumps(result)


def test_collection_binding_resolves_repeated_previews_without_uniqueness() -> None:
    text = "repeat here.\n\nmiddle words.\n\nrepeat here. final words.\n\nend."
    normalized = text.replace("\n", "")
    middle = normalized.index("middle")
    second_repeat = normalized.rindex("repeat here.")
    payload = {
        "uuid": UUID,
        "prompt": text,
        "model_id": "pangram-4",
        "response": {
            "overall": {
                "windows": [
                    {
                        "text": "repeat here.",
                        "start_index": 0,
                        "end_index": middle,
                        "window_index": 0,
                        "label": "Human",
                    },
                    {
                        "text": "middle words.",
                        "start_index": middle,
                        "end_index": second_repeat,
                        "window_index": 1,
                        "label": "Human",
                    },
                    {
                        "text": "repeat here.",
                        "start_index": second_repeat,
                        "end_index": len(normalized),
                        "window_index": 2,
                        "label": "AI-Generated",
                    },
                ]
            }
        },
    }
    record = match_exact_history_record(URL, payload, text)
    assert record is not None
    result = localize_history_record(record, text)
    assert result["validated_full_overall_window_count"] == 3
    final = result["spans"][-1]
    assert text[final["char_start_0"] : final["char_end_0_exclusive"]] == "repeat here. final words.\n\nend."
    assert final["evidence"][0]["scalar_metadata"]["label"] == "AI-Generated"


def test_collection_binding_fails_closed_if_any_preview_does_not_match_mapped_start() -> None:
    text = "alpha beta.\n\ngamma delta epsilon.\n\nzeta eta."
    normalized = text.replace("\n", "")
    gamma = normalized.index("gamma")
    zeta = normalized.index("zeta")
    payload = {
        "uuid": UUID,
        "prompt": text,
        "model_id": "pangram-4",
        "response": {
            "overall": {
                "windows": [
                    {"text": "alpha beta.", "start_index": 0, "end_index": gamma, "window_index": 0},
                    {"text": "WRONG PREVIEW", "start_index": gamma, "end_index": zeta, "window_index": 1},
                    {"text": "zeta eta.", "start_index": zeta, "end_index": len(normalized), "window_index": 2},
                ]
            }
        },
    }
    record = match_exact_history_record(URL, payload, text)
    assert record is not None
    result = localize_history_record(record, text)
    assert result["validated_full_overall_window_count"] == 0
    assert not any(
        evidence.get("binding_mode") == "pangram_linebreak_removed_contiguous_windows+all_previews"
        for span in result["spans"]
        for evidence in span["evidence"]
    )


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
