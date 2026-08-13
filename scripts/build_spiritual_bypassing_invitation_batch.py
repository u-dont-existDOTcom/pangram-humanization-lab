#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/experiments/spiritual-bypassing-invitation-batch-2026-08-13-results.json"
OUT = Path("/tmp/spiritual-bypassing-invitation-batch.json")
AUDIT_ID = "spiritual-bypassing-authorial-repair-2026-08-13"
EXPECTED_R4_SHA = "4f1ab8eb9ff3786009a75a5a1c1835879ba7ed33ebc28ab4f61c2ab70d510148"

CURRENT_ALT = """The alternative I keep coming back to is metta first. Maybe trauma-informed mindfulness or Mindfulness-Based Stress Reduction with a therapist after that. If I still wanted a retreat, [Insight Meditation Society](http://dharma.org) and [Plum Village](http://plumvillage.org) are two places I’d look.

The question I’d care about before I went is what happens if I start destabilizing. Can I just stop? That should be an ordinary option, not a test of character. Your path is yours to shape."""

OWNER_SELECTED_ALT = """I’d start with metta. If that felt steady and I still wanted more, maybe trauma-informed mindfulness or Mindfulness-Based Stress Reduction with a therapist. If I still wanted a retreat after that, I’d ask [Insight Meditation Society](http://dharma.org), [Plum Village](http://plumvillage.org), or whoever I was considering how they handle destabilization and whether pausing the practice is treated as an ordinary option.

That matters to me. A trauma-informed retreat shouldn’t turn continuing into a test of character. Your path is yours to shape."""


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    selected = next(row for row in source["results"] if row["id"] == "AUTHORIAL_OBSERVE_AWAY_FULL")
    if selected["text_sha256"] != EXPECTED_R4_SHA:
        raise SystemExit(f"r4 hash mismatch: {selected['text_sha256']}")
    base = selected["text"]
    if base.count(CURRENT_ALT) != 1:
        raise SystemExit(f"expected one current Alternatives block, found {base.count(CURRENT_ALT)}")
    full = base.replace(CURRENT_ALT, OWNER_SELECTED_ALT, 1)
    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "spiritual-bypassing-authorial-repair-r5-2026-08-13",
        "audit_id": AUDIT_ID,
        "variants": [
            {"id": "OWNER_B_ALT_RESTORED_FULL", "section_id": "FULL_ARTICLE", "text": full}
        ],
    }
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
