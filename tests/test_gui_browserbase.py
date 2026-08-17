from __future__ import annotations

import importlib.util
import json
import stat
from pathlib import Path

import pytest

import pangram_lab.gui_browserbase as gui_browserbase

from pangram_lab.gui_browserbase import (
    RUNNER_VERSION,
    BrowserbaseConfig,
    artifact_paths,
    build_complete_receipt,
    build_context_payload,
    build_session_payload,
    completed_result_exists,
    measurement_dir,
    parse_report_text,
    prepare_measurement,
    run_inputs,
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


def test_build_context_payload_uses_api_key_project_inference() -> None:
    assert build_context_payload() == {}


def test_live_view_url_prefers_fullscreen_human_control_url() -> None:
    debug_response = {
        "debuggerFullscreenUrl": "https://live.example/fullscreen",
        "debuggerUrl": "https://live.example/bordered-devtools",
        "pages": [],
        "wsUrl": "wss://live.example/socket",
    }

    assert gui_browserbase.select_live_view_url(debug_response) == "https://live.example/fullscreen"


def test_live_view_url_rejects_response_without_human_control_url() -> None:
    with pytest.raises(RuntimeError, match="Live View URL"):
        gui_browserbase.select_live_view_url({"pages": [], "wsUrl": "wss://live.example/socket"})


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
    assert not hasattr(config, "project_id")
    assert config.pangram_url == "https://www.pangram.com/"


def test_browserbase_config_bootstrap_needs_only_api_key() -> None:
    config = BrowserbaseConfig.from_env(
        {"BROWSERBASE_API_KEY": "secret"},
        require_context=False,
    )
    assert config.api_key == "secret"
    assert config.context_id is None
    assert not hasattr(config, "project_id")

    existing = BrowserbaseConfig.from_env(
        {
            "BROWSERBASE_API_KEY": "secret",
            "BROWSERBASE_CONTEXT_ID": "ctx_existing",
        },
        require_context=False,
    )
    assert existing.context_id == "ctx_existing"


def test_browserbase_config_defaults_to_authenticated_pangram_dashboard() -> None:
    config = BrowserbaseConfig.from_env(
        {"BROWSERBASE_API_KEY": "secret"},
        require_context=False,
    )

    assert config.pangram_url == "https://www.pangram.com/dashboard"


class _BodyText:
    def __init__(self, text: str) -> None:
        self._text = text

    def inner_text(self) -> str:
        return self._text


class _AuthenticationWallPage:
    def __init__(self, url: str, body: str) -> None:
        self.url = url
        self._body = _BodyText(body)

    def locator(self, selector: str) -> _BodyText:
        assert selector == "body"
        return self._body


@pytest.mark.parametrize("route", ("login", "signup"))
def test_authenticated_detector_rejects_authentication_routes(route: str) -> None:
    page = _AuthenticationWallPage(f"https://www.pangram.com/{route}", "")

    with pytest.raises(RuntimeError, match="authenticated Pangram dashboard"):
        gui_browserbase.authenticated_detector_input(page)


def test_authenticated_detector_rejects_visible_account_wall() -> None:
    page = _AuthenticationWallPage(
        "https://www.pangram.com/",
        "Sign up to gain access to the Pangram Dashboard\nCreate your account to get started",
    )

    with pytest.raises(RuntimeError, match="authenticated Pangram dashboard"):
        gui_browserbase.authenticated_detector_input(page)


class _PageContext:
    def __init__(self, pages: list[object]) -> None:
        self.pages = pages


class _TabbedPage:
    def __init__(self, url: str) -> None:
        self.url = url
        self.context: _PageContext | None = None
        self.goto_calls: list[str] = []

    def goto(self, url: str, *, wait_until: str) -> None:
        self.goto_calls.append(url)
        self.url = url


def test_dashboard_verification_prefers_authenticated_login_tab(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _TabbedPage("https://www.pangram.com/login")
    dashboard = _TabbedPage("https://www.pangram.com/dashboard/check")
    context = _PageContext([original, dashboard])
    original.context = context
    dashboard.context = context

    monkeypatch.setattr(
        gui_browserbase,
        "authenticated_detector_input",
        lambda page: object() if page is dashboard else (_ for _ in ()).throw(RuntimeError("not authenticated")),
    )

    selected = gui_browserbase.select_authenticated_dashboard_page(
        original,
        "https://www.pangram.com/dashboard",
    )

    assert selected is dashboard
    assert original.goto_calls == []


def test_dashboard_verification_navigates_original_when_no_dashboard_tab(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _TabbedPage("https://accounts.google.com/oauth")
    context = _PageContext([original])
    original.context = context
    verified: list[object] = []
    monkeypatch.setattr(gui_browserbase, "authenticated_detector_input", verified.append)

    selected = gui_browserbase.select_authenticated_dashboard_page(
        original,
        "https://www.pangram.com/dashboard",
    )

    assert selected is original
    assert original.goto_calls == ["https://www.pangram.com/dashboard"]
    assert verified == [original]


def test_browserbase_config_reuses_saved_local_context(tmp_path: Path) -> None:
    context_file = tmp_path / "browserbase-context-id"
    context_file.write_text("ctx_saved\n", encoding="utf-8")

    config = BrowserbaseConfig.from_env(
        {"BROWSERBASE_API_KEY": "secret"},
        require_context=True,
        context_id_path=context_file,
    )

    assert config.context_id == "ctx_saved"


def test_bootstrap_cli_persists_context_id_with_private_permissions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script_path = Path(__file__).parents[1] / "scripts" / "pangram_gui_browserbase.py"
    spec = importlib.util.spec_from_file_location("pangram_gui_browserbase_script", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    context_file = tmp_path / "config" / "browserbase-context-id"
    monkeypatch.setattr(module, "DEFAULT_CONTEXT_ID_PATH", context_file)
    monkeypatch.setenv("BROWSERBASE_API_KEY", "secret")
    monkeypatch.delenv("BROWSERBASE_CONTEXT_ID", raising=False)
    monkeypatch.setattr(
        module,
        "bootstrap_login",
        lambda config: {
            "context_id": "ctx_created",
            "session_id": "session_1",
            "debugger_url": "https://live.example/session",
            "verified": True,
        },
    )

    assert module.main(["bootstrap"]) == 0
    assert context_file.read_text(encoding="utf-8") == "ctx_created\n"
    assert stat.S_IMODE(context_file.stat().st_mode) == 0o600


def test_gui_workflow_defaults_to_current_exact_article_source_branch() -> None:
    workflow = (
        Path(__file__).parents[1] / ".github" / "workflows" / "pangram-gui-browserbase.yml"
    ).read_text(encoding="utf-8")

    assert "default: agent/romance-primal-crucible-gui-repair-20260817" in workflow
    assert "default: agent/romance-concept-flow-improvement-20260817" not in workflow


def test_prepare_measurement_hashes_exact_text_and_skips_completed_by_default(tmp_path: Path) -> None:
    input_path = tmp_path / "part.txt"
    input_path.write_text("one two\nthree\n", encoding="utf-8")
    output_root = tmp_path / "state"

    first = prepare_measurement(input_path, output_root=output_root, force=False)
    assert first["text"] == "one two\nthree\n"
    assert first["word_count"] == 3
    assert first["input_sha256"] == sha256_text("one two\nthree\n")
    assert first["skip"] is False

    directory = Path(first["directory"])
    directory.mkdir(parents=True)
    (directory / "result.json").write_text(
        json.dumps({"status": "complete", "runner_version": RUNNER_VERSION}),
        encoding="utf-8",
    )

    second = prepare_measurement(input_path, output_root=output_root, force=False)
    forced = prepare_measurement(input_path, output_root=output_root, force=True)
    assert second["skip"] is True
    assert forced["skip"] is False


def test_run_inputs_refuses_automatic_repeat_after_ambiguous_submission(tmp_path: Path) -> None:
    input_path = tmp_path / "smoke.txt"
    input_path.write_text("An exact smoke boundary.\n", encoding="utf-8")
    output_root = tmp_path / "state"
    first = prepare_measurement(input_path, output_root=output_root, force=False)
    directory = Path(first["directory"])
    directory.mkdir(parents=True)
    (directory / "failure.json").write_text(
        json.dumps(
            {
                "status": "failed",
                "runner_version": RUNNER_VERSION,
                "detector_submission_attempted": True,
            }
        ),
        encoding="utf-8",
    )
    config = BrowserbaseConfig(api_key="secret", context_id="ctx_saved")

    with pytest.raises(RuntimeError, match="refusing to repeat.*ambiguous"):
        run_inputs(config, [input_path], output_root=output_root)


def test_artifact_paths_are_stable_and_explicit(tmp_path: Path) -> None:
    paths = artifact_paths(tmp_path)
    assert paths == {
        "result": tmp_path / "result.json",
        "body": tmp_path / "report-body.txt",
        "pdf": tmp_path / "report.pdf",
        "failure": tmp_path / "failure.json",
        "failure_screenshot": tmp_path / "failure.png",
    }


def test_complete_receipt_records_pdf_provenance_and_session() -> None:
    parsed = {
        "summary": {"fraction_human": 0.944},
        "segments": [{"label": "Human Written", "word_count": 10, "confidence": "High", "text": "x"}],
    }
    receipt = build_complete_receipt(
        input_path="work/part.txt",
        input_sha256="a" * 64,
        word_count=10,
        session_id="sess_1",
        debugger_url="https://debug.example/session",
        report_url="https://www.pangram.com/report/123",
        pdf_provenance="native_pangram_download",
        parsed=parsed,
    )
    assert receipt["status"] == "complete"
    assert receipt["runner_version"] == RUNNER_VERSION
    assert receipt["input_sha256"] == "a" * 64
    assert receipt["word_count"] == 10
    assert receipt["browserbase_session_id"] == "sess_1"
    assert receipt["browserbase_debugger_url"] == "https://debug.example/session"
    assert receipt["report_url"] == "https://www.pangram.com/report/123"
    assert receipt["pdf_provenance"] == "native_pangram_download"
    assert receipt["parsed"] == parsed
