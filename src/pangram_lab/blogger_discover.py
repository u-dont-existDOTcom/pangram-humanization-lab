from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

ATOM = "{http://www.w3.org/2005/Atom}"


@dataclass(frozen=True)
class BloggerPost:
    entry_id: str
    title: str
    published: str
    updated: str | None
    url: str
    labels: tuple[str, ...]


def _root_from_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else "https://" + url)
    if not parsed.netloc:
        raise ValueError(f"invalid Blogger URL: {url}")
    return urlunparse(("https", parsed.netloc.lower(), "", "", "", ""))


def _https_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse(("https", parsed.netloc.lower(), parsed.path, parsed.params, parsed.query, parsed.fragment))


def _iso(value: str) -> datetime:
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _canonical_post_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse(("https", parsed.netloc.lower(), parsed.path, "", "", ""))


def _feed_url(root: str, *, start_index: int, max_results: int) -> str:
    # Blogger documents max-results and 1-based start-index for feed paging.
    # The service can cap a page below the requested max-results, so callers
    # must follow the feed's rel=next link rather than infer EOF from length.
    query = urlencode(
        {
            "alt": "atom",
            "start-index": start_index,
            "max-results": max_results,
        }
    )
    return f"{root.rstrip('/')}/feeds/posts/default?{query}"


def fetch_atom(url: str, *, timeout: int = 30) -> tuple[bytes, str]:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; pangram-humanization-lab Blogger metadata discovery)"
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        body = resp.read()
    return body, hashlib.sha256(body).hexdigest()


def parse_atom_page(body: bytes) -> tuple[list[BloggerPost], str | None]:
    root = ET.fromstring(body)
    posts: list[BloggerPost] = []
    next_url = None

    for link in root.findall(f"{ATOM}link"):
        if link.attrib.get("rel") == "next" and link.attrib.get("href"):
            next_url = _https_url(link.attrib["href"])
            break

    for entry in root.findall(f"{ATOM}entry"):
        entry_id = (entry.findtext(f"{ATOM}id") or "").strip()
        title = (entry.findtext(f"{ATOM}title") or "").strip()
        published = (entry.findtext(f"{ATOM}published") or "").strip()
        updated = (entry.findtext(f"{ATOM}updated") or "").strip() or None
        alt = None
        for link in entry.findall(f"{ATOM}link"):
            if link.attrib.get("rel") == "alternate" and link.attrib.get("href"):
                alt = link.attrib["href"]
                break
        labels = tuple(
            sorted(
                {
                    node.attrib.get("term", "").strip()
                    for node in entry.findall(f"{ATOM}category")
                    if node.attrib.get("term", "").strip()
                }
            )
        )
        if not entry_id or not title or not published or not alt:
            continue
        posts.append(
            BloggerPost(
                entry_id=entry_id,
                title=title,
                published=published,
                updated=updated,
                url=_canonical_post_url(alt),
                labels=labels,
            )
        )
    return posts, next_url


def parse_atom_posts(body: bytes) -> list[BloggerPost]:
    return parse_atom_page(body)[0]


def discover_blog(
    blog_url: str,
    *,
    published_before: str | None = None,
    timeout: int = 30,
    page_size: int = 100,
    max_pages: int = 50,
) -> dict:
    root = _root_from_url(blog_url)
    cutoff = _iso(published_before) if published_before else None
    url = _feed_url(root, start_index=1, max_results=page_size)
    pages: list[dict] = []
    posts: dict[str, BloggerPost] = {}
    seen_urls: set[str] = set()

    for page_number in range(1, max_pages + 1):
        if url in seen_urls:
            raise RuntimeError(f"Blogger feed pagination loop detected: {url}")
        seen_urls.add(url)
        body, body_sha = fetch_atom(url, timeout=timeout)
        batch, next_url = parse_atom_page(body)
        pages.append(
            {
                "page_number": page_number,
                "feed_url": url,
                "feed_sha256": body_sha,
                "entry_count": len(batch),
                "next_url": next_url,
            }
        )
        for post in batch:
            if cutoff and _iso(post.published) >= cutoff:
                continue
            posts[post.entry_id] = post
        if not next_url:
            break
        url = next_url
    else:
        raise RuntimeError(f"Blogger feed paging exceeded max_pages={max_pages}: {root}")

    ordered = sorted(posts.values(), key=lambda p: (_iso(p.published), p.entry_id))
    return {
        "blog_root": root,
        "published_before": published_before,
        "pages": pages,
        "post_count": len(ordered),
        "posts": [
            {
                "entry_id": post.entry_id,
                "title": post.title,
                "published": post.published,
                "updated": post.updated,
                "url": post.url,
                "labels": list(post.labels),
            }
            for post in ordered
        ],
    }


def discover_queue(queue_path: Path, *, timeout: int = 30) -> dict:
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    results: list[dict] = []
    errors: list[dict] = []
    for source in queue.get("blogs", []):
        source_id = source.get("source_id")
        blog_url = source.get("blog_url")
        if not source_id or not blog_url:
            errors.append({"source_id": source_id, "error": "missing-source-id-or-blog-url"})
            continue
        try:
            result = discover_blog(
                blog_url,
                published_before=source.get("published_before"),
                timeout=timeout,
            )
            result.update(
                {
                    "source_id": source_id,
                    "provenance": source.get("provenance"),
                    "owner_confirmation": source.get("owner_confirmation"),
                    "notes": source.get("notes"),
                }
            )
            results.append(result)
        except Exception as exc:
            errors.append(
                {
                    "source_id": source_id,
                    "blog_url": blog_url,
                    "error": str(exc),
                }
            )
    return {
        "schema_version": 1,
        "queue": str(queue_path),
        "content_included": False,
        "results": results,
        "errors": errors,
    }


def add_cli_parsers(subparsers) -> None:
    p = subparsers.add_parser(
        "idiolect-blogger-discover",
        help="Enumerate metadata for confirmed-owner Blogger posts without storing post content.",
    )
    p.add_argument(
        "queue",
        nargs="?",
        default="state/IDIOLECT-BLOGGER-DISCOVERY-QUEUE-2026-08-18.json",
    )
    p.add_argument("--out", default=".local/idiolect-corpus/blogger-discovery.json")
    p.add_argument("--timeout", type=int, default=30)


def run_cli(args) -> int:
    result = discover_queue(Path(args.queue), timeout=args.timeout)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "blogs_discovered": len(result["results"]),
        "posts_discovered": sum(row["post_count"] for row in result["results"]),
        "errors": len(result["errors"]),
        "out": str(out),
    }
    print(json.dumps(summary, indent=2))
    if result["errors"]:
        print(json.dumps(result["errors"], ensure_ascii=False, indent=2), file=sys.stderr)
    return 0 if result["results"] or not result["errors"] else 1
