#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlsplit

import pangram_local_romance_recover_part1 as base
from pangram_lab.browser_history_recovery import (
    discover_pangram_history_navigation_urls_from_page,
    discover_pangram_history_urls,
    discover_pangram_history_urls_from_page,
    extract_pangram_history_urls_from_payload,
)

HISTORY_ROOT_URL = "https://www.pangram.com/history"
_HISTORY_CONTROL_MARKERS = ("history", "past scans", "recent scans", "my scans", "reports")


def _try_exact_history_urls(
    context: Any,
    page: Any,
    exact_text: str,
    history_urls: tuple[str, ...] | list[str] | set[str],
) -> tuple[Any, str, dict[str, object]] | None:
    if not history_urls:
        return None
    working = base.local_transport.normalize_context_tabs(context, keep=page)
    seen: set[str] = set()
    for candidate_url in tuple(history_urls)[:40]:
        candidate = str(candidate_url)
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            working.goto(candidate, wait_until="domcontentloaded")
            if hasattr(working, "wait_for_timeout"):
                working.wait_for_timeout(1_200)
            matched = base.local_transport.find_exact_report_in_open_pages(
                context,
                exact_text,
                expected_word_count=base.EXPECTED_WORDS,
            )
            if matched is not None:
                return matched
            return base.local_transport.wait_for_exact_report_page(
                context,
                exact_text,
                expected_word_count=base.EXPECTED_WORDS,
                timeout_ms=3_500,
                poll_ms=350,
            )
        except Exception:
            continue
    return None


def _pangram_json_response_collector(candidate_urls: set[str]):
    """Capture only result identities from authenticated Pangram JSON responses.

    Response bodies are inspected in memory and immediately discarded. No body,
    cookie, storage value, request header, or private result URL is logged.
    """

    def collect(response: Any) -> None:
        try:
            parsed = urlsplit(str(getattr(response, "url", "")))
            host = parsed.netloc.casefold()
            if host != "pangram.com" and not host.endswith(".pangram.com"):
                return
            headers = getattr(response, "headers", {}) or {}
            content_type = str(headers.get("content-type", "")).casefold()
            if "json" not in content_type:
                return
            content_length = str(headers.get("content-length", "")).strip()
            if content_length.isdigit() and int(content_length) > 5_000_000:
                return
            payload = response.json()
            candidate_urls.update(extract_pangram_history_urls_from_payload(payload, limit=100))
        except Exception:
            return

    return collect


def _click_bounded_history_control(page: Any) -> bool:
    """Click only a visible interactive control explicitly labeled as History/scans."""
    try:
        locator = page.locator("a, button, [role='button']")
        count = int(locator.count())
    except Exception:
        return False

    for index in range(min(count, 200)):
        candidate = locator.nth(index)
        try:
            if hasattr(candidate, "is_visible") and not candidate.is_visible():
                continue
            pieces: list[str] = []
            try:
                pieces.append(str(candidate.inner_text()))
            except Exception:
                pass
            for attr in ("aria-label", "title"):
                try:
                    pieces.append(str(candidate.get_attribute(attr) or ""))
                except Exception:
                    pass
            label = " ".join(pieces).casefold()
            if not any(marker in label for marker in _HISTORY_CONTROL_MARKERS):
                continue
            candidate.click()
            if hasattr(page, "wait_for_timeout"):
                page.wait_for_timeout(1_500)
            return True
        except Exception:
            continue
    return False


def _try_hydrated_dashboard_history(
    context: Any,
    page: Any,
    exact_text: str,
    network_candidates: set[str],
) -> tuple[Any, str, dict[str, object]] | None:
    """Use only read-only authenticated dashboard surfaces to locate prior results."""
    working = base.local_transport.normalize_context_tabs(context, keep=page)
    try:
        working.goto(base.gui_core.DEFAULT_PANGRAM_GUI_URL, wait_until="domcontentloaded")
        base.local_transport.wait_for_authenticated_detector_input(working)
    except Exception:
        return None

    # Some dashboard builds render recent/history result links directly.
    rendered = discover_pangram_history_urls_from_page(working, limit=50)
    recovered = _try_exact_history_urls(context, working, exact_text, rendered)
    if recovered is not None:
        return recovered

    # Prefer routes actually rendered by the current dashboard rather than a
    # remembered route name. The URL is never printed to the operator log.
    navigation_urls = discover_pangram_history_navigation_urls_from_page(working, limit=20)
    for navigation_url in navigation_urls:
        try:
            working.goto(navigation_url, wait_until="domcontentloaded")
            if hasattr(working, "wait_for_timeout"):
                working.wait_for_timeout(1_500)
        except Exception:
            continue
        rendered = discover_pangram_history_urls_from_page(working, limit=50)
        recovered = _try_exact_history_urls(context, working, exact_text, rendered)
        if recovered is not None:
            return recovered
        recovered = _try_exact_history_urls(context, working, exact_text, network_candidates)
        if recovered is not None:
            return recovered
        try:
            if base._try_open_exact_preview(context, exact_text):
                return base.local_transport.wait_for_exact_report_page(
                    context,
                    exact_text,
                    expected_word_count=base.EXPECTED_WORDS,
                    timeout_ms=6_000,
                    poll_ms=400,
                )
        except Exception:
            pass

    # If History is a button/SPA tab rather than a link, click only an
    # explicitly History/scans-labelled interactive element.
    try:
        working.goto(base.gui_core.DEFAULT_PANGRAM_GUI_URL, wait_until="domcontentloaded")
        base.local_transport.wait_for_authenticated_detector_input(working)
    except Exception:
        pass
    if _click_bounded_history_control(working):
        rendered = discover_pangram_history_urls_from_page(working, limit=50)
        recovered = _try_exact_history_urls(context, working, exact_text, rendered)
        if recovered is not None:
            return recovered
        recovered = _try_exact_history_urls(context, working, exact_text, network_candidates)
        if recovered is not None:
            return recovered
        try:
            if base._try_open_exact_preview(context, exact_text):
                return base.local_transport.wait_for_exact_report_page(
                    context,
                    exact_text,
                    expected_word_count=base.EXPECTED_WORDS,
                    timeout_ms=6_000,
                    poll_ms=400,
                )
        except Exception:
            pass

    # The historical root can redirect to the dashboard; still try it because
    # current Pangram builds may hydrate the History tab from that navigation.
    try:
        working.goto(HISTORY_ROOT_URL, wait_until="domcontentloaded")
        if hasattr(working, "wait_for_timeout"):
            working.wait_for_timeout(1_500)
    except Exception:
        pass
    rendered = discover_pangram_history_urls_from_page(working, limit=50)
    recovered = _try_exact_history_urls(context, working, exact_text, rendered)
    if recovered is not None:
        return recovered
    recovered = _try_exact_history_urls(context, working, exact_text, network_candidates)
    if recovered is not None:
        return recovered
    return None


def main() -> int:
    config = base.local_transport.LocalPlaywrightConfig.from_env()
    sqlite_history_urls = discover_pangram_history_urls(config.profile_dir, limit=20)
    print(
        "[pangram-local-recover] dedicated-profile Chromium-history candidates="
        f"{len(sqlite_history_urls)}; dashboard recovery will also inspect rendered/history-response identities "
        "(private URLs not printed)",
        flush=True,
    )

    original_find = base._find_or_open_report

    def enhanced_find(
        context: Any,
        page: Any,
        exact_text: str,
    ) -> tuple[Any, str, dict[str, object]]:
        network_candidates: set[str] = set()
        collector = _pangram_json_response_collector(network_candidates)
        listener_attached = False
        try:
            on = getattr(context, "on", None)
            if callable(on):
                on("response", collector)
                listener_attached = True
        except Exception:
            listener_attached = False

        try:
            recovered = _try_exact_history_urls(
                context,
                page,
                exact_text,
                sqlite_history_urls,
            )
            if recovered is not None:
                print(
                    "[pangram-local-recover] recovered exact Part 1 from dedicated-profile Chromium history",
                    flush=True,
                )
                return recovered

            recovered = _try_hydrated_dashboard_history(
                context,
                page,
                exact_text,
                network_candidates,
            )
            if recovered is not None:
                print(
                    "[pangram-local-recover] recovered exact Part 1 from authenticated Pangram History surface",
                    flush=True,
                )
                return recovered

            # Give any late History-list JSON response one final read-only chance.
            recovered = _try_exact_history_urls(
                context,
                page,
                exact_text,
                network_candidates,
            )
            if recovered is not None:
                print(
                    "[pangram-local-recover] recovered exact Part 1 from authenticated Pangram history response",
                    flush=True,
                )
                return recovered

            return original_find(context, page, exact_text)
        finally:
            if listener_attached:
                try:
                    remove = getattr(context, "remove_listener", None)
                    if callable(remove):
                        remove("response", collector)
                except Exception:
                    pass

    base._find_or_open_report = enhanced_find
    try:
        base._json(base.recover())
    except Exception as exc:
        # Preserve the exact no-repeat boundary in the terminal log.
        diagnostic = {
            "status": "not_recovered",
            "detector_submission_attempted_during_recovery": False,
            "dedicated_profile_chromium_history_candidates": len(sqlite_history_urls),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        print(json.dumps(diagnostic, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
        raise
    finally:
        base._find_or_open_report = original_find
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
