from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


_NATIVE_IMAGE_RE = re.compile(r"\[NATIVE IMAGE —[^\]]*\]")
_NATIVE_YOUTUBE_RE = re.compile(r"\[NATIVE YOUTUBE —[^\]]*\]")
_NATIVE_PREVIEW_RE = re.compile(
    r"\[NATIVE SUBSTACK PREVIEW — (?P<label>.+?) — https?://[^\]]+\]"
)
_NATIVE_BUTTON_RE = re.compile(r"\[NATIVE BUTTON — (?P<label>.+?) — [^\]]+\]")
_SHARE_RE = re.compile(r"\[Share\]\([^\n)]*\)")
_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^\n)]*\)")
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^\n)]*\)")
_HEADING_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s+")
_HORIZONTAL_RULE_RE = re.compile(r"(?m)^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
_BLOCKQUOTE_RE = re.compile(r"(?m)^\s*>\s?")
_UNORDERED_LIST_RE = re.compile(r"(?m)^\s*[-+*]\s+")
_ORDERED_LIST_RE = re.compile(r"(?m)^\s*\d+[.)]\s+")
_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!])")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def reader_visible_text(markdown: str) -> str:
    text = markdown

    # Source-only native objects do not contribute visible article copy.
    text = _NATIVE_IMAGE_RE.sub(" ", text)
    text = _NATIVE_YOUTUBE_RE.sub(" ", text)

    # These native objects surface a visible title/label in the reader.
    text = _NATIVE_PREVIEW_RE.sub(lambda m: f" {m.group('label')} ", text)
    text = _NATIVE_BUTTON_RE.sub(lambda m: f" {m.group('label')} ", text)

    # Substack/source-helper UI, not article-body copy.
    text = _SHARE_RE.sub(" ", text)

    # Render Markdown links/formatting to the words a reader sees.
    text = _MARKDOWN_IMAGE_RE.sub(" ", text)
    text = _MARKDOWN_LINK_RE.sub(r"\1", text)
    text = _HEADING_RE.sub("", text)
    text = _HORIZONTAL_RULE_RE.sub(" ", text)
    text = _BLOCKQUOTE_RE.sub("", text)
    text = _UNORDERED_LIST_RE.sub("", text)
    text = _ORDERED_LIST_RE.sub("", text)

    # Strip emphasis/code delimiters without changing their contents.
    for pattern in (
        r"\*\*\*(.+?)\*\*\*",
        r"\*\*(.+?)\*\*",
        r"\*(.+?)\*",
        r"___(.+?)___",
        r"__(.+?)__",
        r"_(.+?)_",
        r"`([^`]+)`",
    ):
        text = re.sub(pattern, r"\1", text, flags=re.DOTALL)

    text = _ESCAPE_RE.sub(r"\1", text)

    # Match the prior Pangram reader-visible precedent: one plaintext string.
    return re.sub(r"\s+", " ", text).strip()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render Markdown as reader-visible Pangram plaintext.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        source = args.input.read_text(encoding="utf-8")
        visible = reader_visible_text(source)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(visible + "\n", encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "source_path": str(args.input),
            "source_sha256": sha256_text(source),
            "visible_sha256": sha256_text(visible),
            "source_bytes": len(source.encode("utf-8")),
            "visible_bytes": len(visible.encode("utf-8")),
            "visible_words": len(visible.split()),
            "normalization": "reader-visible-plaintext-v1",
            "native_policy": {
                "image": "omit source-only placeholder",
                "youtube": "omit source-only placeholder",
                "substack_preview": "retain visible title",
                "button": "retain visible label",
                "share_helper": "omit source-helper UI",
            },
        }
        args.manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 2

    print(f"visible_sha256={manifest['visible_sha256']}")
    print(f"visible_words={manifest['visible_words']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
