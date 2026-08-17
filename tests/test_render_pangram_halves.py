from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.render_pangram_halves import reader_visible_with_breaks, split_near_half, _article_headings
from scripts.render_reader_visible import reader_visible_text


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work" / "romance-current-assembly"


def test_line_preserved_render_normalizes_to_reader_visible_authority() -> None:
    source = (WORK / "current-master.md").read_text(encoding="utf-8")
    preserved = reader_visible_with_breaks(source)
    assert "\n\n" in preserved
    assert re.sub(r"\s+", " ", preserved).strip() == reader_visible_text(source)


def test_split_is_balanced_at_paragraph_boundary_and_reconstructs_exact_visible_words() -> None:
    source = (WORK / "current-master.md").read_text(encoding="utf-8")
    visible = reader_visible_with_breaks(source)
    part1, part2, _ = split_near_half(visible, _article_headings(source))

    combined = re.sub(r"\s+", " ", part1 + " " + part2).strip()
    assert combined == reader_visible_text(source)
    total = len(combined.split())
    assert abs(len(part1.split()) - len(part2.split())) < total * 0.02
    assert part1.endswith("\n") and part2.endswith("\n")
    assert "\n\n" in part1 and "\n\n" in part2


def test_generated_manifest_matches_current_reader_visible_hash_when_present() -> None:
    manifest_path = WORK / "pangram-halves-manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    reader_manifest = json.loads((WORK / "reader-visible-manifest.json").read_text(encoding="utf-8"))
    assert manifest["reader_visible_sha256"] == reader_manifest["visible_sha256"]
    assert manifest["total_words"] == reader_manifest["visible_words"]
