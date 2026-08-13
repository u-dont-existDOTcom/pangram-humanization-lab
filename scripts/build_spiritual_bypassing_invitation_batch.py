#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/experiments/spiritual-bypassing-invitation-batch-2026-08-13-results.json"
OUT = Path("/tmp/spiritual-bypassing-invitation-batch.json")
AUDIT_ID = "spiritual-bypassing-authorial-repair-2026-08-13"
EXPECTED_R5_SHA = "facb3c95e693957d028a11b8ec30cb8c1670396eae491d5916607a7e042e2c40"

OLD = """If I still wanted a retreat after that, I’d ask [Insight Meditation Society](http://dharma.org), [Plum Village](http://plumvillage.org), or whoever I was considering how they handle destabilization and whether pausing the practice is treated as an ordinary option.

That matters to me. A trauma-informed retreat shouldn’t turn continuing into a test of character. Your path is yours to shape."""

NEW = """If I still wanted a retreat after that, I’d ask [Insight Meditation Society](http://dharma.org), [Plum Village](http://plumvillage.org), or any other retreat I was considering one thing: what happens if I start destabilizing? Is pausing the practice treated as an ordinary option?

A trauma-informed retreat shouldn’t turn continuing into a test of character. Your path is yours to shape."""


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    selected = next(row for row in source["results"] if row["id"] == "OWNER_B_ALT_RESTORED_FULL")
    if selected["text_sha256"] != EXPECTED_R5_SHA:
        raise SystemExit(f"r5 hash mismatch: {selected['text_sha256']}")
    base = selected["text"]
    if base.count(OLD) != 1:
        raise SystemExit(f"expected one owner-B tail, found {base.count(OLD)}")
    full = base.replace(OLD, NEW, 1)
    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "spiritual-bypassing-authorial-repair-r6-2026-08-13",
        "audit_id": AUDIT_ID,
        "variants": [
            {"id": "OWNER_B_MINIMAL_COMPRESS_FULL", "section_id": "FULL_ARTICLE", "text": full}
        ],
    }
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
