from __future__ import annotations

import json
from pathlib import Path

import pytest

from pangram_lab.gui_browserbase import (
    RUNNER_VERSION,
    BrowserbaseConfig,
    build_context_payload,
    build_session_payload,
    completed_result_exists,
    measurement_dir,
    parse_report_text,
    sha256_text,
)


def test_report_parser_extracts_summary_and_segment_blocks() -> None:
    body = """
    AI Detection Report for sample
    Summary
    Authorship Breakdown
    5.6 % of the document AI Generated
    0 % of the document Moderately AI Assisted
    0 % of the document Lightly AI Assisted
    94.4 % of the document Human Written
    Analyzed Text
    Human Written | 836 Words | High Confidence
    Opening human text.
    Fully AI Generated | 413 Words | High Confidence
    That conversation is already part of making love. What do you actually want?
    Human Written | 1738 Words | High Confidence
    Try to convince her to abort when she thinks abortion is killing her child?
    """

    parsed = parse_report_text(body)

    assert parsed["summary"] == {
        "fraction_ai": pytest.approx(0.056),
        "fraction_moderately_ai_assisted": pytest.approx(0.0),
        "fraction_lightly_ai_assisted": pytest.approx(0.0),
        "fraction_human": pytest.approx(0.944),
    }
    assert parsed["segments"] == [
        {
            "label": "Human Written",
            "word_count": 836,
            "confidence": "High",
            "text": "Opening human text.",
        },
        {
            "label": "Fully AI Generated",
            "word_count": 413,
            "confidence": "High",
            "text": "That conversation is already part of making love. What do you actually want?",
        },
        {
            "label": "Human Written",
            "word_count": 1738,
            "confidence": "High",
            "text": "Try to convince her to abort when she thinks abortion is killing her child?",
        },
    ]


def test_report_parser_uses_null_for_missing_confidence_or_summary_fields() -> None:
    body = """
    Analyzed Text
    Fully AI Generated 43 Words
    A partner can comfort you, teach you, protect you, or carry more for a while.
    """
    parsed = parse_report_text(body)
    assert parsed["summary"] == {
        "fraction_ai": None,
        "fraction_moderately_ai_assisted": None,
        "fraction_lightly_ai_assisted": None,
        "fraction_human": None,
    }
    assert parsed["segments"] == [
        {
            "label": "Fully AI Generated",
            "word_count": 43,
            "confidence": None,
            "text": "A partner can comfort you, teach you, protect you, or carry more for a while.",
        }
    ]


def test_measurement_identity_is_content_addressed(tmp_path: Path) -> None:
    text = "Exact Pangram GUI boundary.\n"
    digest = sha256_text(text)
    path = measurement_dir(tmp_path, digest)
    assert path == tmp_path / "pangram-4" / digest
    assert len(digest) == 64
    assert digest == sha256_text(text)
    assert digest != sha256_text(text + "x")


def test_completed_result_exists_requires_matching_runner_and_status(tmp_path: Path) -> None:
    digest = sha256_text("boundary")
    directory = measurement_dir(tmp_path, digest)
    directory.mkdir(parents=True)
    receipt = directory / "result.json"

    assert completed_result_exists(tmp_path, digest) is False

    receipt.write_text(json.dumps({"status": "failed", "runner_version": RUNNER_VERSION}), encoding="utf-8")
    assert completed_result_exists(tmp_path, digest) is False

    receipt.write_text(json.dumps({"status": "complete", "runner_version": "old"}), encoding="utf-8")
    assert completed_result_exists(tmp_path, digest) is False

    receipt.write_text(json.dumps({"status": "complete", "runner_version": RUNNER_VERSION}), encoding="utf-8")
    assert completed_result_exists(tmp_path, digest) is True


def test_build_session_payload_binds_persistent_context_and_metadata() -> None:
    payload = build_session_payload(
        "ctx_123",
        persist=True,
        keep_alive=False,
        timeout=1800,
        user_metadata={"inputSha256": "abc", "task": "pangram-gui"},
    )
    assert payload == {
        "browserSettings": {"context": {"id": "ctx_123", "persist": True}},
        "keepAlive": False,
        "timeout": 1800,
        "userMetadata": {"inputSha256": "abc", "task": "pangram-gui"},
    }


def test_build_session_payload_rejects_unsafe_timeout() -> None:
    with pytest.raises(ValueError, match="timeout"):
        build_session_payload(
            "ctx_123",
            persist=True,
            keep_alive=False,
            timeout=30,
            user_metadata={},
        )


def test_build_context_payload_requires_project_id() -> None:
    assert build_context_payload("proj_123") == {"projectId": "proj_123"}
    with pytest.raises(ValueError, match="project_id"):
        build_context_payload("  ")


def test_browserbase_config_fails_closed_for_unattended_run() -> None:
    with pytest.raises(RuntimeError, match="BROWSERBASE_API_KEY"):
        BrowserbaseConfig.from_env({}, require_context=True)

    with pytest.raises(RuntimeError, match="BROWSERBASE_CONTEXT_ID"):
        BrowserbaseConfig.from_env({"BROWSERBASE_API_KEY": "secret"}, require_context=True)

    config = BrowserbaseConfig.from_env(
        {
            "BROWSERBASE_API_KEY": "secret",
            "BROWSERBASE_CONTEXT_ID": "ctx_123",
            "PANGRAM_GUI_URL": "https://www.pangram.com/",
        },
        require_context=True,
    )
    assert config.api_key == "secret"
    assert config.context_id == "ctx_123"
    assert config.project_id is None
    assert config.pangram_url == "https://www.pangram.com/"


def test_browserbase_config_bootstrap_requires_project_only_when_context_missing() -> None:
    config = BrowserbaseConfig.from_env(
        {
            "BROWSERBASE_API_KEY": "secret",
            "BROWSERBASE_CONTEXT_ID": "ctx_existing",
        },
        require_context=False,
    )
    assert config.context_id == "ctx_existing"

    with pytest.raises(RuntimeError, match="BROWSERBASE_PROJECT_ID"):
        BrowserbaseConfig.from_env(
            {"BROWSERBASE_API_KEY": "secret"},
            require_context=False,
            require_project_if_context_missing=True,
        )
