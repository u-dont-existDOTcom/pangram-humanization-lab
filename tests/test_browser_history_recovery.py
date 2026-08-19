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
    def __init__(self, href: str, label: str = "", aria_label: str = "", title: str = "") -> None:
        self.href = href
        self.label = label
        self.aria_label = aria_label
        self.title = title

    def get_attribute(self, name: str) -> str | None:
        if name == "href":
            return self.href
        if name == "aria-label":
            return self.aria_label
        if name == "title":
            return self.title
        return None

    def inner_text(self) -> str:
        return self.label


class _Anchors:
    def __init__(self, anchors: list[_Anchor]) -> None:
        self.anchors = anchors

    def count(self) -> int:
        return len(self.anchors)

    def nth(self, index: int) -> _Anchor:
        return self.anchors[index]


class _Page:
    def __init__(self, anchors: list[_Anchor]) -> None:
        self.anchors = anchors

    def locator(self, selector: str) -> _Anchors:
        assert selector == "a[href]"
        return _Anchors(self.anchors)


def test_discovers_rendered_result_links_without_leaking_unrelated_links() -> None:
    page = _Page(
        [
            _Anchor("/dashboard"),
            _Anchor("/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb?private=1", "View Results"),
            _Anchor("https://example.com/history/bbbbbbbb-1111-2222-3333-cccccccccccc"),
            _Anchor("https://pangram.com/history/cccccccc-4444-5555-6666-dddddddddddd/", "View Results"),
        ]
    )

    assert discover_pangram_history_urls_from_page(page) == (
        "https://www.pangram.com/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
        "https://www.pangram.com/history/cccccccc-4444-5555-6666-dddddddddddd",
    )


def test_discovers_rendered_history_navigation_without_result_links() -> None:
    page = _Page(
        [
            _Anchor("/dashboard"),
            _Anchor("/dashboard?tab=history", "History"),
            _Anchor("/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb", "View Results"),
            _Anchor("https://example.com/history", "History"),
        ]
    )

    assert discover_pangram_history_navigation_urls_from_page(page) == (
        "https://www.pangram.com/dashboard?tab=history",
    )


def test_discovers_current_all_checks_navigation_by_label_even_without_history_in_url() -> None:
    page = _Page(
        [
            _Anchor("/dashboard", "Detector"),
            _Anchor("/dashboard/checks", "All Checks"),
            _Anchor("/dashboard/groups", "Groups"),
        ]
    )

    assert discover_pangram_history_navigation_urls_from_page(page) == (
        "https://www.pangram.com/dashboard/checks",
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


def test_extracts_current_check_document_uuid_context_but_not_account_uuid() -> None:
    payload = {
        "account": {"id": "99999999-1111-2222-3333-444444444444"},
        "all_checks": [
            {"document_id": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb"},
        ],
        "submissions": [
            {"result_id": "cccccccc-4444-5555-6666-dddddddddddd"},
        ],
    }

    assert extract_pangram_history_urls_from_payload(payload) == (
        "https://www.pangram.com/history/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
        "https://www.pangram.com/history/cccccccc-4444-5555-6666-dddddddddddd",
    )
