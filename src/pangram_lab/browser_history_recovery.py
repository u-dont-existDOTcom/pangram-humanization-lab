from __future__ import annotations

import re
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

_ALLOWED_HOSTS = {"pangram.com", "www.pangram.com"}
_HISTORY_PATH_RE = re.compile(
    r"^/history/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/?$"
)
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_HISTORY_URL_SEARCH_RE = re.compile(
    r"https://(?:www\.)?pangram\.com/history/"
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
    re.IGNORECASE,
)
_RESULT_CONTEXT_MARKERS = ("history", "result", "scan", "detection", "request")


def _absolute_pangram_url(raw_url: str) -> str | None:
    raw = str(raw_url or "").strip()
    if not raw:
        return None
    absolute = urljoin("https://www.pangram.com/", raw)
    parsed = urlsplit(absolute)
    if parsed.scheme != "https" or parsed.netloc.casefold() not in _ALLOWED_HOSTS:
        return None
    return absolute


def _canonical_pangram_history_url(raw_url: str) -> str | None:
    absolute = _absolute_pangram_url(raw_url)
    if absolute is None:
        return None
    parsed = urlsplit(absolute)
    if not _HISTORY_PATH_RE.fullmatch(parsed.path):
        return None
    return "https://www.pangram.com" + parsed.path.rstrip("/")


def _history_db_candidates(profile_dir: Path) -> tuple[Path, ...]:
    root = Path(profile_dir).expanduser().resolve(strict=False)
    candidates: list[Path] = [root / "History"]
    try:
        children = tuple(root.iterdir())
    except OSError:
        children = ()
    for child in children:
        try:
            if child.is_dir():
                candidates.append(child / "History")
        except OSError:
            continue

    result: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        try:
            if resolved.is_file():
                result.append(resolved)
        except OSError:
            continue
    return tuple(result)


def _query_history_snapshot(source: Path, *, limit: int) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="pangram-history-recovery-") as temp_dir:
        snapshot = Path(temp_dir) / "History"
        try:
            shutil.copy2(source, snapshot)
            for suffix in ("-wal", "-shm"):
                sidecar = Path(str(source) + suffix)
                if sidecar.is_file():
                    shutil.copy2(sidecar, Path(str(snapshot) + suffix))
        except OSError:
            return []

        try:
            connection = sqlite3.connect(f"file:{snapshot}?mode=ro", uri=True)
        except sqlite3.Error:
            return []
        try:
            rows = connection.execute(
                "SELECT url FROM urls "
                "WHERE url LIKE 'https://www.pangram.com/history/%' "
                "OR url LIKE 'https://pangram.com/history/%' "
                "ORDER BY last_visit_time DESC LIMIT ?",
                (limit,),
            ).fetchall()
        except sqlite3.Error:
            return []
        finally:
            connection.close()

    return [str(row[0]) for row in rows if row and row[0]]


def discover_pangram_history_urls(
    profile_dir: Path,
    *,
    limit: int = 20,
) -> tuple[str, ...]:
    """Return recent Pangram result URLs from only the dedicated profile history.

    The function never returns unrelated browsing history. Query strings and
    fragments are discarded, and only UUID-shaped ``/history/<id>`` Pangram
    URLs survive validation.
    """
    if limit < 1:
        raise ValueError("limit must be positive")

    result: list[str] = []
    seen: set[str] = set()
    for database in _history_db_candidates(profile_dir):
        for raw_url in _query_history_snapshot(database, limit=limit):
            canonical = _canonical_pangram_history_url(raw_url)
            if canonical is None or canonical in seen:
                continue
            seen.add(canonical)
            result.append(canonical)
            if len(result) >= limit:
                return tuple(result)
    return tuple(result)


def discover_pangram_history_urls_from_page(
    page: Any,
    *,
    limit: int = 50,
) -> tuple[str, ...]:
    """Read only result links already rendered on an authenticated Pangram page."""
    if limit < 1:
        raise ValueError("limit must be positive")
    try:
        locator = page.locator("a[href]")
        count = int(locator.count())
    except Exception:
        return ()

    result: list[str] = []
    seen: set[str] = set()
    for index in range(count):
        try:
            raw = locator.nth(index).get_attribute("href")
        except Exception:
            continue
        canonical = _canonical_pangram_history_url(str(raw or ""))
        if canonical is None or canonical in seen:
            continue
        seen.add(canonical)
        result.append(canonical)
        if len(result) >= limit:
            break
    return tuple(result)


def discover_pangram_history_navigation_urls_from_page(
    page: Any,
    *,
    limit: int = 20,
) -> tuple[str, ...]:
    """Return same-origin rendered links that appear to navigate to History UI.

    Result URLs themselves are excluded. Query strings/fragments are retained in
    memory because a dashboard SPA may encode its selected tab there; callers
    must not print these URLs as operator diagnostics.
    """
    if limit < 1:
        raise ValueError("limit must be positive")
    try:
        locator = page.locator("a[href]")
        count = int(locator.count())
    except Exception:
        return ()

    result: list[str] = []
    seen: set[str] = set()
    for index in range(count):
        try:
            raw = str(locator.nth(index).get_attribute("href") or "")
        except Exception:
            continue
        absolute = _absolute_pangram_url(raw)
        if absolute is None or _canonical_pangram_history_url(absolute) is not None:
            continue
        parsed = urlsplit(absolute)
        marker = f"{parsed.path}?{parsed.query}#{parsed.fragment}".casefold()
        if "history" not in marker or absolute in seen:
            continue
        seen.add(absolute)
        result.append(absolute)
        if len(result) >= limit:
            break
    return tuple(result)


def extract_pangram_history_urls_from_payload(
    payload: Any,
    *,
    limit: int = 100,
) -> tuple[str, ...]:
    """Extract only Pangram result identities from an in-memory JSON payload.

    The payload itself is never returned or persisted. Bare UUID values are
    accepted only when their key ancestry places them under a result/history/
    scan/detection/request object, then converted to the documented
    ``/history/<UUID>`` read-only result route.
    """
    if limit < 1:
        raise ValueError("limit must be positive")
    result: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        canonical = _canonical_pangram_history_url(raw)
        if canonical is not None and canonical not in seen and len(result) < limit:
            seen.add(canonical)
            result.append(canonical)

    def walk(value: Any, ancestry: tuple[str, ...] = ()) -> None:
        if len(result) >= limit:
            return
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, (*ancestry, str(key).casefold()))
            return
        if isinstance(value, (list, tuple)):
            for child in value:
                walk(child, ancestry)
            return
        if not isinstance(value, str):
            return

        text = value.strip()
        for match in _HISTORY_URL_SEARCH_RE.finditer(text):
            add(match.group(0))
            if len(result) >= limit:
                return

        ancestry_text = " ".join(ancestry)
        if _UUID_RE.fullmatch(text) and any(
            marker in ancestry_text for marker in _RESULT_CONTEXT_MARKERS
        ):
            add(f"https://www.pangram.com/history/{text}")

    walk(payload)
    return tuple(result)
