from __future__ import annotations

import re
import shutil
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

_ALLOWED_HOSTS = {"pangram.com", "www.pangram.com"}
_HISTORY_PATH_RE = re.compile(
    r"^/history/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/?$"
)


def _canonical_pangram_history_url(raw_url: str) -> str | None:
    parsed = urlsplit(raw_url)
    if parsed.scheme != "https" or parsed.netloc.casefold() not in _ALLOWED_HOSTS:
        return None
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
