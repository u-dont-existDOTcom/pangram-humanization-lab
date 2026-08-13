#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/experiments/spiritual-bypassing-invitation-batch-2026-08-13-results.json"
OUT = Path("/tmp/spiritual-bypassing-invitation-batch.json")
AUDIT_ID = "spiritual-bypassing-authorial-repair-2026-08-13"
EXPECTED_E_FULL_SHA = "cbe9de3e8621ae2998cdf6893af55bd3a0263bf1adcde23ae95f58f82f7fac3b"

OLD = """Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up.

That is where equanimity can turn into spiritual bypassing for me: instead of healing the emotional mess, it becomes a way to stand above it."""

NEW = """Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up.

For me, this is where equanimity can turn into spiritual bypassing. The feeling comes up and, instead of healing what’s underneath it, you try to observe it away—to see it as insubstantial, not yours, and let it go."""


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    selected = next(row for row in source["results"] if row["id"] == "DARK_E_FULL")
    if selected["text_sha256"] != EXPECTED_E_FULL_SHA:
        raise SystemExit(f"E-full hash mismatch: {selected['text_sha256']}")
    base = selected["text"]
    if base.count(OLD) != 1:
        raise SystemExit(f"expected one authorial repair target, found {base.count(OLD)}")
    full = base.replace(OLD, NEW, 1)
    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "spiritual-bypassing-authorial-repair-r4-2026-08-13",
        "audit_id": AUDIT_ID,
        "variants": [
            {"id": "AUTHORIAL_OBSERVE_AWAY_FULL", "section_id": "FULL_ARTICLE", "text": full}
        ],
    }
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
