#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r10-visible-repair.md"
OUT = Path("/tmp/spiritual-bypassing-visible-boundary-r11-2026-08-14.json")
AUDIT_ID = "spiritual-bypassing-visible-owner-repair-2026-08-14"

OLD = """Day five is where I get stuck. If I’m dissociating, is that a sign to stop or just another reaction I’m supposed to observe? I don’t see how the instruction itself tells me.

There are plenty of “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana), and critics describe a “push through” culture. Some teachers compare intense practice without emotional groundwork to revving an engine without oil.

For me, this is where equanimity can turn into spiritual bypassing. The feeling comes up and, instead of healing what’s underneath it, you try to observe it away—to see it as insubstantial, not yours, and let it go."""

NEW = """Day five is where I get stuck. If I’m dissociating, how do I know whether that’s a warning or something to keep observing? “Observe it and don’t react” doesn’t answer that for me.

[r/vipassana](http://Reddit.com/r/vipassana) has plenty of “dark night” accounts, and critics describe a “push through” culture. Some teachers compare intense practice without emotional groundwork to revving an engine without oil.

The feeling comes up and, instead of healing what’s underneath it, you try to observe it away—to see it as insubstantial, not yours, and let it go."""


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    base = SOURCE.read_text(encoding="utf-8")
    if base.count(OLD) != 1:
        raise SystemExit(f"expected one remaining red span, found {base.count(OLD)}")
    repaired = base.replace(OLD, NEW, 1)
    repaired_visible = visible_text(repaired)
    candidate = ROOT / "state/candidates/spiritual-bypassing-r11-visible-repair.md"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(repaired, encoding="utf-8")
    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "spiritual-bypassing-visible-boundary-r11-2026-08-14",
        "audit_id": AUDIT_ID,
        "variants": [
            {"id": "REMOVE_ABSTRACT_BRIDGE", "section_id": "FULL_ARTICLE", "text": repaired_visible}
        ],
    }
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "repaired_words": len(repaired_visible.split()),
        "repaired_sha256": hashlib.sha256(repaired_visible.encode()).hexdigest(),
        "candidate": str(candidate.relative_to(ROOT)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
