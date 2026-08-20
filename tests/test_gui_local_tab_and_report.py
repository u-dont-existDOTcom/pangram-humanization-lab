from __future__ import annotations

from pathlib import Path

from pangram_lab import gui_local


class FakeBody:
    def __init__(self, text: str) -> None:
        self.text = text

    def inner_text(self) -> str:
        return self.text


class FakePage:
    def __init__(self, url: str, body: str = "") -> None:
        self.url = url
        self.body = body
        self.closed = False
        self.goto_calls: list[str] = []
        self.wait_hook = None

    def is_closed(self) -> bool:
        return self.closed

    def close(self, **kwargs: object) -> None:
        self.closed = True

    def goto(self, url: str, **kwargs: object) -> None:
        self.url = url
        self.goto_calls.append(url)

    def locator(self, selector: str) -> FakeBody:
        assert selector == "body"
        return FakeBody(self.body)

    def title(self) -> str:
        return "fake"

    def wait_for_timeout(self, milliseconds: int) -> None:
        if self.wait_hook is not None:
            hook = self.wait_hook
            self.wait_hook = None
            hook()


class FakeContext:
    def __init__(self, pages: list[FakePage]) -> None:
        self._pages = pages
        self.closed = False

    @property
    def pages(self) -> list[FakePage]:
        return [page for page in self._pages if not page.closed]

    def new_page(self) -> FakePage:
        page = FakePage("about:blank")
        self._pages.append(page)
        return page

    def close(self) -> None:
        self.closed = True


class FakePlaywright:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


def report_body(text: str) -> str:
    return (
        "Pangram 4.0\nAuthorship Breakdown\n100% Human Written\nAnalyzed Text\n"
        "Human Written | 3 Words | High Confidence\n"
        + text
    )


def test_normalize_context_tabs_closes_every_extra_tab() -> None:
    first = FakePage("https://www.pangram.com/dashboard")
    second = FakePage("https://www.pangram.com/history")
    third = FakePage("https://www.pangram.com/report/123")
    context = FakeContext([first, second, third])

    kept = gui_local.normalize_context_tabs(context, keep=second)

    assert kept is second
    assert context.pages == [second]
    assert first.closed is True
    assert third.closed is True


def test_close_local_session_leaves_blank_tab_state_and_stops_browser() -> None:
    first = FakePage("https://www.pangram.com/dashboard")
    second = FakePage("https://www.pangram.com/report/123")
    context = FakeContext([first, second])
    playwright = FakePlaywright()

    gui_local._close_local_session(playwright, context)

    assert first.closed is True
    assert second.goto_calls == ["about:blank"]
    assert context.closed is True
    assert playwright.stopped is True


def test_find_exact_report_ignores_dashboard_containing_exact_input() -> None:
    dashboard = FakePage("https://www.pangram.com/dashboard", "one two three")
    report = FakePage("https://www.pangram.com/report/123", report_body("one two three"))
    context = FakeContext([dashboard, report])

    matched = gui_local.find_exact_report_in_open_pages(
        context,
        "one two three",
        expected_word_count=3,
    )

    assert matched is not None
    page, body, parsed = matched
    assert page is report
    assert "Authorship Breakdown" in body
    assert sum(int(segment["word_count"]) for segment in parsed["segments"]) == 3


def test_wait_for_exact_report_page_detects_new_tab_after_submit() -> None:
    dashboard = FakePage("https://www.pangram.com/dashboard", "one two three")
    context = FakeContext([dashboard])

    def open_report() -> None:
        context._pages.append(
            FakePage("https://www.pangram.com/report/123", report_body("one two three"))
        )

    dashboard.wait_hook = open_report

    page, body, parsed = gui_local.wait_for_exact_report_page(
        context,
        "one two three",
        expected_word_count=3,
        timeout_ms=5_000,
        poll_ms=10,
        diagnostic_dir=Path("/tmp"),
    )

    assert page.url.endswith("/report/123")
    assert "100% Human Written" in body
    assert parsed["segments"][0]["label"] == "Human Written"
