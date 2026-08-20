from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pangram_lab import gui_local
from pangram_lab.gui_local import LocalPlaywrightConfig


def test_inert_home_git_marker_is_ignored_by_semantic_probe(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    profile = tmp_path / ".config" / "pangram-local-browser"

    assert gui_local.containing_git_root(profile, home=tmp_path) is None


def test_real_git_worktree_still_blocks_profile(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    profile = repo / "profile"

    assert gui_local.containing_git_root(profile) == repo.resolve()

    try:
        gui_local.validate_profile_dir(profile, home=tmp_path)
    except RuntimeError as exc:
        assert "inside a Git repository" in str(exc)
    else:
        raise AssertionError("real Git worktree must remain blocked")


def test_persistent_launch_enables_chromium_sandbox(tmp_path: Path, monkeypatch) -> None:
    launch_options: dict[str, object] = {}

    class FakePage:
        pass

    class FakeContext:
        def __init__(self) -> None:
            self.pages = [FakePage()]

        def close(self) -> None:
            pass

    context = FakeContext()

    class FakeChromium:
        def launch_persistent_context(self, **kwargs: object) -> FakeContext:
            launch_options.update(kwargs)
            return context

    class FakePlaywright:
        def __init__(self) -> None:
            self.chromium = FakeChromium()

        def stop(self) -> None:
            pass

    playwright = FakePlaywright()

    class FakeStarter:
        def start(self) -> FakePlaywright:
            return playwright

    monkeypatch.setattr(
        gui_local.gui_core,
        "_load_playwright",
        lambda: (lambda: FakeStarter()),
    )

    config = LocalPlaywrightConfig(
        profile_dir=tmp_path / "profile",
        browser_executable=Path("/bin/true"),
        headed=True,
    )
    active_playwright, active_context, _ = gui_local._launch_persistent_context(config)
    gui_local._close_local_session(active_playwright, active_context)

    assert launch_options["chromium_sandbox"] is True
    assert launch_options["headless"] is False
    assert launch_options["executable_path"] == "/bin/true"


def test_wait_for_authenticated_detector_input_tolerates_delayed_spa_hydration() -> None:
    attempts = 0
    waits: list[int] = []
    field = object()

    class FakePage:
        def wait_for_timeout(self, milliseconds: int) -> None:
            waits.append(milliseconds)

    def probe(page: object) -> object:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError(
                "Pangram detector text input was not found; login may have expired or the UI changed"
            )
        return field

    result = gui_local.wait_for_authenticated_detector_input(
        FakePage(),
        timeout_ms=5_000,
        poll_ms=10,
        probe=probe,
    )

    assert result is field
    assert attempts == 3
    assert waits == [10, 10]


def test_wait_for_authenticated_detector_input_fails_fast_on_explicit_login_loss() -> None:
    waits: list[int] = []

    class FakePage:
        def wait_for_timeout(self, milliseconds: int) -> None:
            waits.append(milliseconds)

    def probe(page: object) -> object:
        raise RuntimeError("authenticated Pangram dashboard is required; login did not persist")

    with pytest.raises(RuntimeError, match="login did not persist"):
        gui_local.wait_for_authenticated_detector_input(
            FakePage(),
            timeout_ms=5_000,
            poll_ms=10,
            probe=probe,
        )

    assert waits == []


def test_auth_surface_diagnostic_does_not_capture_body_excerpt_or_form_values() -> None:
    class Locator:
        def __init__(self, texts: list[str]) -> None:
            self.texts = texts

        def count(self) -> int:
            return len(self.texts)

        def nth(self, index: int) -> "LocatorItem":
            return LocatorItem(self.texts[index])

        def inner_text(self) -> str:
            return "TOP SECRET FORM VALUE should never be emitted"

    class LocatorItem:
        def __init__(self, text: str) -> None:
            self.text = text

        def is_visible(self) -> bool:
            return True

        def inner_text(self) -> str:
            return self.text

    class FakePage:
        url = "https://www.pangram.com/dashboard?private=token#secret"

        def title(self) -> str:
            return "AI Detection Dashboard"

        def locator(self, selector: str) -> Locator:
            if selector == "body":
                return Locator(["unused"])
            if selector == "h1, h2":
                return Locator(["Dashboard"])
            if selector == "button":
                return Locator(["Check for AI"])
            return Locator([])

    diagnostic = gui_local.auth_surface_diagnostic(FakePage())
    serialized = str(diagnostic)

    assert diagnostic["safe_url"] == "https://www.pangram.com/dashboard"
    assert "private=token" not in serialized
    assert "TOP SECRET FORM VALUE" not in serialized
    assert "body_excerpt" not in diagnostic
