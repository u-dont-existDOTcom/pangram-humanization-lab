from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from pangram_lab.gui_local_legacy import *  # noqa: F401,F403
from pangram_lab import gui_local_legacy as _legacy


def containing_git_root(path: Path, *, home: Path | None = None) -> Path | None:
    """Return an enclosing Git root while ignoring an inert marker at $HOME.

    A valid Git worktree is always blocked. Outside the user's home directory,
    an unreadable/inert `.git` marker is treated conservatively as a repository
    boundary. The special case exists only because stale `$HOME/.git` debris
    otherwise makes every normal config directory appear unsafe.
    """
    current = _legacy._resolved(path)
    selected_home = _legacy._resolved(Path.home() if home is None else home)
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        marker = candidate / ".git"
        if not marker.exists():
            continue
        completed = subprocess.run(
            ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            top = Path(completed.stdout.strip()).expanduser().resolve(strict=False)
            if top == candidate.expanduser().resolve(strict=False):
                return top
        if candidate == selected_home:
            # Inert home-level markers are not repositories. This is the exact
            # live Zorin failure mode observed on 2026-08-18.
            continue
        # Elsewhere fail closed: a .git marker may represent a damaged or
        # unusual worktree that we should not put persistent auth material in.
        return candidate.expanduser().resolve(strict=False)
    return None


# validate_profile_dir and LocalPlaywrightConfig are defined in the preserved
# transport core; they resolve containing_git_root dynamically.
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


def _sync_core_seams() -> None:
    """Keep legacy core calls aligned with wrapper-level test/runtime seams."""
    _legacy.containing_git_root = containing_git_root
    _legacy._launch_persistent_context = _launch_persistent_context
    # Existing tests and recovery code intentionally monkeypatch this public
    # seam on gui_local; propagate the current wrapper value before delegation.
    _legacy.capture_report_pdf = globals()["capture_report_pdf"]


def bootstrap_login(*args: Any, **kwargs: Any) -> dict[str, object]:
    _sync_core_seams()
    return _legacy.bootstrap_login(*args, **kwargs)


def verify_login_persistence(*args: Any, **kwargs: Any) -> dict[str, object]:
    _sync_core_seams()
    return _legacy.verify_login_persistence(*args, **kwargs)


def launch_smoke_test(*args: Any, **kwargs: Any) -> dict[str, object]:
    _sync_core_seams()
    return _legacy.launch_smoke_test(*args, **kwargs)


def run_inputs(*args: Any, **kwargs: Any) -> list[dict[str, object]]:
    _sync_core_seams()
    return _legacy.run_inputs(*args, **kwargs)


def recover_existing_report(*args: Any, **kwargs: Any) -> dict[str, object]:
    _sync_core_seams()
    return _legacy.recover_existing_report(*args, **kwargs)


def __getattr__(name: str) -> Any:
    return getattr(_legacy, name)
