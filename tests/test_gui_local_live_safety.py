from __future__ import annotations

import subprocess
from pathlib import Path

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
