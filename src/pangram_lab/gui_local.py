from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from pangram_lab.gui_local_legacy import *  # noqa: F401,F403
from pangram_lab import gui_local_legacy as _legacy
from pangram_lab.exact_history_recovery import wait_for_exact_history_record
from pangram_lab.history_api_record import ExactHistoryRecord, parse_history_record_result


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


def _page_is_closed(page: Any) -> bool:
    try:
        value = getattr(page, "is_closed", None)
        return bool(value() if callable(value) else value)
    except Exception:
        return False


def _close_page(page: Any) -> None:
    if _page_is_closed(page):
        return
    close = getattr(page, "close", None)
    if not callable(close):
        return
    try:
        close(run_before_unload=False)
    except TypeError:
        close()
    except Exception:
        pass


def normalize_context_tabs(
    context: Any,
    *,
    keep: Any | None = None,
    blank_keep: bool = False,
) -> Any:
    """Reduce a persistent browser context to one working tab.

    Persistent Chromium-family profiles can restore every tab that was open at
    shutdown. Local automation does not need that tab history; keeping it causes
    visible clutter and can make result selection ambiguous. This helper leaves
    one tab alive and closes every other tab explicitly before the browser
    context is closed.
    """
    pages = [page for page in tuple(getattr(context, "pages", ())) if not _page_is_closed(page)]
    if keep is None or keep not in pages:
        keep = pages[-1] if pages else context.new_page()
        pages = [page for page in tuple(getattr(context, "pages", ())) if not _page_is_closed(page)]
    for candidate in pages:
        if candidate is not keep:
            _close_page(candidate)
    if blank_keep and keep is not None and not _page_is_closed(keep):
        try:
            keep.goto("about:blank", wait_until="domcontentloaded", timeout=5_000)
        except TypeError:
            try:
                keep.goto("about:blank", wait_until="domcontentloaded")
            except Exception:
                pass
        except Exception:
            pass
    return keep


def _launch_persistent_context(
    config: Any,
    *,
    normalize_tabs: bool = True,
) -> tuple[Any, Any, Any]:
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
    pages = tuple(getattr(context, "pages", ()))
    page = pages[-1] if pages else context.new_page()
    if normalize_tabs:
        page = normalize_context_tabs(context, keep=page)
    return playwright, context, page


def _close_local_session(playwright: Any, context: Any) -> None:
    """Close local persistent automation without leaving restored-tab clutter."""
    try:
        pages = [page for page in tuple(getattr(context, "pages", ())) if not _page_is_closed(page)]
        keep = pages[-1] if pages else None
        if keep is not None:
            normalize_context_tabs(context, keep=keep, blank_keep=True)
        context.close()
    finally:
        playwright.stop()


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


def _safe_page_url(page: Any) -> str:
    raw_url = str(getattr(page, "url", ""))
    parsed = urlsplit(raw_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return parsed.path or raw_url.split("?", 1)[0].split("#", 1)[0]


def auth_surface_diagnostic(page: Any) -> dict[str, object]:
    """Return a privacy-bounded structural snapshot of the current auth surface."""
    raw_url = str(getattr(page, "url", ""))
    parsed = urlsplit(raw_url)
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
        "safe_url": _safe_page_url(page),
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


def _report_candidate(
    page: Any,
    exact_text: str,
    expected_word_count: int,
) -> tuple[Any, str, dict[str, object]] | None:
    if _page_is_closed(page):
        return None
    try:
        body = _legacy.gui_core.clean_report_body_artifact(page.locator("body").inner_text())
    except Exception:
        return None
    try:
        parsed = _legacy.gui_core.parse_report_for_exact_input(
            body,
            exact_text,
            expected_word_count=expected_word_count,
        )
    except Exception:
        return None
    segments = list(parsed.get("segments", []))
    if not segments:
        return None
    try:
        parsed_words = sum(int(segment.get("word_count", 0)) for segment in segments)
    except Exception:
        return None
    if parsed_words != expected_word_count:
        return None
    if not _legacy.gui_core.report_body_matches_input(body, exact_text):
        return None
    return page, body, parsed


def find_exact_report_in_open_pages(
    context: Any,
    exact_text: str,
    *,
    expected_word_count: int,
) -> tuple[Any, str, dict[str, object]] | None:
    """Find an already-open exact Pangram report without clicking or submitting."""
    pages = tuple(getattr(context, "pages", ()))
    for candidate in reversed(pages):
        matched = _report_candidate(candidate, exact_text, expected_word_count)
        if matched is not None:
            return matched
    return None


def report_surface_diagnostic(context: Any) -> dict[str, object]:
    pages: list[dict[str, object]] = []
    for candidate in tuple(getattr(context, "pages", ())):
        if _page_is_closed(candidate):
            continue
        try:
            title = str(candidate.title())[:200]
        except Exception:
            title = ""
        try:
            body = " ".join(candidate.locator("body").inner_text().split())
        except Exception:
            body = ""
        folded = body.casefold()
        pages.append(
            {
                "safe_url": _safe_page_url(candidate),
                "title": title,
                "body_character_count": len(body),
                "markers": {
                    "authorship_breakdown": "authorship breakdown" in folded,
                    "analyzed_text": "analyzed text" in folded,
                    "human_written": "human written" in folded,
                    "fully_ai_generated": "fully ai generated" in folded,
                    "words_scanned": "words scanned" in folded,
                },
            }
        )
    return {
        "captured_at_utc": _legacy.utc_now_iso(),
        "open_page_count": len(pages),
        "pages": pages,
        "privacy_note": "No cookies, storage values, HTML, form values, or body excerpts captured.",
    }


def _write_report_diagnostic(
    context: Any,
    *,
    diagnostic_dir: Path | None = None,
) -> dict[str, str]:
    directory = diagnostic_dir or (Path.home() / "Téléchargements")
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "pangram-local-report-diagnostic.json"
    diagnostic = report_surface_diagnostic(context)
    json_path.write_text(
        json.dumps(diagnostic, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"json": str(json_path)}


def wait_for_exact_report_page(
    context: Any,
    exact_text: str,
    *,
    expected_word_count: int,
    timeout_ms: int = 180_000,
    poll_ms: int = 1_000,
    diagnostic_dir: Path | None = None,
) -> tuple[Any, str, dict[str, object]]:
    """Wait across all tabs for the exact report boundary, not a generic UI marker."""
    if timeout_ms < 1:
        raise ValueError("timeout_ms must be positive")
    if poll_ms < 1:
        raise ValueError("poll_ms must be positive")
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    while True:
        matched = find_exact_report_in_open_pages(
            context,
            exact_text,
            expected_word_count=expected_word_count,
        )
        if matched is not None:
            return matched
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            paths = _write_report_diagnostic(context, diagnostic_dir=diagnostic_dir)
            raise RuntimeError(
                "Pangram exact report did not become available before timeout; "
                f"diagnostic_json={paths['json']}"
            )
        sleep_ms = min(poll_ms, max(1, int(remaining * 1000)))
        pages = [page for page in tuple(getattr(context, "pages", ())) if not _page_is_closed(page)]
        if pages and hasattr(pages[-1], "wait_for_timeout"):
            pages[-1].wait_for_timeout(sleep_ms)
        else:
            time.sleep(sleep_ms / 1000.0)


def _sync_core_seams() -> None:
    """Keep legacy core calls aligned with wrapper-level test/runtime seams."""
    _legacy.containing_git_root = containing_git_root
    _legacy._launch_persistent_context = globals()["_launch_persistent_context"]
    _legacy._close_local_session = globals()["_close_local_session"]
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


def _reservation_receipt(
    config: Any,
    item: dict[str, object],
    source: dict[str, object] | None,
) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema_version": 1,
        "status": "reserved",
        **_legacy._transport_fields(config),
        "model": _legacy.gui_core.MODEL_ID,
        "reserved_at_utc": _legacy.utc_now_iso(),
        "input_path": _legacy._receipt_input_path(item, source),
        "input_sha256": str(item["input_sha256"]),
        "word_count": int(item["word_count"]),
        "detector_submission_attempted": False,
        "evidence_source": "pre_click_paid_reservation",
    }
    if source is not None:
        receipt["source"] = dict(source)
    return receipt


def _materialize_exact_record(
    context: Any,
    page: Any,
    record: ExactHistoryRecord,
) -> tuple[Any, str, dict[str, object]]:
    report_page = normalize_context_tabs(context, keep=page)
    report_page.goto(record.report_url, wait_until="domcontentloaded")
    if hasattr(report_page, "wait_for_timeout"):
        report_page.wait_for_timeout(1_800)
    body = _legacy.gui_core.clean_report_body_artifact(
        report_page.locator("body").inner_text()
    )
    parsed = parse_history_record_result(record, body)
    return report_page, body, parsed


def run_inputs(
    config: Any,
    input_paths: Any,
    *,
    output_root: Path = Path("state/gui-runs"),
    force: bool = False,
    report_timeout_ms: int = 180_000,
    expected_sha256: dict[str, str] | None = None,
    source_metadata: dict[str, dict[str, object]] | None = None,
    evidence_callback: Any | None = None,
    print_fn: Any = print,
) -> list[dict[str, object]]:
    _sync_core_seams()
    prepared = _legacy._prepare_inputs(
        input_paths,
        output_root=output_root,
        force=force,
        expected_sha256=expected_sha256,
    )
    blocked = [item for item in prepared if item["blocked_by_ambiguous_submission"]]
    if blocked:
        identities = ", ".join(str(item["input_sha256"]) for item in blocked)
        raise RuntimeError(
            "refusing to repeat Pangram GUI input after an ambiguous prior submission or "
            f"unresolved paid reservation: {identities}. Recover the existing History record first."
        )

    pending = [item for item in prepared if not item["skip"]]
    results: list[dict[str, object]] = [
        {
            "status": "cached",
            "transport": _legacy.TRANSPORT_ID,
            "input_path": item["input_path"],
            "input_sha256": item["input_sha256"],
            "word_count": item["word_count"],
            "directory": item["directory"],
        }
        for item in prepared
        if item["skip"]
    ]
    if not pending:
        return results

    immediate_probe = _legacy.gui_core.authenticated_detector_input
    playwright, context, page = _launch_persistent_context(config)
    try:
        for item in pending:
            directory = Path(str(item["directory"]))
            paths = _legacy.gui_core.artifact_paths(directory)
            reservation_path = directory / "reservation.json"
            directory.mkdir(parents=True, exist_ok=True)
            source = _legacy._source_for_item(item, source_metadata)
            stage = "navigate"
            detector_submission_attempted = False
            try:
                page.goto(config.pangram_url, wait_until="domcontentloaded")
                stage = "verify_authentication"
                field = wait_for_authenticated_detector_input(page, probe=immediate_probe)
                stage = "fill_input"
                field.fill(str(item["text"]))
                stage = "locate_detector_action"
                button = _legacy.gui_core.detection_button(page)

                stage = "reserve_paid_call"
                reservation = _reservation_receipt(config, item, source)
                _legacy._write_json(reservation_path, reservation)
                _legacy._persist_evidence(evidence_callback, directory, reservation)
                reserved_at = datetime.fromisoformat(
                    str(reservation["reserved_at_utc"]).replace("Z", "+00:00")
                ).astimezone(timezone.utc)

                stage = "submit"
                detector_submission_attempted = True
                button.click()
                print_fn(
                    f"[pangram-local] submitted sha={item['input_sha256']}; waiting for exact report"
                )
                stage = "wait_report"
                _legacy.gui_core.wait_for_report(page, timeout_ms=report_timeout_ms)

                stage = "bind_exact_history_record"
                request_getter = getattr(getattr(context, "request", None), "get", None)
                if callable(request_getter):
                    record, history_proof = wait_for_exact_history_record(
                        context,
                        str(item["text"]),
                        target_time=reserved_at,
                        timeout_ms=min(30_000, report_timeout_ms),
                    )
                else:
                    record = None
                    history_proof = {
                        "history_list_attempts": 0,
                        "history_list_status_counts": {
                            "context_request_unavailable": 1
                        },
                    }
                if record is not None:
                    page, body, parsed = _materialize_exact_record(context, page, record)
                    report_url = "https://www.pangram.com/history/<uuid>"
                else:
                    stage = "capture_legacy_report"
                    body = _legacy.gui_core.clean_report_body_artifact(
                        page.locator("body").inner_text()
                    )
                    parsed = _legacy.gui_core.parse_report_for_exact_input(
                        body,
                        str(item["text"]),
                        expected_word_count=int(item["word_count"]),
                    )
                    segments = list(parsed["segments"])
                    if not segments:
                        raise RuntimeError(
                            "Pangram report was visible, but neither an exact stored History record "
                            "nor legacy analyzed segments could be parsed; history_proof="
                            + json.dumps(history_proof, sort_keys=True)
                        )
                    parsed_word_count = sum(int(segment["word_count"]) for segment in segments)
                    if parsed_word_count != int(item["word_count"]):
                        raise RuntimeError(
                            "legacy Pangram report word count does not match exact input: "
                            f"report={parsed_word_count} input={item['word_count']}"
                        )
                    report_url = page.url

                paths["body"].write_text(body, encoding="utf-8")
                stage = "capture_pdf"
                pdf_provenance = capture_report_pdf(page, paths["pdf"])
                receipt = _legacy.build_complete_receipt(
                    config,
                    item=item,
                    report_url=report_url,
                    pdf_provenance=pdf_provenance,
                    parsed=parsed,
                    body=body,
                    pdf_path=paths["pdf"],
                    source=source,
                )
                receipt["paid_reservation"] = reservation
                if record is not None:
                    receipt["history_api_exact_identity"] = record.public_proof()
                    receipt["history_binding_proof"] = history_proof
                    if parsed.get("detector_version"):
                        receipt["detector_version"] = parsed["detector_version"]
                _legacy._write_json(paths["result"], receipt)
                _legacy._remove_stale_failures(directory, paths)
                stage = "persist_evidence"
                _legacy._persist_evidence(evidence_callback, directory, receipt)
                results.append(receipt)
                print_fn(
                    f"[pangram-local] complete sha={item['input_sha256']} "
                    f"words={item['word_count']} pdf={pdf_provenance}"
                )
            except Exception as exc:
                if stage == "persist_evidence":
                    raise
                failure = _legacy.build_failure_receipt(
                    config,
                    item=item,
                    stage=stage,
                    detector_submission_attempted=detector_submission_attempted,
                    error=exc,
                    source=source,
                )
                _legacy._write_json(paths["failure"], failure)
                try:
                    page.screenshot(path=str(paths["failure_screenshot"]), full_page=True)
                except Exception:
                    pass
                try:
                    _legacy._persist_evidence(evidence_callback, directory, failure)
                except Exception as durability_error:
                    raise RuntimeError(
                        "Pangram run failed and saved failure evidence could not be pushed durably: "
                        f"run_error={exc}; durability_error={durability_error}"
                    ) from durability_error
                raise
    finally:
        _close_local_session(playwright, context)
    return results


def recover_existing_report(*args: Any, **kwargs: Any) -> dict[str, object]:
    return _delegate_with_waiting_auth(_legacy.recover_existing_report, *args, **kwargs)


def __getattr__(name: str) -> Any:
    return getattr(_legacy, name)
