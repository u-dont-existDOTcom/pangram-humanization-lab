#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/experiments/spiritual-bypassing-invitation-batch-2026-08-13-results.json"
OUT = Path("/tmp/spiritual-bypassing-invitation-batch.json")
AUDIT_ID = "spiritual-bypassing-b-improve-2026-08-13"
EXPECTED_R2_C_FULL_SHA = "054ae3a2a3c20c2a06b805adf93840a58c7a8a17d7d6d175a733918d0a0a8b3a"

OLD = """If I start dissociating on day five, how am I supposed to know whether something difficult is coming up or the practice is making me worse? From inside the retreat, “keep observing” can sound exactly the same in both situations.

Critics describe a “push through” culture on [r/vipassana](http://Reddit.com/r/vipassana), and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up."""

CANDIDATES = {
    "E": """Day five is where I get stuck. Suppose I’m dissociating. Am I supposed to read that as a warning, or as another reaction to observe without reacting?

There are plenty of “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana). Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up.""",
    "F": """This is the part I don’t know how you’re supposed to judge from inside the retreat. If I’m dissociating on day five, is that the practice exposing something painful, or is the practice making me worse? “Observe and don’t react” doesn’t answer that.

There are plenty of “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana). Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up.""",
}


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    selected = next(row for row in source["results"] if row["id"] == "DARK_C_FULL")
    if selected["text_sha256"] != EXPECTED_R2_C_FULL_SHA:
        raise SystemExit(f"r2 C-full hash mismatch: {selected['text_sha256']}")
    base = selected["text"]
    if base.count(OLD) != 1:
        raise SystemExit(f"expected one remaining Dark Side target block, found {base.count(OLD)}")

    variants = []
    for name, replacement in CANDIDATES.items():
        full = base.replace(OLD, replacement, 1)
        parts = [part.strip() for part in full.split("\n---\n")]
        if len(parts) != 6:
            raise SystemExit(f"expected six article boundaries, got {len(parts)}")
        dark_side = parts[1]
        variants.append({"id": f"DARK_{name}_SECTION", "section_id": "dark-side-transition", "text": dark_side})
        variants.append({"id": f"DARK_{name}_FULL", "section_id": "FULL_ARTICLE", "text": full})

    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "spiritual-bypassing-b-repair-r3-2026-08-13",
        "audit_id": AUDIT_ID,
        "variants": variants,
    }
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
