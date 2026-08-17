from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from scripts import render_reader_visible as rrv
except ModuleNotFoundError:  # direct execution: python scripts/render_pangram_halves.py
    import render_reader_visible as rrv


_EMPHASIS_PATTERNS = (
    r"\*\*\*(.+?)\*\*\*",
    r"\*\*(.+?)\*\*",
    r"\*(.+?)\*",
    r"___(.+?)___",
    r"__(.+?)__",
    r"_(.+?)_",
    r"`([^`]+)`",
)
_HEADING_LINE_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def reader_visible_with_breaks(markdown: str) -> str:
    """Render the same visible words as reader_visible_text while preserving layout."""
    text = markdown

    text = rrv._NATIVE_IMAGE_RE.sub(" ", text)
    text = rrv._NATIVE_YOUTUBE_RE.sub(" ", text)
    text = rrv._NATIVE_PREVIEW_RE.sub(lambda m: f" {m.group('label')} ", text)
    text = rrv._NATIVE_BUTTON_RE.sub(lambda m: f" {m.group('label')} ", text)
    text = rrv._SHARE_RE.sub(" ", text)

    text = rrv._MARKDOWN_IMAGE_RE.sub(" ", text)
    text = rrv._MARKDOWN_LINK_RE.sub(r"\1", text)
    text = rrv._HEADING_RE.sub("", text)
    text = rrv._HORIZONTAL_RULE_RE.sub(" ", text)
    text = rrv._BLOCKQUOTE_RE.sub("", text)
    text = rrv._UNORDERED_LIST_RE.sub("", text)
    text = rrv._ORDERED_LIST_RE.sub("", text)

    for pattern in _EMPHASIS_PATTERNS:
        text = re.sub(pattern, r"\1", text, flags=re.DOTALL)
    text = rrv._ESCAPE_RE.sub(r"\1", text)

    # Normalize horizontal whitespace but preserve paragraph/list line structure.
    out: list[str] = []
    pending_blank = False
    for raw in text.splitlines():
        line = re.sub(r"[ \t]+", " ", raw).strip()
        if line:
            if pending_blank and out:
                out.append("")
            out.append(line)
            pending_blank = False
        elif out:
            pending_blank = True

    visible = "\n".join(out).strip()
    collapsed = re.sub(r"\s+", " ", visible).strip()
    expected = rrv.reader_visible_text(markdown)
    if collapsed != expected:
        raise ValueError("line-preserved render does not normalize to reader-visible authority")
    return visible


def _article_headings(markdown: str) -> set[str]:
    headings: set[str] = set()
    for line in markdown.splitlines():
        match = _HEADING_LINE_RE.match(line)
        if match is None:
            continue
        rendered = reader_visible_with_breaks(match.group(1)).strip()
        if rendered:
            headings.add(rendered)
    return headings


def split_near_half_at_heading(visible: str, headings: set[str]) -> tuple[str, str, str | None]:
    blocks = visible.split("\n\n")
    if len(blocks) < 2:
        raise ValueError("not enough visible blocks to split")

    block_words = [len(block.split()) for block in blocks]
    total = sum(block_words)
    target = total / 2

    cumulative = 0
    candidates: list[tuple[float, int]] = []
    all_boundaries: list[tuple[float, int]] = []
    for i in range(1, len(blocks)):
        cumulative += block_words[i - 1]
        distance = abs(cumulative - target)
        all_boundaries.append((distance, i))
        if blocks[i] in headings:
            candidates.append((distance, i))

    _, split_at = min(candidates or all_boundaries)
    part1 = "\n\n".join(blocks[:split_at]).strip() + "\n"
    part2 = "\n\n".join(blocks[split_at:]).strip() + "\n"
    split_heading = blocks[split_at] if blocks[split_at] in headings else None
    return part1, part2, split_heading


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Romance into two line-preserved Pangram paste halves.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--part1", required=True, type=Path)
    parser.add_argument("--part2", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    markdown = args.input.read_text(encoding="utf-8")
    visible = reader_visible_with_breaks(markdown)
    part1, part2, split_heading = split_near_half_at_heading(visible, _article_headings(markdown))

    combined_collapsed = re.sub(r"\s+", " ", part1 + " " + part2).strip()
    canonical = rrv.reader_visible_text(markdown)
    if combined_collapsed != canonical:
        raise ValueError("split halves do not reconstruct the reader-visible authority")

    for path, text in ((args.part1, part1), (args.part2, part2)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    manifest = {
        "schema_version": 1,
        "source_path": str(args.input),
        "source_sha256": _sha256(markdown),
        "reader_visible_sha256": _sha256(canonical),
        "total_words": len(canonical.split()),
        "part1_words": len(part1.split()),
        "part2_words": len(part2.split()),
        "part1_sha256": _sha256(part1),
        "part2_sha256": _sha256(part2),
        "split_before_heading": split_heading,
        "format": "reader-visible words with paragraph/list line breaks preserved; no detector-only labels added",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
