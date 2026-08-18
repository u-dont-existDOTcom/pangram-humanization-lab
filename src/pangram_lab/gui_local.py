from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from pangram_lab.gui_local_legacy import *  # noqa: F401,F403
from pangram_lab import gui_local_legacy as _legacy


def containing_git_root(path: Path) -> Path | None:
    """Return an enclosing *valid* Git worktree root, ignoring stale .git markers."""
    current = _legacy._resolved(path)
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if not (candidate / ".git").exists():
            continue
        completed = subprocess.run(
            ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            continue
        raw = completed.stdout.strip()
        if not raw:
            continue
        top = Path(raw).expanduser().resolve(strict=False)
        if top == candidate.expanduser().resolve(strict=False):
            return top
    return None


# validate_profile_dir and LocalPlaywrightConfig are defined in the legacy core;
# they resolve this global dynamically, so patch the semantic Git-root probe in
# the core instead of weakening the profile safety policy.
_legacy.containing_git_root = containing_git_root


def _launch_persistent_context(config: Any) -> tuple[Any, Any, Any]:
    profile_dir = _legacy.validate_profile_dir(
        config.profile_dir,
        allow_ordinary_profile=config.allow_ordinary_profile,
        allow_in_git_repo=config.allow_profile_in_git_repo,
    )
    _legacy.ensure_profile_dir(profile_dir)
    sync_playwright = _legacy.gui_core._load_playwright()
    playwright = sync_playwright().start()
    launch_options: dict[str, object] = {
        "user_data_dir": str(profile_dir),
        "headless": not config.headed,
        # Playwright defaults Chromium sandboxing to false. This local runner
        # stores an authenticated persistent profile, so use the OS sandbox on
        # Joel's normal non-root desktop rather than accepting --no-sandbox.
        "chromium_sandbox": True,
    }
    if config.browser_executable is not None:
        launch_options["executable_path"] = str(config.browser_executable)
    if config.headed:
        launch_options["no_viewport"] = True
        launch_options["args"] = ["--start-maximized"]
    try:
        context = playwright.chromium.launch_persistent_context(**launch_options)
    except Exception:
        playwright.stop()
        raise
    pages = context.pages
    page = pages[0] if pages else context.new_page()
    return playwright, context, page


# Public functions imported above execute in gui_local_legacy's module globals.
# Patch that core launch seam so bootstrap/verify/run/recover all inherit the
# sandboxed local transport without duplicating detector logic.
_legacy._launch_persistent_context = _launch_persistent_context


def __getattr__(name: str) -> Any:
    return getattr(_legacy, name)
