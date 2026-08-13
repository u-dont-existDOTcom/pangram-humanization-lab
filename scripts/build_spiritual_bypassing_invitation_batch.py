#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/experiments/spiritual-bypassing-r13-interaction-2026-08-13-results.json"
OUT = Path("/tmp/spiritual-bypassing-invitation-batch.json")
EXPECTED_B_SHA = "192f8d3d34f05a39208451b5ce740c569a546a3a66467818261c63561eab12a9"
AUDIT_ID = "spiritual-bypassing-b-improve-2026-08-13"

OLD = """I’d start with metta. If that felt steady and I still wanted more, maybe trauma-informed mindfulness or Mindfulness-Based Stress Reduction with a therapist. If I still wanted a retreat after that, I’d ask [Insight Meditation Society](http://dharma.org), [Plum Village](http://plumvillage.org), or whoever I was considering how they handle destabilization and whether pausing the practice is treated as an ordinary option.

That matters to me. A trauma-informed retreat shouldn’t turn continuing into a test of character. Your path is yours to shape."""

CANDIDATES = {
    "A": """I’d start with metta. Trauma-informed mindfulness—maybe Mindfulness-Based Stress Reduction with a therapist—is another option before ten silent days. [Insight Meditation Society](http://dharma.org) and [Plum Village](http://plumvillage.org) are two places I’d look if I still wanted a retreat.

What I’d ask before going is simple: what happens if the practice starts destabilizing me? I want stopping to be an ordinary option, not a test of character. Your path is yours to shape.""",
    "B": """The alternative I keep coming back to is metta first. Maybe trauma-informed mindfulness or Mindfulness-Based Stress Reduction with a therapist after that. If I still wanted a retreat, [Insight Meditation Society](http://dharma.org) and [Plum Village](http://plumvillage.org) are two places I’d look.

The question I’d care about before I went is what happens if I start destabilizing. Can I just stop? That should be an ordinary option, not a test of character. Your path is yours to shape.""",
}


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    selected = next(row for row in source["results"] if row["id"] == "ALT_INVITATIONAL")
    if selected["text_sha256"] != EXPECTED_B_SHA:
        raise SystemExit(f"owner-selected B hash mismatch: {selected['text_sha256']}")
    base = selected["text"]
    if base.count(OLD) != 1:
        raise SystemExit(f"expected one owner-selected Alternatives block, found {base.count(OLD)}")

    variants = []
    for name, replacement in CANDIDATES.items():
        full = base.replace(OLD, replacement, 1)
        parts = [part.strip() for part in full.split("\n---\n")]
        if len(parts) != 6:
            raise SystemExit(f"expected six article boundaries, got {len(parts)}")
        alternatives = parts[4]
        variants.append({"id": f"ALT_{name}_SECTION", "section_id": "alternatives", "text": alternatives})
        variants.append({"id": f"ALT_{name}_FULL", "section_id": "FULL_ARTICLE", "text": full})

    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "spiritual-bypassing-b-repair-r1-2026-08-13",
        "audit_id": AUDIT_ID,
        "variants": variants,
    }
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
