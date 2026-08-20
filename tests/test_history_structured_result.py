from __future__ import annotations

import pytest

from pangram_lab.history_api_record import (
    match_exact_history_record,
    parse_history_record_result,
    structured_history_result_shape,
)


URL = "https://web.pangram.com/api/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb/"
UUID = "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb"


def _record(payload: dict, text: str = "one two three"):
    match = match_exact_history_record(URL, {"uuid": UUID, "prompt": text, **payload}, text)
    assert match is not None
    return match


def test_prefers_explicit_structured_overall_result_when_rendered_summary_is_absent() -> None:
    record = _record(
        {
            "model_id": "pangram-4",
            "response": {
                "overall": {
                    "stage": "STAGE_SUCCESS",
                    "version": "4.0",
                    "fraction_ai": 0.08,
                    "fraction_ai_assisted": 0.02,
                    "fraction_human": 0.90,
                    "headline": "Human Written",
                    "prediction_short": "Human",
                    "text": "preview only",
                },
                "in_page": {
                    "fraction_ai": 1.0,
                    "fraction_ai_assisted": 0.0,
                    "fraction_human": 0.0,
                },
            },
        }
    )
    parsed = parse_history_record_result(record, "rendered page has no percentage summary")
    assert parsed["summary_source"] == "stored_history_structured_result"
    assert parsed["structured_result_field_path"] == ["response", "overall"]
    assert parsed["summary"]["fraction_ai"] == 0.08
    assert parsed["summary"]["fraction_ai_assisted"] == 0.02
    assert parsed["summary"]["fraction_human"] == 0.90
    assert parsed["detector_stage"] == "STAGE_SUCCESS"
    assert parsed["detector_version"] == "4.0"


def test_accepts_explicit_moderate_and_light_assistance_when_aggregate_is_absent() -> None:
    record = _record(
        {
            "model_id": "pangram-4",
            "response": {
                "overall": {
                    "stage": "STAGE_SUCCESS",
                    "version": "4.0",
                    "fraction_ai": 0.10,
                    "fraction_moderately_ai_assisted": 0.05,
                    "fraction_lightly_ai_assisted": 0.05,
                    "fraction_human": 0.80,
                }
            },
        }
    )
    parsed = parse_history_record_result(record, "")
    assert parsed["summary"]["fraction_ai_assisted"] == 0.10
    assert parsed["summary"]["fraction_moderately_ai_assisted"] == 0.05
    assert parsed["summary"]["fraction_lightly_ai_assisted"] == 0.05


def test_rejects_wrong_version_even_when_fraction_fields_exist() -> None:
    record = _record(
        {
            "model_id": "pangram-4",
            "response": {
                "overall": {
                    "stage": "STAGE_SUCCESS",
                    "version": "3.3.2",
                    "fraction_ai": 0.08,
                    "fraction_ai_assisted": 0.02,
                    "fraction_human": 0.90,
                }
            },
        }
    )
    with pytest.raises(RuntimeError, match="canonical structured fractions"):
        parse_history_record_result(record, "no rendered summary")


def test_rejects_prediction_probability_as_structured_fraction_substitute() -> None:
    record = _record(
        {
            "model_id": "pangram-4",
            "prediction": "human",
            "prediction_prob": 0.92,
            "response": {
                "overall": {
                    "stage": "STAGE_SUCCESS",
                    "version": "4.0",
                    "prediction": "human",
                    "prediction_prob": 0.92,
                }
            },
        }
    )
    with pytest.raises(RuntimeError, match="prediction_prob semantics"):
        parse_history_record_result(record, "no rendered summary")


def test_safe_shape_excludes_article_text_windows_and_uuid() -> None:
    record = _record(
        {
            "model_id": "pangram-4",
            "response": {
                "overall": {
                    "stage": "STAGE_SUCCESS",
                    "version": "4.0",
                    "fraction_ai": 0.08,
                    "fraction_ai_assisted": 0.02,
                    "fraction_human": 0.90,
                    "text": "SECRET ARTICLE TEXT",
                    "windows": [{"text": "SECRET WINDOW"}],
                }
            },
        }
    )
    shape = structured_history_result_shape(record)
    rendered = str(shape)
    assert "SECRET ARTICLE TEXT" not in rendered
    assert "SECRET WINDOW" not in rendered
    assert UUID not in rendered
    assert "fraction_ai" in rendered
    assert "windows" in rendered  # key names are safe; values are not copied.
