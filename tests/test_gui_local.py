from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pangram_lab import gui_browserbase as gui_core
from pangram_lab import gui_local
from pangram_lab.gui_local import LocalPlaywrightConfig


def _config(tmp_path: Path, *, headed: bool = True) -> LocalPlaywrightConfig:
    return LocalPlaywrightConfig(
        profile_dir=tmp_path / "pangram-profile",
        browser_executable=Path("/bin/true"),
        headed=headed,
    )


def test_profile_guard_rejects_ordinary_browser_profiles(tmp_path: Path) -> None:
    ordinary = tmp_path / ".config" / "BraveSoftware" / "Brave-Browser" / "Default"

    with pytest.raises(RuntimeError, match="ordinary browser profile"):
        gui_local.validate_profile_dir(ordinary, home=tmp_path)

    assert gui_local.validate_profile_dir(
        ordinary,
        home=tmp_path,
        allow_ordinary_profile=True,
    ) == ordinary.resolve()


def test_profile_guard_rejects_profile_inside_git_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)

    with pytest.raises(RuntimeError, match="inside a Git repository"):
        gui_local.validate_profile_dir(repo / "browser-profile", home=tmp_path)


def test_profile_guard_rejects_broad_paths(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="unsafe Pangram profile"):
        gui_local.validate_profile_dir(tmp_path, home=tmp_path)


def test_local_config_is_headed_by_default_and_discovers_explicit_browser(
    tmp_path: Path,
) -> None:
    browser = tmp_path / "brave"
    browser.write_text("#!/bin/sh\n", encoding="utf-8")
    browser.chmod(0o755)

    config = LocalPlaywrightConfig.from_env(
        {},
        profile_dir=tmp_path / "profile",
        browser_executable=browser,
    )

    assert config.headed is True
    assert config.profile_dir == (tmp_path / "profile").resolve()
    assert config.browser_executable == browser.resolve()


def test_persistent_launch_uses_dedicated_profile_headed_and_closes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launch_options: dict[str, object] = {}

    class FakePage:
        pass

    class FakeContext:
        def __init__(self) -> None:
            self.pages = [FakePage()]
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class FakeChromium:
        def launch_persistent_context(self, **kwargs: object) -> FakeContext:
            launch_options.update(kwargs)
            return context

    class FakePlaywright:
        def __init__(self) -> None:
            self.chromium = FakeChromium()
            self.stopped = False

        def stop(self) -> None:
            self.stopped = True

    class FakeStarter:
        def start(self) -> FakePlaywright:
            return playwright

    context = FakeContext()
    playwright = FakePlaywright()
    monkeypatch.setattr(gui_local.gui_core, "_load_playwright", lambda: FakeStarter)

    active_playwright, active_context, page = gui_local._launch_persistent_context(
        _config(tmp_path)
    )
    gui_local._close_local_session(active_playwright, active_context)

    assert page is context.pages[0]
    assert launch_options["user_data_dir"] == str((tmp_path / "pangram-profile").resolve())
    assert launch_options["executable_path"] == "/bin/true"
    assert launch_options["headless"] is False
    assert launch_options["no_viewport"] is True
    assert launch_options["args"] == ["--start-maximized"]
    assert context.closed is True
    assert playwright.stopped is True


def test_verify_is_read_only_and_closes_on_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class Field:
        def is_editable(self) -> bool:
            calls.append("is_editable")
            return True

        def fill(self, text: str) -> None:
            raise AssertionError("verify must not fill detector text")

    class Page:
        url = "about:blank"

        def goto(self, url: str, *, wait_until: str) -> None:
            calls.append("goto")
            self.url = url

    class Context:
        def close(self) -> None:
            calls.append("close")

    class Playwright:
        def stop(self) -> None:
            calls.append("stop")

    page = Page()
    monkeypatch.setattr(
        gui_local,
        "_launch_persistent_context",
        lambda config: (Playwright(), Context(), page),
    )
    monkeypatch.setattr(gui_local.gui_core, "authenticated_detector_input", lambda candidate: Field())
    monkeypatch.setattr(
        gui_local.gui_core,
        "detection_button",
        lambda candidate: (_ for _ in ()).throw(AssertionError("verify must not submit")),
    )

    result = gui_local.verify_login_persistence(_config(tmp_path), print_fn=lambda message: None)

    assert result["verified"] is True
    assert result["submitted"] is False
    assert calls == ["goto", "is_editable", "close", "stop"]


def test_verify_closes_on_authentication_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class Page:
        def goto(self, url: str, *, wait_until: str) -> None:
            calls.append("goto")

    class Context:
        def close(self) -> None:
            calls.append("close")

    class Playwright:
        def stop(self) -> None:
            calls.append("stop")

    monkeypatch.setattr(
        gui_local,
        "_launch_persistent_context",
        lambda config: (Playwright(), Context(), Page()),
    )
    monkeypatch.setattr(
        gui_local.gui_core,
        "authenticated_detector_input",
        lambda page: (_ for _ in ()).throw(RuntimeError("login expired")),
    )

    with pytest.raises(RuntimeError, match="login expired"):
        gui_local.verify_login_persistence(_config(tmp_path), print_fn=lambda message: None)

    assert calls == ["goto", "close", "stop"]


class _Field:
    def __init__(self) -> None:
        self.filled: list[str] = []

    def fill(self, text: str) -> None:
        self.filled.append(text)


class _Button:
    def __init__(self, error: Exception | None = None) -> None:
        self.clicks = 0
        self.error = error

    def click(self) -> None:
        self.clicks += 1
        if self.error is not None:
            raise self.error


class _Body:
    def __init__(self, text: str) -> None:
        self.text = text

    def inner_text(self) -> str:
        return self.text


class _Page:
    def __init__(self, body: str) -> None:
        self.url = "about:blank"
        self.body = body
        self.goto_calls: list[str] = []

    def goto(self, url: str, *, wait_until: str) -> None:
        self.goto_calls.append(url)
        self.url = url

    def locator(self, selector: str) -> _Body:
        assert selector == "body"
        return _Body(self.body)

    def screenshot(self, *, path: str, full_page: bool) -> None:
        Path(path).write_bytes(b"png")


class _Context:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _Playwright:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


def _install_successful_measurement_fakes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    body: str,
) -> tuple[_Field, _Button, _Context, _Playwright, list[int]]:
    field = _Field()
    button = _Button()
    context = _Context()
    playwright = _Playwright()
    page = _Page(body)
    launches: list[int] = []

    def launch(config: object) -> tuple[_Playwright, _Context, _Page]:
        launches.append(1)
        return playwright, context, page

    monkeypatch.setattr(gui_local, "_launch_persistent_context", launch)
    monkeypatch.setattr(gui_local.gui_core, "authenticated_detector_input", lambda candidate: field)
    monkeypatch.setattr(gui_local.gui_core, "detection_button", lambda candidate: button)
    monkeypatch.setattr(gui_local.gui_core, "wait_for_report", lambda page, timeout_ms: None)

    def capture(candidate: object, path: Path) -> str:
        path.write_bytes(b"%PDF-local")
        return "local_cdp_print_fallback"

    monkeypatch.setattr(gui_local, "capture_report_pdf", capture)
    return field, button, context, playwright, launches


def test_local_run_writes_transport_provenance_and_reuses_shared_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "part.txt"
    input_path.write_text("one two three", encoding="utf-8")
    output_root = tmp_path / "runs"
    body = (
        "Pangram 4.0\nAnalyzed Text\n"
        "Human Written | 3 Words | High Confidence\n"
        "one two three"
    )
    field, button, context, playwright, launches = _install_successful_measurement_fakes(
        monkeypatch,
        tmp_path,
        body=body,
    )
    persisted: list[tuple[Path, dict[str, object]]] = []

    results = gui_local.run_inputs(
        _config(tmp_path),
        [input_path],
        output_root=output_root,
        evidence_callback=lambda directory, receipt: persisted.append((directory, dict(receipt))),
        print_fn=lambda message: None,
    )

    result = results[0]
    assert result["status"] == "complete"
    assert result["transport"] == "local_playwright"
    assert result["transport_runner_version"] == gui_local.LOCAL_RUNNER_VERSION
    assert result["runner_version"] == gui_core.RUNNER_VERSION
    assert result["detector_version"] == "4.0"
    assert result["report_layout"] == "segmented_report"
    assert field.filled == ["one two three"]
    assert button.clicks == 1
    assert context.closed is True
    assert playwright.stopped is True
    assert [receipt[1]["status"] for receipt in persisted] == ["reserved", "complete"]

    digest = gui_core.sha256_text("one two three")
    result_path = gui_core.measurement_dir(output_root, digest) / "result.json"
    stored = json.loads(result_path.read_text(encoding="utf-8"))
    assert stored["transport"] == "local_playwright"

    cached = gui_local.run_inputs(
        _config(tmp_path),
        [input_path],
        output_root=output_root,
        print_fn=lambda message: None,
    )
    assert cached == [
        {
            "status": "cached",
            "transport": "local_playwright",
            "input_path": str(input_path),
            "input_sha256": digest,
            "word_count": 3,
            "directory": str(gui_core.measurement_dir(output_root, digest)),
        }
    ]
    assert launches == [1]


def test_local_run_prefers_exact_structured_history_record_over_legacy_segments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "part.txt"
    input_path.write_text("one two three", encoding="utf-8")
    output_root = tmp_path / "runs"
    uuid = "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb"
    page = _Page("Overview without legacy analyzed segments")
    field = _Field()
    button = _Button()
    playwright = _Playwright()

    class Response:
        status = 200
        headers = {"content-type": "application/json"}

        def __init__(self, value: object) -> None:
            self.value = value

        def json(self) -> object:
            return self.value

    class Request:
        def get(self, url: str, *, timeout: int) -> Response:
            if url.endswith("/api/history-list/"):
                return Response(
                    {
                        "results": [
                            {
                                "uuid": uuid,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ]
                    }
                )
            return Response(
                {
                    "uuid": uuid,
                    "prompt": "one two three",
                    "response": {
                        "overall": {
                            "stage": "STAGE_SUCCESS",
                            "version": "4.0",
                            "fraction_ai": 0.8,
                            "fraction_ai_assisted": 0.0,
                            "fraction_human": 0.2,
                        }
                    },
                }
            )

    class Context:
        request = Request()

        def __init__(self) -> None:
            self.pages = [page]
            self.closed = False

        def close(self) -> None:
            self.closed = True

    context = Context()
    monkeypatch.setattr(
        gui_local,
        "_launch_persistent_context",
        lambda config: (playwright, context, page),
    )
    monkeypatch.setattr(gui_local.gui_core, "authenticated_detector_input", lambda candidate: field)
    monkeypatch.setattr(gui_local.gui_core, "detection_button", lambda candidate: button)
    monkeypatch.setattr(gui_local.gui_core, "wait_for_report", lambda candidate, timeout_ms: None)

    def capture(candidate: object, path: Path) -> str:
        path.write_bytes(b"%PDF-exact-history")
        return "local_cdp_print_fallback"

    monkeypatch.setattr(gui_local, "capture_report_pdf", capture)
    persisted: list[dict[str, object]] = []
    result = gui_local.run_inputs(
        _config(tmp_path),
        [input_path],
        output_root=output_root,
        evidence_callback=lambda directory, receipt: persisted.append(dict(receipt)),
        print_fn=lambda message: None,
    )[0]

    assert button.clicks == 1
    assert [receipt["status"] for receipt in persisted] == ["reserved", "complete"]
    assert result["parsed"]["summary"]["fraction_ai"] == 0.8
    assert result["parsed"]["summary_source"] == "stored_history_structured_result"
    assert result["history_api_exact_identity"]["exact_text_sha256"] == gui_core.sha256_text(
        "one two three"
    )
    assert result["report_url"] == "https://www.pangram.com/history/<uuid>"


def test_exact_sha_gate_fails_before_browser_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "part.txt"
    input_path.write_text("one two three", encoding="utf-8")
    monkeypatch.setattr(
        gui_local,
        "_launch_persistent_context",
        lambda config: (_ for _ in ()).throw(AssertionError("browser must not launch")),
    )

    with pytest.raises(RuntimeError, match="exact SHA-256 changed"):
        gui_local.run_inputs(
            _config(tmp_path),
            [input_path],
            output_root=tmp_path / "runs",
            expected_sha256={str(input_path): "0" * 64},
        )


def test_post_click_failure_is_ambiguous_and_blocks_automatic_repeat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "part.txt"
    input_path.write_text("one two three", encoding="utf-8")
    output_root = tmp_path / "runs"
    page = _Page("")
    context = _Context()
    playwright = _Playwright()
    field = _Field()
    button = _Button(RuntimeError("UI changed after click boundary"))
    launches: list[int] = []

    def launch(config: object) -> tuple[_Playwright, _Context, _Page]:
        launches.append(1)
        return playwright, context, page

    monkeypatch.setattr(gui_local, "_launch_persistent_context", launch)
    monkeypatch.setattr(gui_local.gui_core, "authenticated_detector_input", lambda candidate: field)
    monkeypatch.setattr(gui_local.gui_core, "detection_button", lambda candidate: button)

    with pytest.raises(RuntimeError, match="UI changed"):
        gui_local.run_inputs(
            _config(tmp_path),
            [input_path],
            output_root=output_root,
            print_fn=lambda message: None,
        )

    digest = gui_core.sha256_text("one two three")
    failure_path = gui_core.measurement_dir(output_root, digest) / "failure.json"
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    assert failure["detector_submission_attempted"] is True
    assert failure["transport"] == "local_playwright"

    with pytest.raises(RuntimeError, match="ambiguous prior submission"):
        gui_local.run_inputs(
            _config(tmp_path),
            [input_path],
            output_root=output_root,
            print_fn=lambda message: None,
        )
    assert launches == [1]


def test_unresolved_paid_reservation_blocks_restart_before_browser_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "part.txt"
    input_path.write_text("one two three", encoding="utf-8")
    output_root = tmp_path / "runs"
    digest = gui_core.sha256_text("one two three")
    directory = gui_core.measurement_dir(output_root, digest)
    directory.mkdir(parents=True)
    (directory / "reservation.json").write_text(
        json.dumps({"status": "reserved", "input_sha256": digest}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        gui_local,
        "_launch_persistent_context",
        lambda config: (_ for _ in ()).throw(AssertionError("browser must not launch")),
    )

    with pytest.raises(RuntimeError, match="unresolved paid reservation"):
        gui_local.run_inputs(
            _config(tmp_path),
            [input_path],
            output_root=output_root,
            print_fn=lambda message: None,
        )


def test_recover_captures_existing_report_without_submission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "part.txt"
    input_path.write_text("one two three", encoding="utf-8")
    output_root = tmp_path / "runs"
    body = (
        "Pangram 4.0\nAnalyzed Text\n"
        "Human Written | 3 Words | High Confidence\n"
        "one two three"
    )
    page = _Page(body)
    context = _Context()
    playwright = _Playwright()
    monkeypatch.setattr(
        gui_local,
        "_launch_persistent_context",
        lambda config: (playwright, context, page),
    )
    monkeypatch.setattr(gui_local.gui_core, "authenticated_detector_input", lambda candidate: object())
    monkeypatch.setattr(
        gui_local.gui_core,
        "detection_button",
        lambda candidate: (_ for _ in ()).throw(AssertionError("recover must not submit")),
    )
    monkeypatch.setattr(
        gui_local.gui_core,
        "select_existing_report_page",
        lambda candidate, exact_text: (candidate, body),
    )

    def capture(candidate: object, path: Path) -> str:
        path.write_bytes(b"%PDF-recovered")
        return "local_cdp_print_fallback"

    monkeypatch.setattr(gui_local, "capture_report_pdf", capture)

    result = gui_local.recover_existing_report(
        _config(tmp_path),
        input_path,
        output_root=output_root,
        input_fn=lambda prompt: "",
        print_fn=lambda message: None,
    )

    assert result["status"] == "complete"
    assert result["evidence_source"] == "recovered_existing_report"
    assert result["detector_submission_attempted"] is False
    assert context.closed is True
    assert playwright.stopped is True
