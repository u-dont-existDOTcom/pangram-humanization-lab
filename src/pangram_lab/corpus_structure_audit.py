from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .corpus_acquire import (
    PostBodyParser,
    canonicalize,
    extract_blogspot,
    fetch_html,
    iter_inventory_items,
    normalize_visible_text,
    word_count,
)

_EXPLICIT_Q_RE = re.compile(r"(?im)^\s*(?:Q:|Question:)\s*")
_MESSAGE_OTHER_RE = re.compile(r"(?im)^\s*Message by (?!You:)\S.*?:\s*")
_GENERIC_LABEL_RE = re.compile(r"(?im)^\s*[A-Z][A-Za-z .'-]{1,50}:\s*")


def _post_body_text(html: str, *, drop_blockquotes: bool) -> str:
    parser = PostBodyParser(drop_blockquotes=drop_blockquotes)
    parser.feed(html)
    if not parser.found_body:
        raise ValueError("no recognized authored post-body container found")
    return normalize_visible_text(parser.text())


def _paragraph_count(text: str) -> int:
    return len([part for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]) if text.strip() else 0


def audit_blogspot_structure(html: str, *, mode: str) -> dict:
    full_body = _post_body_text(html, drop_blockquotes=False)
    unquoted_body = _post_body_text(html, drop_blockquotes=True)
    retained_visible = extract_blogspot(html, mode=mode)
    canonical = canonicalize(retained_visible)

    full_words = word_count(full_body)
    unquoted_words = word_count(unquoted_body)
    retained_words = canonical.word_count
    blockquote_words = max(0, full_words - unquoted_words)
    mode_removed_words = max(0, unquoted_words - retained_words)

    return {
        "post_body_word_count": full_words,
        "unquoted_body_word_count": unquoted_words,
        "blockquote_word_count_removed": blockquote_words,
        "blockquote_fraction": round(blockquote_words / full_words, 6) if full_words else 0.0,
        "retained_word_count": retained_words,
        "retained_fraction_of_unquoted_body": round(retained_words / unquoted_words, 6) if unquoted_words else 0.0,
        "mode_removed_word_count": mode_removed_words,
        "retained_paragraph_count": _paragraph_count(canonical.text),
        "explicit_q_marker_count": len(_EXPLICIT_Q_RE.findall(canonical.text)),
        "message_other_marker_count": len(_MESSAGE_OTHER_RE.findall(canonical.text)),
        "generic_label_line_count": len(_GENERIC_LABEL_RE.findall(canonical.text)),
        "quality_flags": canonical.quality_flags,
        "canonical_sha256": canonical.sha256,
    }


def audit_inventory(
    inventory_path: Path,
    *,
    sample_ids: set[str] | None = None,
    timeout: int = 30,
) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    results: list[dict] = []
    errors: list[dict] = []

    for item in iter_inventory_items(inventory):
        sample_id = item.get("sample_id")
        if not sample_id or (sample_ids and sample_id not in sample_ids):
            continue
        url = item.get("url")
        mode = item.get("extraction_mode", "manual-review")
        if not url or mode == "manual-review":
            errors.append({"sample_id": sample_id, "url": url, "error": "not-automatically-auditable"})
            continue
        try:
            html, source_html_sha256 = fetch_html(url, timeout=timeout)
            host = re.sub(r"^https?://", "", url).split("/", 1)[0].lower()
            if not host.endswith("blogspot.com"):
                raise ValueError(f"no structural auditor for host: {host}")
            structural = audit_blogspot_structure(html, mode=mode)
            results.append(
                {
                    "sample_id": sample_id,
                    "site_group": item.get("site_group"),
                    "source_group": item.get("source_group"),
                    "url": url,
                    "extraction_mode": mode,
                    "source_html_sha256": source_html_sha256,
                    **structural,
                }
            )
        except Exception as exc:
            errors.append({"sample_id": sample_id, "url": url, "error": str(exc)})

    return {
        "schema_version": 1,
        "inventory": str(inventory_path),
        "raw_or_canonical_prose_in_output": False,
        "results": results,
        "errors": errors,
    }


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.corpus_structure_audit")
    parser.add_argument(
        "inventory",
        nargs="?",
        default="state/IDIOLECT-LEGACY-TRIAGE-QUEUE-2026-08-18.json",
    )
    parser.add_argument("--out", default=".local/idiolect-corpus/structural-audit.json")
    parser.add_argument("--sample-id", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    result = audit_inventory(
        Path(args.inventory),
        sample_ids=set(args.sample_id) if args.sample_id else None,
        timeout=args.timeout,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "audited": len(result["results"]),
                "errors": len(result["errors"]),
                "out": str(out),
            },
            indent=2,
        )
    )
    if result["errors"]:
        print(json.dumps(result["errors"], ensure_ascii=False, indent=2), file=sys.stderr)
    return 0 if result["results"] or not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
