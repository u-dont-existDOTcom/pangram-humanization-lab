#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import pangram_local_romance_recover_part1 as base
from pangram_lab.browser_history_recovery import (
    discover_pangram_history_navigation_urls_from_page,
    discover_pangram_history_urls,
    discover_pangram_history_urls_from_page,
    extract_pangram_history_urls_from_payload,
)

HISTORY_ROOT_URL = "https://www.pangram.com/history"
_HISTORY_CONTROL_MARKERS = (
    "history",
    "all checks",
    "past checks",
    "recent checks",
    "checks",
    "past scans",
    "recent scans",
    "my scans",
    "reports",
    "records",
)
_RESULT_CONTROL_MARKERS = ("view results", "view result", "results")
_INTERACTIVE_SELECTOR = (
    "a, button, [role='button'], [role='link'], [role='menuitem'], "
    "[role='tab'], [role='combobox']"
)
_UUID_IN_PATH_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_LONG_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]{24,}")
_EMAIL_RE = re.compile(r"\b[^\s@]+@[^\s@]+\b")


def _safe_absolute_pangram_url(raw_url: str) -> str | None:
    raw = str(raw_url or "").strip()
    if not raw:
        return None
    absolute = urljoin("https://www.pangram.com/", raw)
    parsed = urlsplit(absolute)
    if parsed.scheme != "https" or parsed.netloc.casefold() not in {"pangram.com", "www.pangram.com"}:
        return None
    return absolute


def _control_label(candidate: Any) -> str:
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
    return " ".join(" ".join(piece.split()) for piece in pieces if piece).strip()


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
    for candidate_url in tuple(history_urls)[:60]:
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


def _discover_result_action_urls_from_page(page: Any, *, limit: int = 60) -> tuple[str, ...]:
    """Return same-origin hrefs behind explicit current-UI `View Results` controls."""
    try:
        locator = page.locator("a[href]")
        count = int(locator.count())
    except Exception:
        return ()
    result: list[str] = []
    seen: set[str] = set()
    for index in range(min(count, 500)):
        candidate = locator.nth(index)
        label = _control_label(candidate).casefold()
        if not any(marker in label for marker in _RESULT_CONTROL_MARKERS):
            continue
        try:
            raw = str(candidate.get_attribute("href") or "")
        except Exception:
            continue
        absolute = _safe_absolute_pangram_url(raw)
        if absolute is None or absolute in seen:
            continue
        seen.add(absolute)
        result.append(absolute)
        if len(result) >= limit:
            break
    return tuple(result)


def _redact_network_path(raw_url: str) -> tuple[str, str]:
    try:
        parsed = urlsplit(raw_url)
        host = parsed.netloc.casefold()
        path = parsed.path or "/"
    except Exception:
        return "", ""
    path = _UUID_IN_PATH_RE.sub("<uuid>", path)
    path = _LONG_TOKEN_RE.sub("<token>", path)
    return host, path[:240]


def _json_shape(payload: Any) -> dict[str, object]:
    if isinstance(payload, dict):
        keys = sorted(str(key)[:80] for key in payload.keys())[:40]
        return {"type": "object", "keys": keys, "key_count": len(payload)}
    if isinstance(payload, list):
        item_keys: list[str] = []
        for item in payload[:5]:
            if isinstance(item, dict):
                item_keys.extend(str(key)[:80] for key in item.keys())
        return {
            "type": "array",
            "length": len(payload),
            "item_keys": sorted(set(item_keys))[:40],
        }
    return {"type": type(payload).__name__}


def _response_collector(
    candidate_urls: set[str],
    network_metadata: list[dict[str, object]],
    json_shapes: list[dict[str, object]],
):
    """Collect result identities plus privacy-bounded network structure.

    Bodies are inspected only in memory when JSON and then discarded. No body,
    query string, cookie, storage value, request/response header value, or
    private result URL is logged.
    """
    seen_meta: set[tuple[object, ...]] = set()
    seen_shapes: set[tuple[object, ...]] = set()

    def collect(response: Any) -> None:
        try:
            raw_url = str(getattr(response, "url", ""))
            host, safe_path = _redact_network_path(raw_url)
            if not host:
                return
            status = int(getattr(response, "status", 0) or 0)
            headers = getattr(response, "headers", {}) or {}
            content_type = str(headers.get("content-type", "")).split(";", 1)[0].casefold()[:100]
            request = getattr(response, "request", None)
            method = str(getattr(request, "method", "") or "")[:16]
            meta_key = (host, safe_path, status, content_type, method)
            if meta_key not in seen_meta and len(network_metadata) < 120:
                seen_meta.add(meta_key)
                network_metadata.append(
                    {
                        "host": host,
                        "path": safe_path,
                        "status": status,
                        "content_type": content_type,
                        "method": method,
                    }
                )

            if "json" not in content_type:
                return
            content_length = str(headers.get("content-length", "")).strip()
            if content_length.isdigit() and int(content_length) > 5_000_000:
                return
            payload = response.json()
            # The exact-report verifier is the authority for any candidate, so
            # JSON may come from a backend host different from pangram.com.
            candidate_urls.update(extract_pangram_history_urls_from_payload(payload, limit=100))
            shape = _json_shape(payload)
            shape_key = (
                host,
                safe_path,
                str(shape.get("type")),
                tuple(shape.get("keys", ())),
                tuple(shape.get("item_keys", ())),
            )
            if shape_key not in seen_shapes and len(json_shapes) < 60:
                seen_shapes.add(shape_key)
                json_shapes.append({"host": host, "path": safe_path, **shape})
        except Exception:
            return

    return collect


def _safe_control_labels(page: Any, *, limit: int = 80) -> list[str]:
    try:
        locator = page.locator(_INTERACTIVE_SELECTOR)
        count = int(locator.count())
    except Exception:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for index in range(min(count, 300)):
        candidate = locator.nth(index)
        try:
            if hasattr(candidate, "is_visible") and not candidate.is_visible():
                continue
        except Exception:
            continue
        label = _control_label(candidate)
        label = _EMAIL_RE.sub("<email>", label)
        label = _LONG_TOKEN_RE.sub("<token>", label)
        label = label[:160].strip()
        if not label or label in seen:
            continue
        seen.add(label)
        result.append(label)
        if len(result) >= limit:
            break
    return result


def _click_bounded_history_control(page: Any) -> bool:
    """Click only a visible control explicitly labelled as past-record navigation."""
    try:
        locator = page.locator(_INTERACTIVE_SELECTOR)
        count = int(locator.count())
    except Exception:
        return False

    for index in range(min(count, 300)):
        candidate = locator.nth(index)
        try:
            if hasattr(candidate, "is_visible") and not candidate.is_visible():
                continue
            label = _control_label(candidate).casefold()
            if not any(marker in label for marker in _HISTORY_CONTROL_MARKERS):
                continue
            candidate.click()
            if hasattr(page, "wait_for_timeout"):
                page.wait_for_timeout(1_800)
            return True
        except Exception:
            continue
    return False


def _click_navigation_expander(page: Any) -> bool:
    """Open one explicitly-labelled menu/sidebar control, if present."""
    markers = ("menu", "navigation", "sidebar", "open menu", "show menu")
    try:
        locator = page.locator(_INTERACTIVE_SELECTOR)
        count = int(locator.count())
    except Exception:
        return False
    for index in range(min(count, 200)):
        candidate = locator.nth(index)
        try:
            if hasattr(candidate, "is_visible") and not candidate.is_visible():
                continue
            label = _control_label(candidate).casefold()
            if not label or not any(marker in label for marker in markers):
                continue
            candidate.click()
            if hasattr(page, "wait_for_timeout"):
                page.wait_for_timeout(800)
            return True
        except Exception:
            continue
    return False


def _try_current_record_surface(
    context: Any,
    page: Any,
    exact_text: str,
    network_candidates: set[str],
) -> tuple[Any, str, dict[str, object]] | None:
    rendered = discover_pangram_history_urls_from_page(page, limit=80)
    action_urls = _discover_result_action_urls_from_page(page, limit=80)
    recovered = _try_exact_history_urls(
        context,
        page,
        exact_text,
        (*rendered, *action_urls, *tuple(network_candidates)),
    )
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
    return None


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
        if hasattr(working, "wait_for_timeout"):
            working.wait_for_timeout(1_200)
    except Exception:
        return None

    recovered = _try_current_record_surface(context, working, exact_text, network_candidates)
    if recovered is not None:
        return recovered

    # Prefer routes rendered by the current dashboard. The helper recognizes
    # both the older History vocabulary and the current Pangram `All Checks`
    # surface documented by Pangram itself.
    navigation_urls = discover_pangram_history_navigation_urls_from_page(working, limit=30)
    for navigation_url in navigation_urls:
        try:
            working.goto(navigation_url, wait_until="domcontentloaded")
            if hasattr(working, "wait_for_timeout"):
                working.wait_for_timeout(1_800)
        except Exception:
            continue
        recovered = _try_current_record_surface(context, working, exact_text, network_candidates)
        if recovered is not None:
            return recovered

    # If the sidebar/menu is collapsed, reveal it once and repeat the strictly
    # labelled All Checks/History control search.
    try:
        working.goto(base.gui_core.DEFAULT_PANGRAM_GUI_URL, wait_until="domcontentloaded")
        base.local_transport.wait_for_authenticated_detector_input(working)
    except Exception:
        pass
    _click_navigation_expander(working)
    if _click_bounded_history_control(working):
        recovered = _try_current_record_surface(context, working, exact_text, network_candidates)
        if recovered is not None:
            return recovered

    # Older routing fallback. A current build may redirect this back to the
    # dashboard; the network listener can still observe any record-list load.
    try:
        working.goto(HISTORY_ROOT_URL, wait_until="domcontentloaded")
        if hasattr(working, "wait_for_timeout"):
            working.wait_for_timeout(1_800)
    except Exception:
        pass
    return _try_current_record_surface(context, working, exact_text, network_candidates)


def _write_safe_history_diagnostic(
    page: Any,
    *,
    network_metadata: list[dict[str, object]],
    json_shapes: list[dict[str, object]],
    network_candidate_count: int,
    chromium_candidate_count: int,
) -> Path:
    path = Path.home() / "Téléchargements" / "pangram-local-history-structure-diagnostic.json"
    payload = {
        "privacy_note": (
            "Structural diagnostic only: no response bodies, submitted text, cookies, storage values, "
            "query strings, headers, or private result URLs are included."
        ),
        "safe_page": base.local_transport.auth_surface_diagnostic(page),
        "visible_interactive_labels": _safe_control_labels(page),
        "chromium_history_candidate_count": chromium_candidate_count,
        "network_result_identity_candidate_count": network_candidate_count,
        "network_responses": network_metadata,
        "json_response_shapes": json_shapes,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main() -> int:
    config = base.local_transport.LocalPlaywrightConfig.from_env()
    sqlite_history_urls = discover_pangram_history_urls(config.profile_dir, limit=20)
    print(
        "[pangram-local-recover] dedicated-profile Chromium-history candidates="
        f"{len(sqlite_history_urls)}; current Pangram All Checks/History recovery enabled "
        "(private URLs not printed)",
        flush=True,
    )

    original_find = base._find_or_open_report
    last_diagnostic_path: Path | None = None

    def enhanced_find(
        context: Any,
        page: Any,
        exact_text: str,
    ) -> tuple[Any, str, dict[str, object]]:
        nonlocal last_diagnostic_path
        network_candidates: set[str] = set()
        network_metadata: list[dict[str, object]] = []
        json_shapes: list[dict[str, object]] = []
        collector = _response_collector(network_candidates, network_metadata, json_shapes)
        listener_attached = False
        try:
            on = getattr(context, "on", None)
            if callable(on):
                on("response", collector)
                listener_attached = True
        except Exception:
            listener_attached = False

        try:
            recovered = _try_exact_history_urls(context, page, exact_text, sqlite_history_urls)
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
                    "[pangram-local-recover] recovered exact Part 1 from authenticated Pangram All Checks/History surface",
                    flush=True,
                )
                return recovered

            # Give late record-list JSON responses one final read-only chance.
            recovered = _try_exact_history_urls(context, page, exact_text, network_candidates)
            if recovered is not None:
                print(
                    "[pangram-local-recover] recovered exact Part 1 from authenticated Pangram record response",
                    flush=True,
                )
                return recovered

            last_diagnostic_path = _write_safe_history_diagnostic(
                page,
                network_metadata=network_metadata,
                json_shapes=json_shapes,
                network_candidate_count=len(network_candidates),
                chromium_candidate_count=len(sqlite_history_urls),
            )
            print(
                "[pangram-local-recover] no exact record recovered; safe structural diagnostic="
                f"{last_diagnostic_path}",
                flush=True,
            )
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
        diagnostic = {
            "status": "not_recovered",
            "detector_submission_attempted_during_recovery": False,
            "dedicated_profile_chromium_history_candidates": len(sqlite_history_urls),
            "safe_structure_diagnostic": str(last_diagnostic_path) if last_diagnostic_path else None,
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
