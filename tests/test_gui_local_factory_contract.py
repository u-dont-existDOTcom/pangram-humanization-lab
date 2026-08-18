from __future__ import annotations

from pathlib import Path

import pytest

from pangram_lab import gui_local


def test_playwright_loader_contract_is_callable_then_startable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launches: list[dict[str, object]] = []

    class Page:
        pass

    class Context:
        pages = [Page()]

        def close(self) -> None:
            pass

    class Chromium:
        def launch_persistent_context(self, **kwargs: object) -> Context:
            launches.append(kwargs)
            return Context()

    class Playwright:
        chromium = Chromium()

        def stop(self) -> None:
            pass

    class Manager:
        def start(self) -> Playwright:
            return Playwright()

    monkeypatch.setattr(gui_local.gui_core, "_load_playwright", lambda: (lambda: Manager()))
    config = gui_local.LocalPlaywrightConfig(
        profile_dir=tmp_path / "profile",
        browser_executable=Path("/bin/true"),
    )

    playwright, context, page = gui_local._launch_persistent_context(config)
    gui_local._close_local_session(playwright, context)

    assert launches and launches[0]["headless"] is False
