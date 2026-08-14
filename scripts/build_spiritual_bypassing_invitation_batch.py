#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/experiments/spiritual-bypassing-invitation-batch-2026-08-13-results.json"
OUT = Path("/tmp/spiritual-bypassing-visible-boundary-r08-2026-08-14.json")
AUDIT_ID = "spiritual-bypassing-visible-boundary-2026-08-14"
EXPECTED_R6_SHA = "ec5a59dfd61d3cc3263ccff836a935d12104c85ab9d64f2707026a363ab2f4e9"

OLD_OPEN = """I have a problem with Goenka retreats: people with a recent history of mental instability are screened out, but the people who get in are still taught basically one response to whatever surfaces—observe it and don’t react.

Some people love Goenka retreats. I also know people who came out in pieces. Both are real. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.

My bias here is that healing starts with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com)."""

NEW_OPEN = """Some of you reading this probably love Goenka retreats. I’m not trying to tell you that your good experience didn’t happen. If it helped you, it helped you. I’m asking you to make room for the people who came out in pieces too.

My problem is bigger than Goenka. I worry about the point where a practice for observing pain turns into a way of avoiding what the pain is asking us to heal. That is what I mean by spiritual bypassing here.

Goenka is the clearest example for me because people with a recent history of mental instability are screened out, but the people who get in are still taught basically one response to whatever surfaces—observe it and don’t react. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.

My bias is that healing starts with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com)."""


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    selected = next(row for row in source["results"] if row["id"] == "OWNER_B_MINIMAL_COMPRESS_FULL")
    if selected["text_sha256"] != EXPECTED_R6_SHA:
        raise SystemExit(f"r6 hash mismatch: {selected['text_sha256']}")
    base = selected["text"]
    if base.count(OLD_OPEN) != 1:
        raise SystemExit(f"expected one opening span, found {base.count(OLD_OPEN)}")
    repaired = base.replace(OLD_OPEN, NEW_OPEN, 1)
    repaired_visible = visible_text(repaired)

    candidate = ROOT / "state/candidates/spiritual-bypassing-r08-minimal-invitational-opening.md"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(repaired, encoding="utf-8")

    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "spiritual-bypassing-visible-boundary-r08-2026-08-14",
        "audit_id": AUDIT_ID,
        "variants": [
            {"id": "MINIMAL_INVITATIONAL_OPENING", "section_id": "FULL_ARTICLE", "text": repaired_visible}
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
