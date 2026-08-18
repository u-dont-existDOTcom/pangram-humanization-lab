from __future__ import annotations

import collections
import html as html_lib
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from .blogger_discover import ATOM, _feed_url, _https_url, _root_from_url, fetch_atom

_NAME_TOKEN = r"[A-Z][A-Za-zÀ-ÖØ-öø-ÿ.'’\-]*"
_PERSON_LABEL_RE = re.compile(rf"^({_NAME_TOKEN}(?:\s+{_NAME_TOKEN}){{1,4}})\s*:?$")


class BoldSpeakerLabelScanner(HTMLParser):
    """Collect explicit person-like labels rendered in bold/strong/cite tags.

    Only the label strings are retained. No surrounding post/comment prose is
    stored or returned.
    """

    _LABEL_TAGS = {"b", "strong", "cite"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts: list[str] = []
        self.labels: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() in self._LABEL_TAGS:
            if self.depth == 0:
                self.parts = []
            self.depth += 1

    def handle_endtag(self, tag: str):
        if tag.lower() not in self._LABEL_TAGS or self.depth <= 0:
            return
        self.depth -= 1
        if self.depth == 0:
            value = html_lib.unescape("".join(self.parts))
            value = re.sub(r"\s+", " ", value).strip()
            m = _PERSON_LABEL_RE.match(value)
            if m:
                self.labels.append(m.group(1).strip())
            self.parts = []

    def handle_data(self, data: str):
        if self.depth:
            self.parts.append(data)


def _canonical_post_url(entry: ET.Element) -> str | None:
    for link in entry.findall(f"{ATOM}link"):
        if link.attrib.get("rel") == "alternate" and link.attrib.get("href"):
            url = _https_url(link.attrib["href"])
            parsed = urlparse(url)
            return parsed._replace(query="", fragment="").geturl()
    return None


def _entry_html(entry: ET.Element) -> str:
    for tag in (f"{ATOM}content", f"{ATOM}summary"):
        node = entry.find(tag)
        if node is not None and node.text:
            return node.text
    return ""


def _speaker_labels(content_html: str) -> list[str]:
    scanner = BoldSpeakerLabelScanner()
    scanner.feed(content_html)
    return scanner.labels


def scan_atom_page(body: bytes, *, target_speaker: str) -> tuple[list[dict], str | None]:
    root = ET.fromstring(body)
    next_url = None
    for link in root.findall(f"{ATOM}link"):
        if link.attrib.get("rel") == "next" and link.attrib.get("href"):
            next_url = _https_url(link.attrib["href"])
            break

    rows: list[dict] = []
    target_key = target_speaker.casefold()
    for entry in root.findall(f"{ATOM}entry"):
        url = _canonical_post_url(entry)
        if not url:
            continue
        content_html = _entry_html(entry)
        labels = _speaker_labels(content_html)
        target_label_count = sum(1 for label in labels if label.casefold() == target_key)
        raw_target_occurrences = content_html.casefold().count(target_key)
        if not raw_target_occurrences and not target_label_count:
            continue
        rows.append(
            {
                "entry_id": (entry.findtext(f"{ATOM}id") or "").strip(),
                "title": (entry.findtext(f"{ATOM}title") or "").strip(),
                "published": (entry.findtext(f"{ATOM}published") or "").strip(),
                "url": url,
                "raw_target_occurrences": raw_target_occurrences,
                "target_label_count": target_label_count,
                "explicit_speaker_labels": labels,
            }
        )
    return rows, next_url


def discover_dharma_authors(
    blog_url: str,
    *,
    target_speaker: str = "Joel Rosenblum",
    timeout: int = 30,
    page_size: int = 100,
    max_pages: int = 50,
) -> dict:
    root = _root_from_url(blog_url)
    url = _feed_url(root, start_index=1, max_results=page_size)
    pages: list[dict] = []
    target_posts: dict[str, dict] = {}
    seen_urls: set[str] = set()

    for page_number in range(1, max_pages + 1):
        if url in seen_urls:
            raise RuntimeError(f"Blogger feed pagination loop detected: {url}")
        seen_urls.add(url)
        body, body_sha = fetch_atom(url, timeout=timeout)
        rows, next_url = scan_atom_page(body, target_speaker=target_speaker)
        pages.append(
            {
                "page_number": page_number,
                "feed_sha256": body_sha,
                "target_post_count": len(rows),
                "next_present": bool(next_url),
            }
        )
        for row in rows:
            target_posts[row["url"]] = row
        if not next_url:
            break
        url = next_url
    else:
        raise RuntimeError(f"Blogger feed paging exceeded max_pages={max_pages}: {root}")

    thread_counts: collections.Counter[str] = collections.Counter()
    marker_counts: collections.Counter[str] = collections.Counter()
    target_key = target_speaker.casefold()
    for row in target_posts.values():
        unique = {label for label in row["explicit_speaker_labels"] if label.casefold() != target_key}
        thread_counts.update(unique)
        marker_counts.update(label for label in row["explicit_speaker_labels"] if label.casefold() != target_key)

    candidates = [
        {
            "speaker": speaker,
            "thread_count": thread_counts[speaker],
            "marker_count": marker_counts[speaker],
        }
        for speaker in sorted(thread_counts, key=lambda value: (-thread_counts[value], value.casefold()))
    ]

    posts = sorted(target_posts.values(), key=lambda row: (row.get("published") or "", row["url"]))
    return {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "blog_root": root,
        "target_speaker": target_speaker,
        "feed_pages": pages,
        "target_post_count": len(posts),
        "target_posts": posts,
        "control_speaker_candidates": candidates,
    }


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.dharma_author_discover")
    parser.add_argument("--blog", default="https://dharmaconnectiongroup.blogspot.com/")
    parser.add_argument("--target-speaker", default="Joel Rosenblum")
    parser.add_argument("--out", default=".local/idiolect-corpus/dharma-author-census.json")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    try:
        result = discover_dharma_authors(
            args.blog,
            target_speaker=args.target_speaker,
            timeout=args.timeout,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
