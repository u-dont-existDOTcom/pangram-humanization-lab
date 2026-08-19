from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from pangram_lab.browser_history_recovery import (
    discover_pangram_history_navigation_urls_from_page,
    discover_pangram_history_urls,
    discover_pangram_history_urls_from_page,
    extract_pangram_history_urls_from_payload,
)


def _write_history(path: Path, rows: list[tuple[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE urls (url TEXT, last_visit_time INTEGER)")
        connection.executemany("INSERT INTO urls(url, last_visit_time) VALUES (?, ?)", rows)
        connection.commit()
    finally:
        connection.close()


def test_discovers_only_recent_pangram_uuid_history_urls(tmp_path: Path) -> None:
    history = tmp_path / "Default" / "History"
    newest = "https://www.pangram.com/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb?private=x#frag"
    older = "https://pangram.com/history/cccccccc-4444-5555-6666-dddddddddddd/"
    _write_history(
        history,
        [
            ("https://example.com/private-history", 999),
            (newest, 300),
            (older, 200),
            ("https://www.pangram.com/dashboard", 100),
            ("https://www.pangram.com/history/not-a-uuid", 50),
        ],
    )

    assert discover_pangram_history_urls(tmp_path) == (
        "https://www.pangram.com/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
        "https://www.pangram.com/history/cccccccc-4444-5555-6666-dddddddddddd",
    )


def test_deduplicates_across_profile_history_databases(tmp_path: Path) -> None:
    url = "https://www.pangram.com/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb"
    _write_history(tmp_path / "Default" / "History", [(url, 100)])
    _write_history(tmp_path / "Profile 1" / "History", [(url + "?x=1", 200)])

    assert discover_pangram_history_urls(tmp_path) == (url,)


def test_missing_or_invalid_history_database_is_nonfatal(tmp_path: Path) -> None:
    assert discover_pangram_history_urls(tmp_path) == ()

    broken = tmp_path / "Default" / "History"
    broken.parent.mkdir(parents=True)
    broken.write_text("not sqlite", encoding="utf-8")
    assert discover_pangram_history_urls(tmp_path) == ()


def test_limit_must_be_positive(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="positive"):
        discover_pangram_history_urls(tmp_path, limit=0)


class _Anchor:
    def __init__(self, href: str) -> None:
        self.href = href

    def get_attribute(self, name: str) -> str | None:
        assert name == "href"
        return self.href


class _Anchors:
    def __init__(self, hrefs: list[str]) -> None:
        self.hrefs = hrefs

    def count(self) -> int:
        return len(self.hrefs)

    def nth(self, index: int) -> _Anchor:
        return _Anchor(self.hrefs[index])


class _Page:
    def __init__(self, hrefs: list[str]) -> None:
        self.hrefs = hrefs

    def locator(self, selector: str) -> _Anchors:
        assert selector == "a[href]"
        return _Anchors(self.hrefs)


def test_discovers_rendered_result_links_without_leaking_unrelated_links() -> None:
    page = _Page(
        [
            "/dashboard",
            "/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb?private=1",
            "https://example.com/history/bbbbbbbb-1111-2222-3333-cccccccccccc",
            "https://pangram.com/history/cccccccc-4444-5555-6666-dddddddddddd/",
        ]
    )

    assert discover_pangram_history_urls_from_page(page) == (
        "https://www.pangram.com/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
        "https://www.pangram.com/history/cccccccc-4444-5555-6666-dddddddddddd",
    )


def test_discovers_rendered_history_navigation_without_result_links() -> None:
    page = _Page(
        [
            "/dashboard",
            "/dashboard?tab=history",
            "/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
            "https://example.com/history",
        ]
    )

    assert discover_pangram_history_navigation_urls_from_page(page) == (
        "https://www.pangram.com/dashboard?tab=history",
    )


def test_extracts_only_result_identifiers_from_in_memory_json_payload() -> None:
    payload = {
        "account_id": "99999999-1111-2222-3333-444444444444",
        "recent_scans": [
            {
                "id": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
                "private_text": "must not be returned",
            },
            {
                "dashboard_link": "https://www.pangram.com/history/cccccccc-4444-5555-6666-dddddddddddd?x=1",
            },
        ],
    }

    assert extract_pangram_history_urls_from_payload(payload) == (
        "https://www.pangram.com/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
        "https://www.pangram.com/history/cccccccc-4444-5555-6666-dddddddddddd",
    )
