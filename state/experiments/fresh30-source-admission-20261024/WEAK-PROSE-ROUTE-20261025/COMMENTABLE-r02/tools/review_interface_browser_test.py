#!/usr/bin/env python3
"""Browser-regression test for an exact packaged review HTML file.

The test first attempts the exact local file in headless Chromium, blocks external HTTP(S) requests, and exercises comments, focus-safe exact selected-text offsets, second-line sliders, full-draft mode, decisions, copy/export, search, filtering, reasoning, and persistence. When the execution environment blocks file and loopback navigation, it uses exact-HTML `page.set_content` with a deterministic Storage shim and reports that limitation rather than claiming local-file confirmation. It never edits the input files.

Usage:
  python review_interface_browser_test.py review.html \
    --article article.html --out browser-test.md --json-out browser-test.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import http.server
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import threading
import time
from typing import Any
from urllib.parse import quote, urlsplit

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

REVIEW_FORMAT = "joel-commentable-diff-review-v4"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.ids: set[str] = set()
        self._anchor_text: list[str] | None = None
        self._anchor_href = ""
        self._anchor_id = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {k.lower(): v or "" for k, v in attrs}
        if values.get("id"):
            self.ids.add(values["id"])
        if tag.lower() == "a":
            self._anchor_href = values.get("href", "")
            self._anchor_id = values.get("id", "")
            self._anchor_text = []

    def handle_data(self, data: str) -> None:
        if self._anchor_text is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._anchor_text is not None:
            self.links.append({"href": self._anchor_href, "text": " ".join(self._anchor_text).strip(), "id": self._anchor_id})
            self._anchor_text = None
            self._anchor_href = ""
            self._anchor_id = ""


def link_audit(path: Path) -> dict[str, Any]:
    parser = LinkParser()
    parser.feed(path.read_text(encoding="utf-8"))
    empty = []
    unresolved = []
    for link in parser.links:
        href, text, link_id = link["href"], link["text"], link["id"]
        if (not href or href == "#") and link_id != "downloadFallback":
            empty.append({"href": href, "text": text, "id": link_id})
        elif href.startswith("#") and href != "#" and href[1:] not in parser.ids:
            unresolved.append({"href": href, "text": text, "id": link_id})
    return {
        "link_count": len(parser.links),
        "empty_targets": empty,
        "unresolved_internal_fragments": unresolved,
        "attachment_to_intended_text": "manual editorial audit required",
    }


def record(results: list[dict[str, Any]], name: str, status: str, detail: str = "") -> None:
    results.append({"test": name, "status": status, "detail": detail})


def first_text_cell(page, exclude_selector: str = "") -> str:
    selectors = page.locator('.diff-cell[data-cell-key]:not(.empty)')
    count = selectors.count()
    for i in range(count):
        cell = selectors.nth(i)
        key = cell.get_attribute("data-cell-key") or ""
        if exclude_selector and key == exclude_selector:
            continue
        text = (cell.locator(".passage-wrap").inner_text() or "").strip()
        if len(text) >= 8:
            return f'[data-cell-key="{key}"]'
    raise RuntimeError("no non-empty review cell with enough text")


def set_slider(page, cell_selector: str, slider_selector: str, value: int) -> None:
    page.eval_on_selector(
        f"{cell_selector} {slider_selector}",
        """(el, value) => { el.value = String(value); el.dispatchEvent(new Event('input', {bubbles:true})); }""",
        value,
    )


def select_text_and_open_comment(page, cell_selector: str, length: int = 12) -> dict[str, Any]:
    """Select exact text, snapshot it on pointerdown, clear browser selection, then click.

    Clearing the live selection before click simulates the real-browser focus change that
    previously caused highlighted-word notes to fall back to the whole passage.
    """
    return page.evaluate(
        """({selector, length}) => {
          const cell = document.querySelector(selector);
          const passage = cell.querySelector('.passage');
          const walker = document.createTreeWalker(passage, NodeFilter.SHOW_TEXT);
          let node = walker.nextNode();
          while (node && (!node.textContent || node.textContent.length < 6)) node = walker.nextNode();
          if (!node || !node.textContent) throw new Error('No usable text node');
          const start = Math.min(2, Math.max(0, node.textContent.length - 1));
          const end = Math.min(start + length, node.textContent.length);
          const range = document.createRange(); range.setStart(node, start); range.setEnd(node, end);
          const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
          const quote = selection.toString();
          const button = cell.querySelector('.comment-btn');
          button.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true, pointerType:'mouse'}));
          selection.removeAllRanges();
          button.click();
          return {quote, start, end};
        }""",
        {"selector": cell_selector, "length": length},
    )


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def start_loopback_server(root: Path) -> tuple[http.server.ThreadingHTTPServer, threading.Thread]:
    handler = functools.partial(QuietHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def loopback_url(server: http.server.ThreadingHTTPServer, root: Path, path: Path) -> str:
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    return f"http://127.0.0.1:{server.server_port}/{quote(rel)}"


def check_review_control_contrast(page) -> dict[str, Any]:
    return page.evaluate("""() => {
      const lum=s=>{const v=s.match(/[\d.]+/g).slice(0,3).map(Number).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return v[0]*.2126+v[1]*.7152+v[2]*.0722;};
      const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
      const bad=[];let count=0,min=100;
      for(const el of document.querySelectorAll('textarea,select,option,optgroup,input[type=search],input[type=text]')){
        const s=getComputedStyle(el);count++;
        if(s.backgroundColor==='rgba(0, 0, 0, 0)'){bad.push({id:el.id,reason:'transparent field background'});continue;}
        const colors=[s.color,s.webkitTextFillColor||s.color];
        if(el.matches('input,textarea'))colors.push(s.caretColor,getComputedStyle(el,'::placeholder').color);
        for(const color of colors){const r=ratio(color,s.backgroundColor);min=Math.min(min,r);if(r<4.5)bad.push({id:el.id,tag:el.tagName,color,bg:s.backgroundColor,contrast:r});}
      }return {count,minContrast:min,bad};
    }""")


def run_browser_test(review: Path, article: Path | None, timeout_ms: int) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    console_errors: list[str] = []
    page_errors: list[str] = []
    blocked_requests: list[str] = []
    exported_json: dict[str, Any] | None = None
    exported_markdown = ""
    load_seconds = 0.0
    navigation_mode = "file://"
    loopback_server: http.server.ThreadingHTTPServer | None = None
    loopback_thread: threading.Thread | None = None
    served_root = Path(os.path.commonpath([str(review.resolve().parent)] + ([str(article.resolve().parent)] if article else [])))

    with sync_playwright() as p:
        system_chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
        launch_args: dict[str, Any] = {"headless": True}
        if system_chromium:
            launch_args["executable_path"] = system_chromium
        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(accept_downloads=True)
        context.set_default_timeout(timeout_ms)
        context.add_init_script(
            """
            Object.defineProperty(navigator, 'clipboard', {
              configurable: true,
              value: { writeText: async text => { window.__reviewTestClipboard = String(text); } }
            });
            """
        )

        def block_network(route) -> None:
            host = (urlsplit(route.request.url).hostname or "").lower()
            if host in {"127.0.0.1", "localhost"}:
                route.continue_()
                return
            blocked_requests.append(route.request.url)
            route.abort()

        context.route(re.compile(r"^https?://"), block_network)
        page = context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        started = time.perf_counter()
        try:
            page.goto(review.resolve().as_uri(), wait_until="load")
        except PlaywrightError as file_exc:
            navigation_mode = "loopback-http-fallback"
            loopback_server, loopback_thread = start_loopback_server(served_root)
            try:
                page.goto(loopback_url(loopback_server, served_root, review), wait_until="load")
            except PlaywrightError as http_exc:
                navigation_mode = "page.set_content-fallback"
                page.close()
                page = context.new_page()
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                page.evaluate(
                    """() => {
                      const store = {};
                      Object.defineProperty(window, 'localStorage', {configurable:true, value:{
                        getItem:key => Object.prototype.hasOwnProperty.call(store,key) ? store[key] : null,
                        setItem:(key,value) => { store[key] = String(value); },
                        removeItem:key => { delete store[key]; },
                        clear:() => { Object.keys(store).forEach(key => delete store[key]); }
                      }});
                      Object.defineProperty(navigator, 'clipboard', {configurable:true, value:{
                        writeText: async text => { window.__reviewTestClipboard = String(text); }
                      }});
                    }"""
                )
                page.set_content(review.read_text(encoding="utf-8"), wait_until="load")
                record(results, "local-file navigation", "not-applicable", f"file:// and loopback navigation blocked; exact HTML tested with page.set_content. file error: {file_exc}; loopback error: {http_exc}")
            else:
                record(results, "local-file navigation", "not-applicable", f"file:// blocked; exact file tested via loopback HTTP: {file_exc}")
        else:
            record(results, "local-file navigation", "pass", "file://")
        load_seconds = time.perf_counter() - started
        record(results, "open exact review file", "pass", f"{navigation_mode}; loaded in {load_seconds:.3f}s")
        record(results, "offline review", "pass" if not blocked_requests else "fail", f"external requests blocked: {len(blocked_requests)}")

        required_selectors = [
            "#search", "#changedOnly", "#openDrawer", "#exportJson", "#exportMd",
            "#copyJson", "#copyMd", "#commentOverlay", "#reasonOverlay",
            ".keep-btn", ".remove-btn", ".brainstorm-btn",
            ".humor-slider", ".tech-slider", ".length-slider", ".blunt-slider",
        ]
        missing = [selector for selector in required_selectors if page.locator(selector).count() == 0]
        record(results, "fixed interface controls", "pass" if not missing else "fail", ", ".join(missing))

        meta = page.eval_on_selector("#review-data", "el => JSON.parse(el.textContent)")
        declared_format = meta.get("interface_format") or (REVIEW_FORMAT if REVIEW_FORMAT in review.read_text(encoding="utf-8") else "")
        record(results, "review format", "pass" if declared_format == REVIEW_FORMAT else "fail", str(declared_format))
        view_mode = meta.get("view_mode") or "comparison"
        record(results, "view mode", "pass" if view_mode in {"comparison", "full-draft"} else "fail", str(view_mode))
        first_cell_for_layout = first_text_cell(page)
        layout = page.eval_on_selector(first_cell_for_layout, """cell => {
          const head=cell.querySelector('.cell-headline').getBoundingClientRect();
          const tuners=cell.querySelector('.tuners').getBoundingClientRect();
          return {headline_bottom:head.bottom,tuners_top:tuners.top,technical_label:cell.querySelector('.tech-slider').getAttribute('aria-label')};
        }""")
        slider_line_ok = layout["tuners_top"] >= layout["headline_bottom"] - 1 and layout["technical_label"] == "Technical detail"
        record(results, "sliders on second line with clear technical label", "pass" if slider_line_ok else "fail", json.dumps(layout))
        if view_mode == "full-draft":
            single_ok = page.locator("body.single-view").count() == 1 and page.locator(".diff-row").count() == page.locator(".diff-cell[data-cell-key]").count() and page.locator(".diff-cell.empty").count() == 0
            record(results, "full-draft one-column commentable layout", "pass" if single_ok else "fail")

        cell_one = first_text_cell(page)
        key_one = page.locator(cell_one).get_attribute("data-cell-key") or ""
        try:
            cell_two = first_text_cell(page, key_one)
        except RuntimeError:
            cell_two = ""

        # Whole-cell comment lifecycle.
        page.locator(f"{cell_one} .comment-btn").click()
        page.locator("#commentText").fill("whole-cell comment")
        stress = page.add_style_tag(content=':root{color-scheme:dark !important}')
        for scheme in ("light", "dark"):
            page.emulate_media(color_scheme=scheme)
            contrast_report = check_review_control_contrast(page)
            record(results, "typed text and native control contrast: " + scheme,
                   "pass" if contrast_report["count"] > 0 and not contrast_report["bad"] else "fail", json.dumps(contrast_report))
        stress.evaluate("el => el.remove()")
        page.emulate_media(color_scheme="light")
        page.locator("#saveComment").click()
        saved = page.locator(cell_one).evaluate("el => el.classList.contains('has-comment')")
        page.locator(f"{cell_one} .comment-btn").click()
        page.locator("#commentText").fill("unsaved replacement")
        page.keyboard.press("Escape")
        page.locator(f"{cell_one} .comment-btn").click()
        escaped_value = page.locator("#commentText").input_value()
        page.locator("#commentText").fill("edited first line")
        page.locator("#commentText").press("Shift+Enter")
        page.locator("#commentText").type("second line")
        page.locator("#commentText").press("Enter")
        page.locator(f"{cell_one} .comment-btn").click()
        edited_value = page.locator("#commentText").input_value()
        page.locator("#clearComment").click()
        cleared = not page.locator(cell_one).evaluate("el => el.classList.contains('has-comment')")
        lifecycle_ok = saved and escaped_value == "whole-cell comment" and "second line" in edited_value and cleared
        record(results, "whole-cell comment create/reopen/edit/delete and Enter/Shift+Enter/Escape", "pass" if lifecycle_ok else "fail")

        # Selected-text comment and exact offsets.
        selection_result = select_text_and_open_comment(page, cell_one)
        selected_quote = selection_result["quote"]
        quote_shown = page.locator("#commentQuote").inner_text()
        selected_comment = "selected-text comment — verbatim"
        page.locator("#commentText").fill(selected_comment)
        page.locator("#saveComment").click()
        record(results, "selected-text comment survives toolbar focus", "pass" if selected_quote == quote_shown and bool(selected_quote) else "fail", selected_quote)

        # A separate whole-passage comment adds export coverage when the review has another cell.
        whole_comment = "whole-passage export comment"
        if cell_two:
            page.locator(f"{cell_two} .comment-btn").click()
            page.locator("#commentText").fill(whole_comment)
            page.locator("#saveComment").click()
        else:
            record(results, "separate whole-passage export comment", "not-applicable", "review has only one non-empty cell")

        # Decisions and history.
        decision_states = []
        for button_class, expected in (("keep-btn", "keep"), ("remove-btn", "remove"), ("brainstorm-btn", "brainstorm"), ("keep-btn", "keep")):
            page.locator(f"{cell_one} .{button_class}").click()
            if button_class == "brainstorm-btn" and page.locator("#commentOverlay").evaluate("el => el.classList.contains('open')"):
                page.keyboard.press("Escape")
            active = page.locator(cell_one).get_attribute("class") or ""
            decision_states.append(f"decision-{expected}" in active)
        record(results, "Keep/Remove/Brainstorm and supersession", "pass" if all(decision_states) else "fail")

        slider_values = {".humor-slider": 4, ".tech-slider": 0, ".length-slider": 3, ".blunt-slider": 1}
        for selector, value in slider_values.items():
            set_slider(page, cell_one, selector, value)
        current = {selector: int(page.locator(f"{cell_one} {selector}").input_value()) for selector in slider_values}
        record(results, "four sliders", "pass" if current == slider_values else "fail", json.dumps(current))

        page.locator(f"{cell_one} .why-btn").click()
        reason_open = page.locator("#reasonOverlay").evaluate("el => el.classList.contains('open')")
        reason_text = page.locator("#reasonSummary").inner_text()
        page.keyboard.press("Escape")
        record(results, "reasoning panel", "pass" if reason_open and bool(reason_text.strip()) else "fail")

        relation = page.locator('.relation-chip[data-target-row]:not([data-target-row=""])')
        if relation.count():
            target = relation.first.get_attribute("data-target-row") or ""
            relation.first.click()
            record(results, "moved/consolidated destination jump", "pass" if page.locator(f"#{target}").count() else "fail", target)
        else:
            record(results, "moved/consolidated destination jump", "not-applicable", "no moved/consolidated row in this review")

        if view_mode == "comparison":
            equal_rows = page.locator(".diff-row.state-equal").count()
            page.locator("#changedOnly").click()
            changed_class = page.locator("body").evaluate("el => el.classList.contains('changed-only')")
            hidden_equal = page.locator(".diff-row.state-equal").evaluate_all(
                "els => els.every(el => getComputedStyle(el).display === 'none')"
            ) if equal_rows else True
            page.locator("#changedOnly").click()
            record(results, "changed-only filtering", "pass" if changed_class and hidden_equal else "fail", f"equal rows: {equal_rows}")
        else:
            hidden_filter = page.locator("#changedOnly").evaluate("el => getComputedStyle(el).display === 'none'")
            record(results, "changed-only filter hidden in full-draft mode", "pass" if hidden_filter else "fail")

        passage_text = page.locator(f"{cell_one} .passage-wrap").inner_text().strip()
        token_match = re.search(r"[A-Za-z0-9]{4,}", passage_text)
        token = token_match.group(0) if token_match else passage_text[:4]
        page.locator("#search").fill(token)
        visible_rows = page.locator(".diff-row:not(.search-miss)").count()
        page.locator("#search").fill("")
        record(results, "search", "pass" if visible_rows >= 1 else "fail", token)

        # Copy and export controls live in the review drawer.
        if not page.locator("#drawer").evaluate("el => el.classList.contains('open')"):
            page.locator("#openDrawer").click()
        # Copy actions use an injected deterministic clipboard sink.
        page.locator("#copyJson").click()
        page.wait_for_timeout(50)
        copied_json = page.evaluate("window.__reviewTestClipboard || ''")
        copy_json_ok = False
        try:
            copied_obj = json.loads(copied_json)
            copy_json_ok = copied_obj.get("format") == REVIEW_FORMAT
        except Exception:
            copied_obj = {}
        page.locator("#copyMd").click()
        page.wait_for_timeout(50)
        copied_md = page.evaluate("window.__reviewTestClipboard || ''")
        record(results, "Copy JSON", "pass" if copy_json_ok else "fail")
        record(results, "Copy Markdown", "pass" if selected_comment in copied_md else "fail")

        with tempfile.TemporaryDirectory(prefix="review-browser-download-") as td:
            td_path = Path(td)
            with page.expect_download() as download_info:
                page.locator("#exportJson").click()
            json_download = download_info.value
            json_path = td_path / (json_download.suggested_filename or "review.json")
            json_download.save_as(json_path)
            exported_json = json.loads(json_path.read_text(encoding="utf-8"))

            with page.expect_download() as download_info:
                page.locator("#exportMd").click()
            md_download = download_info.value
            md_path = td_path / (md_download.suggested_filename or "review.md")
            md_download.save_as(md_path)
            exported_markdown = md_path.read_text(encoding="utf-8")

        items = exported_json.get("items", []) if isinstance(exported_json, dict) else []
        selected_items = [item for item in items if item.get("comment") == selected_comment]
        whole_items = [item for item in items if item.get("comment") == whole_comment]
        offsets_ok = bool(selected_items) and selected_items[0].get("comment_scope") == "selected-text" and selected_items[0].get("selected_quote") == selected_quote and selected_items[0].get("selected_quote_start") == selection_result["start"] and selected_items[0].get("selected_quote_end") == selection_result["end"]
        decision_history_ok = bool(selected_items) and len(selected_items[0].get("decision_history") or []) >= 4
        whole_export_ok = bool(whole_items) if cell_two else True
        export_ok = exported_json.get("format") == REVIEW_FORMAT and offsets_ok and whole_export_ok and selected_comment in exported_markdown and decision_history_ok
        record(results, "JSON/Markdown export and parse", "pass" if export_ok else "fail", f"items: {len(items)}")

        # Reload persistence. When navigation is blocked by the execution environment,
        # re-inject the exact HTML into the same window so the deterministic Storage shim remains.
        if navigation_mode == "page.set_content-fallback":
            page.set_content(review.read_text(encoding="utf-8"), wait_until="load")
        else:
            page.reload(wait_until="load")
        persisted_comment = page.locator(cell_one).evaluate("el => el.classList.contains('has-comment')")
        persisted_sliders = {selector: int(page.locator(f"{cell_one} {selector}").input_value()) for selector in slider_values}
        persisted_decision = "decision-keep" in (page.locator(cell_one).get_attribute("class") or "")
        persistence_ok = persisted_comment and persisted_sliders == slider_values and persisted_decision
        record(results, "reload and local persistence", "pass" if persistence_ok else "fail")

        if article:
            article_page = context.new_page()
            article_console: list[str] = []
            article_page.on("console", lambda msg: article_console.append(msg.text) if msg.type == "error" else None)
            if navigation_mode == "file://":
                article_page.goto(article.resolve().as_uri(), wait_until="load")
            elif navigation_mode == "loopback-http-fallback":
                article_page.goto(loopback_url(loopback_server, served_root, article), wait_until="load")
            else:
                article_page.set_content(article.read_text(encoding="utf-8"), wait_until="load")
            text_ok = bool(article_page.locator("body").inner_text().strip())
            record(results, "open packaged article as local file", "pass" if text_ok and not article_console else "fail", f"console errors: {len(article_console)}")
            article_page.close()

        record(results, "no console errors", "pass" if not console_errors else "fail", " | ".join(console_errors))
        record(results, "no page errors", "pass" if not page_errors else "fail", " | ".join(page_errors))
        browser.close()
        if loopback_server:
            loopback_server.shutdown()
            loopback_server.server_close()
        if loopback_thread:
            loopback_thread.join(timeout=2)

    review_links = link_audit(review)
    record(results, "review links: empty and internal fragments", "pass" if not review_links["empty_targets"] and not review_links["unresolved_internal_fragments"] else "fail", json.dumps(review_links))
    article_links = link_audit(article) if article else None
    if article_links:
        record(results, "article links: empty and internal fragments", "pass" if not article_links["empty_targets"] and not article_links["unresolved_internal_fragments"] else "fail", json.dumps(article_links))

    failures = [item for item in results if item["status"] == "fail"]
    return {
        "format": "joel-review-browser-test-v1",
        "tested_utc": utc_now(),
        "browser": "Chromium via Playwright",
        "review_file": review.name,
        "review_sha256": sha256_file(review),
        "article_file": article.name if article else "",
        "article_sha256": sha256_file(article) if article else "",
        "navigation_mode": navigation_mode,
        "network_policy": "external HTTP(S) requests blocked; loopback allowed only when file:// was unavailable",
        "clipboard_test": "deterministic injected writeText sink; browser permission path remains destination-specific",
        "load_seconds": round(load_seconds, 3),
        "result": "pass" if not failures else "fail",
        "tests": results,
        "blocked_requests": blocked_requests,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "limitations": [
            "Link attachment to the intended phrase requires editorial comparison with the authoritative source.",
            "When navigation_mode is page.set_content-fallback, controls and persistence use an exact-HTML injection plus deterministic Storage shim; this does not prove local-file navigation. This run never proves Opera-specific behavior or publication-platform reconstruction.",
            "A modest-laptop claim requires testing on that class of machine; this report records only the current environment.",
        ],
    }


def markdown_report(data: dict[str, Any]) -> str:
    lines = [
        "# Review Interface Browser Test",
        "",
        f"- **Result:** {data['result']}",
        f"- **Tested UTC:** {data['tested_utc']}",
        f"- **Browser:** {data['browser']}",
        f"- **Review:** `{data['review_file']}` — `{data['review_sha256']}`",
        f"- **Article:** `{data['article_file']}` — `{data['article_sha256']}`" if data.get("article_file") else "- **Article:** not supplied",
        f"- **Review load:** {data['load_seconds']} seconds",
        f"- **Navigation:** {data.get('navigation_mode', '')}",
        f"- **Network policy:** {data['network_policy']}",
        f"- **Clipboard path:** {data['clipboard_test']}",
        "",
        "## Tests",
        "",
        "| Test | Status | Detail |",
        "|---|---|---|",
    ]
    for item in data["tests"]:
        detail = str(item.get("detail", "")).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {item['test']} | {item['status']} | {detail} |")
    lines.extend(["", "## Limitations", ""])
    for limitation in data["limitations"]:
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path)
    parser.add_argument("--article", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--timeout-ms", type=int, default=10000)
    args = parser.parse_args()
    if not args.review.is_file():
        parser.error("review file does not exist")
    if args.article and not args.article.is_file():
        parser.error("article file does not exist")

    try:
        data = run_browser_test(args.review, args.article, args.timeout_ms)
    except Exception as exc:
        data = {
            "format": "joel-review-browser-test-v1",
            "tested_utc": utc_now(),
            "result": "fail",
            "browser": "Chromium via Playwright",
            "review_file": args.review.name,
            "review_sha256": sha256_file(args.review),
            "article_file": args.article.name if args.article else "",
            "article_sha256": sha256_file(args.article) if args.article else "",
            "load_seconds": 0,
            "navigation_mode": "not completed",
            "network_policy": "external HTTP(S) requests intended to be blocked",
            "clipboard_test": "not completed",
            "tests": [{"test": "browser run", "status": "fail", "detail": f"{type(exc).__name__}: {exc}"}],
            "blocked_requests": [],
            "console_errors": [],
            "page_errors": [],
            "limitations": ["Browser automation failed before the full test sequence completed."],
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown_report(data), encoding="utf-8")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": data["result"], "report": str(args.out)}, indent=2))
    return 0 if data["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
