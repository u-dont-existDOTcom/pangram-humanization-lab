from __future__ import annotations

import hashlib
import html as html_lib
import json
import re
import sys
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

_BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "div", "dl", "dt", "dd",
    "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
    "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table",
    "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
}
_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "iframe", "template"}
_RETRYABLE_HTTP = {429, 500, 502, 503, 504}

_EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>()]+")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d().\-\s]{7,}\d)(?!\w)")
_TIMESTAMP_SUFFIX_RE = re.compile(
    r",?\s*(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"\d{1,2}\s+\d{4},\s+\d{1,2}:\d{2}\s*(?:AM|PM)(?:\s+via\s+\w+)?(?:\s*·.*)?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CanonicalText:
    text: str
    sha256: str
    word_count: int
    redactions: dict[str, int]
    quality_flags: list[str]


class PostBodyParser(HTMLParser):
    """Extract authored body text from common Blogger/Substack-ish HTML.

    Visible anchor text is preserved while href values are ignored. Extraction
    is intentionally conservative: if no recognized body container exists, the
    caller should fail instead of silently modeling a complete web page.
    """

    def __init__(self, *, drop_blockquotes: bool = False):
        super().__init__(convert_charrefs=True)
        self.drop_blockquotes = drop_blockquotes
        self.capture = False
        self.capture_depth = 0
        self.skip_depth = 0
        self.quote_depth = 0
        self.parts: list[str] = []
        self.found_body = False

    @staticmethod
    def _is_body(tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        attr = {k.lower(): (v or "") for k, v in attrs}
        classes = set(attr.get("class", "").split())
        if "post-body" in classes or "entry-content" in classes:
            return True
        if attr.get("itemprop", "").lower() in {"articlebody", "text"}:
            return True
        if tag == "article" and ("post" in classes or "entry" in classes):
            return True
        return False

    def _sep(self, value: str = "\n") -> None:
        if self.capture and not self.skip_depth and not self.quote_depth:
            self.parts.append(value)

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        if not self.capture:
            if self._is_body(tag, attrs):
                self.capture = True
                self.found_body = True
                self.capture_depth = 1
            return

        if tag not in _VOID_TAGS:
            self.capture_depth += 1
        if tag in _SKIP_TAGS:
            self.skip_depth += 1
        if self.drop_blockquotes and tag == "blockquote":
            self.quote_depth += 1
        if tag in _BLOCK_TAGS:
            self._sep()

    def handle_startendtag(self, tag: str, attrs):
        if self.capture and tag.lower() in _BLOCK_TAGS:
            self._sep()

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if not self.capture:
            return
        if tag in _BLOCK_TAGS:
            self._sep()
        if tag in _SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        if self.drop_blockquotes and tag == "blockquote" and self.quote_depth:
            self.quote_depth -= 1
        if tag not in _VOID_TAGS:
            self.capture_depth -= 1
        if self.capture_depth <= 0:
            self.capture = False

    def handle_data(self, data: str):
        if self.capture and not self.skip_depth and not self.quote_depth:
            self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def _clean_line(line: str) -> str:
    line = html_lib.unescape(line).replace("\u00a0", " ")
    return re.sub(r"[ \t]+", " ", line).strip()


def normalize_visible_text(text: str) -> str:
    lines = [
        _clean_line(line)
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    out: list[str] = []
    for line in lines:
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        out.append(line)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out).strip()


def redact_nonstyle_tokens(text: str) -> tuple[str, dict[str, int]]:
    counts = {"email": 0, "phone": 0, "url": 0}

    def sub_count(pattern: re.Pattern, key: str, value: str) -> str:
        def repl(match):
            counts[key] += 1
            return ""

        return pattern.sub(repl, value)

    text = sub_count(_EMAIL_RE, "email", text)
    text = sub_count(_URL_RE, "url", text)
    text = sub_count(_PHONE_RE, "phone", text)
    return normalize_visible_text(text), counts


def _dedupe_adjacent(lines: Iterable[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        line = _clean_line(line)
        if not line:
            continue
        if out and out[-1] == line:
            continue
        out.append(line)
    return out


def extract_speaker_lines(text: str, speaker: str) -> str:
    """Keep explicit speaker-prefixed lines from imported discussion pages."""
    pat = re.compile(rf"^\s*{re.escape(speaker)}\s*:?\s*(.+?)\s*$", re.IGNORECASE)
    kept: list[str] = []
    for line in text.splitlines():
        m = pat.match(line)
        if not m:
            continue
        value = _TIMESTAMP_SUFFIX_RE.sub("", m.group(1)).strip()
        if value:
            kept.append(value)
    return "\n\n".join(_dedupe_adjacent(kept))


def extract_message_by_you(text: str) -> str:
    """Keep explicit Messenger-export turns marked ``Message by You:``."""
    pat = re.compile(r"^\s*Message by You:\s*(.+?)\s*$", re.IGNORECASE)
    kept: list[str] = []
    for line in text.splitlines():
        m = pat.match(line)
        if not m:
            continue
        value = _TIMESTAMP_SUFFIX_RE.sub("", m.group(1)).strip()
        if value:
            kept.append(value)
    return "\n\n".join(_dedupe_adjacent(kept))


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))


def canonicalize(text: str) -> CanonicalText:
    text = normalize_visible_text(text)
    text, redactions = redact_nonstyle_tokens(text)
    wc = word_count(text)
    flags: list[str] = []
    if wc < 100:
        flags.append("short-under-100-words")
    if wc < 250:
        flags.append("thin-for-authorship-attribution")
    if re.search(
        r"(?im)^\s*(?:Q:|Question:|Message by (?!You:)|[A-Z][A-Za-z .'-]{1,50}:)",
        text,
    ):
        flags.append("possible-unremoved-dialogue")
    if "Posted by" in text or "Email This" in text or "BlogThis!" in text:
        flags.append("possible-platform-chrome")
    data = text.encode("utf-8")
    return CanonicalText(
        text=text,
        sha256=hashlib.sha256(data).hexdigest(),
        word_count=wc,
        redactions=redactions,
        quality_flags=flags,
    )


def _retry_after_seconds(exc: HTTPError, *, attempt: int) -> float:
    raw = (exc.headers.get("Retry-After") or "").strip() if exc.headers else ""
    if raw.isdigit():
        return min(60.0, max(0.0, float(raw)))
    if raw:
        try:
            target = parsedate_to_datetime(raw)
            if target.tzinfo is None:
                target = target.replace(tzinfo=timezone.utc)
            return min(60.0, max(0.0, target.timestamp() - time.time()))
        except (TypeError, ValueError, OverflowError):
            pass
    return min(30.0, 1.5 * (2 ** attempt))


def fetch_html(url: str, *, timeout: int = 30, max_attempts: int = 5) -> tuple[str, str]:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; pangram-humanization-lab idiolect corpus acquisition)"
        },
    )
    for attempt in range(max_attempts):
        try:
            with urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                encoding = resp.headers.get_content_charset() or "utf-8"
            return body.decode(encoding, errors="replace"), hashlib.sha256(body).hexdigest()
        except HTTPError as exc:
            if exc.code not in _RETRYABLE_HTTP or attempt >= max_attempts - 1:
                raise
            time.sleep(_retry_after_seconds(exc, attempt=attempt))
    raise RuntimeError("unreachable retry loop")


def extract_blogspot(html: str, *, mode: str) -> str:
    drop_quotes = (
        mode in {"post-body-drop-blockquotes", "message-by-you"}
        or mode.startswith("speaker-prefix:")
    )
    parser = PostBodyParser(drop_blockquotes=drop_quotes)
    parser.feed(html)
    if not parser.found_body:
        raise ValueError("no recognized authored post-body container found")
    text = normalize_visible_text(parser.text())
    if mode.startswith("speaker-prefix:"):
        speaker = mode.split(":", 1)[1].strip()
        text = extract_speaker_lines(text, speaker)
    elif mode == "message-by-you":
        text = extract_message_by_you(text)
    elif mode not in {"post-body", "post-body-drop-blockquotes"}:
        raise ValueError(f"unsupported extraction mode: {mode}")
    return text


def iter_inventory_items(inventory: dict) -> Iterable[dict]:
    for source in inventory.get("sources", []):
        common = {
            "parent_source_id": source.get("source_id"),
            "source_group": source.get("source_group"),
            "provenance": source.get("provenance"),
            "modality": source.get("modality"),
            "registers": source.get("registers", []),
        }
        nested = source.get("known_posts") or source.get("known_threads")
        if nested:
            for item in nested:
                yield {**common, **item}
            continue
        if source.get("canonical_url") and source.get("capture_status") == "public-captured":
            yield {
                **common,
                "sample_id": source["source_id"],
                "title": source.get("title"),
                "date": source.get("date"),
                "url": source["canonical_url"],
                "extraction_mode": source.get("extraction_mode", "manual-review"),
            }


def acquire_inventory(
    inventory_path: Path,
    *,
    out_dir: Path,
    manifest_out: Path,
    sample_ids: set[str] | None = None,
    timeout: int = 30,
) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    errors: list[dict] = []

    for item in iter_inventory_items(inventory):
        sample_id = item.get("sample_id")
        if not sample_id or (sample_ids and sample_id not in sample_ids):
            continue
        mode = item.get("extraction_mode", "manual-review")
        url = item.get("url")
        if not url:
            errors.append({"sample_id": sample_id, "error": "no-url"})
            continue
        if mode == "manual-review":
            errors.append({"sample_id": sample_id, "url": url, "error": "manual-review-required"})
            continue
        try:
            raw_html, raw_sha = fetch_html(url, timeout=timeout)
            host = re.sub(r"^https?://", "", url).split("/", 1)[0].lower()
            if host.endswith("blogspot.com"):
                visible = extract_blogspot(raw_html, mode=mode)
            else:
                raise ValueError(f"no extractor for host: {host}")
            canon = canonicalize(visible)
            path = out_dir / f"{sample_id}.txt"
            path.write_text(canon.text + "\n", encoding="utf-8")
            results.append(
                {
                    "sample_id": sample_id,
                    "parent_source_id": item.get("parent_source_id"),
                    "source_group": item.get("source_group"),
                    "title": item.get("title"),
                    "date": item.get("date"),
                    "url": url,
                    "provenance": item.get("provenance"),
                    "modality": item.get("modality"),
                    "registers": item.get("registers", []),
                    "extraction_mode": mode,
                    "source_html_sha256": raw_sha,
                    "canonical_sha256": canon.sha256,
                    "word_count": canon.word_count,
                    "redactions": canon.redactions,
                    "quality_flags": canon.quality_flags,
                    "local_text_path": str(path),
                }
            )
        except Exception as exc:
            errors.append({"sample_id": sample_id, "url": url, "error": str(exc)})

    runtime = {
        "inventory": str(inventory_path),
        "raw_text_committed": False,
        "results": results,
        "errors": errors,
    }
    manifest_out.write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return runtime


def add_cli_parsers(subparsers) -> None:
    p = subparsers.add_parser(
        "idiolect-corpus-acquire",
        help="Fetch and canonicalize public Joel corpus sources into a gitignored local corpus.",
    )
    p.add_argument(
        "inventory",
        nargs="?",
        default="state/IDIOLECT-CORPUS-SOURCE-INVENTORY-2026-08-18.json",
    )
    p.add_argument("--out-dir", default=".local/idiolect-corpus/text")
    p.add_argument(
        "--manifest-out", default=".local/idiolect-corpus/acquisition-manifest.json"
    )
    p.add_argument("--sample-id", action="append", default=[])
    p.add_argument("--timeout", type=int, default=30)


def run_cli(args) -> int:
    runtime = acquire_inventory(
        Path(args.inventory),
        out_dir=Path(args.out_dir),
        manifest_out=Path(args.manifest_out),
        sample_ids=set(args.sample_id) if args.sample_id else None,
        timeout=args.timeout,
    )
    print(
        json.dumps(
            {
                "acquired": len(runtime["results"]),
                "errors": len(runtime["errors"]),
                "manifest": args.manifest_out,
            },
            indent=2,
        )
    )
    if runtime["errors"]:
        print(json.dumps(runtime["errors"], ensure_ascii=False, indent=2), file=sys.stderr)
    return 0 if runtime["results"] or not runtime["errors"] else 1
