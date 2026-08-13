#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/experiments/spiritual-bypassing-invitation-batch-2026-08-13-results.json"
OUT = Path("/tmp/spiritual-bypassing-invitation-batch.json")
AUDIT_ID = "spiritual-bypassing-b-improve-2026-08-13"
EXPECTED_R1_B_FULL_SHA = "e05fcd090da184be2c1398eb84fb6dc2e9fb442536c97f9d71ec2dfb42e84042"

OLD = """That leaves the question the application can’t answer. If I start dissociating on day five, how am I supposed to tell the difference between “something difficult is coming up” and “this is actually making me worse”? I don’t want the fact that I’m reacting to become evidence that I need to practice non-reaction harder.

There are plenty of “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana). Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up.

That is where spiritual bypassing enters the picture for me. Equanimity can become a way to avoid emotional mess instead of healing it. It can also become a way to ignore injustice while calling that inner peace. Remember some of the Buddhist responses to the Myanmar coup?"""

CANDIDATES = {
    "C": """If I start dissociating on day five, how am I supposed to know whether something difficult is coming up or the practice is making me worse? From inside the retreat, “keep observing” can sound exactly the same in both situations.

Critics describe a “push through” culture on [r/vipassana](http://Reddit.com/r/vipassana), and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up.

That is where equanimity can turn into spiritual bypassing for me: instead of healing the emotional mess, it becomes a way to stand above it. It can do the same thing with injustice: ignore it and call that inner peace. Remember some of the Buddhist responses to the Myanmar coup?""",
    "D": """If I start dissociating on day five, what exactly am I supposed to do with that information? If the answer is still “observe and don’t react,” then the same instruction is being used for pain that may be moving through and for a practice that may be making me worse.

There are plenty of “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana). Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up.

That overlap is what I mean by spiritual bypassing here. Equanimity becomes a way to get around the emotional mess rather than heal it. It can also become a way to ignore injustice while calling that inner peace. Remember some of the Buddhist responses to the Myanmar coup?""",
}


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    selected = next(row for row in source["results"] if row["id"] == "ALT_B_FULL")
    if selected["text_sha256"] != EXPECTED_R1_B_FULL_SHA:
        raise SystemExit(f"r1 B-full hash mismatch: {selected['text_sha256']}")
    base = selected["text"]
    if base.count(OLD) != 1:
        raise SystemExit(f"expected one Dark Side target block, found {base.count(OLD)}")

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
        "experiment_id": "spiritual-bypassing-b-repair-r2-2026-08-13",
        "audit_id": AUDIT_ID,
        "variants": variants,
    }
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
