from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from pangram_lab.gui_local_legacy import *  # noqa: F401,F403
from pangram_lab import gui_local_legacy as _legacy


AuthProbe = Callable[[Any], Any]


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


def _visible_locator_stats(page: Any, selector: str) -> dict[str, int | None]:
    try:
        locator = page.locator(selector)
        count = int(locator.count())
    except Exception:
        return {"count": None, "visible": None}
    visible = 0
    for index in range(count):
        try:
            if locator.nth(index).is_visible():
                visible += 1
        except Exception:
            continue
    return {"count": count, "visible": visible}


def _visible_texts(page: Any, selector: str, *, limit: int = 12) -> list[str]:
    try:
        locator = page.locator(selector)
        count = int(locator.count())
    except Exception:
        return []
    values: list[str] = []
    for index in range(min(count, limit * 3)):
        candidate = locator.nth(index)
        try:
            if hasattr(candidate, "is_visible") and not candidate.is_visible():
                continue
            text = " ".join(str(candidate.inner_text()).split())
        except Exception:
            continue
        if text:
            values.append(text[:160])
        if len(values) >= limit:
            break
    return values


def auth_surface_diagnostic(page: Any) -> dict[str, object]:
    """Return a privacy-bounded structural snapshot of the current auth surface."""
    raw_url = str(getattr(page, "url", ""))
    parsed = urlsplit(raw_url)
    safe_url = ""
    if parsed.scheme and parsed.netloc:
        safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    else:
        safe_url = parsed.path or raw_url.split("?", 1)[0].split("#", 1)[0]

    try:
        title = str(page.title())[:200]
    except Exception:
        title = ""
    try:
        body = " ".join(page.locator("body").inner_text().split())
    except Exception:
        body = ""
    folded = body.casefold()
    account_wall_markers = (
        "log in to your account",
        "create your account to get started",
        "sign up to gain access to the pangram dashboard",
        "already have an account? sign in",
        "don't have an account? sign up",
    )
    locator_stats = {
        "textarea": _visible_locator_stats(page, "textarea"),
        "contenteditable_true": _visible_locator_stats(page, '[contenteditable="true"]'),
        "role_textbox": _visible_locator_stats(page, '[role="textbox"]'),
        "text_input": _visible_locator_stats(page, 'input[type="text"]'),
        "untyped_input": _visible_locator_stats(page, "input:not([type])"),
        "iframe": _visible_locator_stats(page, "iframe"),
    }
    return {
        "captured_at_utc": _legacy.utc_now_iso(),
        "safe_url": safe_url,
        "path": parsed.path,
        "title": title,
        "body_character_count": len(body),
        "markers": {
            "loading": folded.strip().startswith("loading"),
            "account_wall": any(marker in folded for marker in account_wall_markers),
            "dashboard_word_visible": "dashboard" in folded,
        },
        "locator_stats": locator_stats,
        "headings": _visible_texts(page, "h1, h2"),
        "button_labels": _visible_texts(page, "button"),
        "privacy_note": "No cookies, storage values, HTML, form values, submitted text, or body excerpt captured.",
    }


def _write_auth_diagnostic(page: Any, *, diagnostic_dir: Path | None = None) -> dict[str, str]:
    directory = diagnostic_dir or (Path.home() / "Téléchargements")
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "pangram-local-auth-diagnostic.json"
    screenshot_path = directory / "pangram-local-auth-diagnostic.png"
    diagnostic = auth_surface_diagnostic(page)
    json_path.write_text(
        json.dumps(diagnostic, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    screenshot_saved = False
    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
        screenshot_saved = True
    except Exception:
        pass
    result = {"json": str(json_path)}
    if screenshot_saved:
        result["screenshot"] = str(screenshot_path)
    return result


def wait_for_authenticated_detector_input(
    page: Any,
    *,
    timeout_ms: int = 30_000,
    poll_ms: int = 250,
    probe: AuthProbe | None = None,
    diagnostic_dir: Path | None = None,
) -> Any:
    """Wait for Pangram's hydrated authenticated detector surface without submitting text."""
    if timeout_ms < 1:
        raise ValueError("timeout_ms must be positive")
    if poll_ms < 1:
        raise ValueError("poll_ms must be positive")
    immediate_probe = probe or _legacy.gui_core.authenticated_detector_input
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    last_error: RuntimeError | None = None

    while True:
        try:
            return immediate_probe(page)
        except RuntimeError as exc:
            last_error = exc
            message = str(exc).casefold()
            # These are semantic authentication failures, not hydration races.
            if "login did not persist" in message or "account wall is visible" in message:
                raise

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            paths = _write_auth_diagnostic(page, diagnostic_dir=diagnostic_dir)
            diagnostic = auth_surface_diagnostic(page)
            if diagnostic.get("markers", {}).get("account_wall"):
                classification = "login_not_persisted"
            elif re_search_login_path(str(diagnostic.get("path", ""))):
                classification = "login_not_persisted"
            else:
                classification = "dashboard_surface_timeout"
            detail = str(last_error) if last_error is not None else "detector surface unavailable"
            raise RuntimeError(
                "Pangram authenticated detector surface did not become ready within "
                f"{timeout_ms} ms; classification={classification}; last_error={detail}; "
                f"diagnostic_json={paths['json']}"
                + (f"; diagnostic_screenshot={paths['screenshot']}" if "screenshot" in paths else "")
            ) from last_error

        sleep_ms = min(poll_ms, max(1, int(remaining * 1000)))
        if hasattr(page, "wait_for_timeout"):
            page.wait_for_timeout(sleep_ms)
        else:
            time.sleep(sleep_ms / 1000.0)


def re_search_login_path(path: str) -> bool:
    lowered = path.casefold().rstrip("/")
    return lowered.endswith("/login") or lowered.endswith("/signup")


def _sync_core_seams() -> None:
    """Keep legacy core calls aligned with wrapper-level test/runtime seams."""
    _legacy.containing_git_root = containing_git_root
    _legacy._launch_persistent_context = _launch_persistent_context
    # Existing tests and recovery code intentionally monkeypatch this public
    # seam on gui_local; propagate the current wrapper value before delegation.
    _legacy.capture_report_pdf = globals()["capture_report_pdf"]


def _delegate_with_waiting_auth(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Temporarily make all local core auth probes hydration-aware."""
    _sync_core_seams()
    immediate_probe = _legacy.gui_core.authenticated_detector_input

    def waiting_probe(page: Any) -> Any:
        return wait_for_authenticated_detector_input(page, probe=immediate_probe)

    _legacy.gui_core.authenticated_detector_input = waiting_probe
    try:
        return function(*args, **kwargs)
    finally:
        _legacy.gui_core.authenticated_detector_input = immediate_probe


def bootstrap_login(*args: Any, **kwargs: Any) -> dict[str, object]:
    return _delegate_with_waiting_auth(_legacy.bootstrap_login, *args, **kwargs)


def verify_login_persistence(*args: Any, **kwargs: Any) -> dict[str, object]:
    return _delegate_with_waiting_auth(_legacy.verify_login_persistence, *args, **kwargs)


def launch_smoke_test(*args: Any, **kwargs: Any) -> dict[str, object]:
    _sync_core_seams()
    return _legacy.launch_smoke_test(*args, **kwargs)


def run_inputs(*args: Any, **kwargs: Any) -> list[dict[str, object]]:
    return _delegate_with_waiting_auth(_legacy.run_inputs, *args, **kwargs)


def recover_existing_report(*args: Any, **kwargs: Any) -> dict[str, object]:
    return _delegate_with_waiting_auth(_legacy.recover_existing_report, *args, **kwargs)


def __getattr__(name: str) -> Any:
    return getattr(_legacy, name)
