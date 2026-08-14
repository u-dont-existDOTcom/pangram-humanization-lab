#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r19-visible-relocate-pushthrough.md"
OUT = Path('/tmp/spiritual-bypassing-primer-r20-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-primer-architecture-owner-2026-08-14'

SECTION_END = "\n\n---\n\n# The Dark Side of Deep Dives: When Intensity Meets Unhealed Wounds"

NEW_INTRO = """# A Primer on Spiritual Bypassing

Spiritual bypassing is when a spiritual idea or practice gets used to get around something that still needs healing. That's what I want to look at here, using Goenka retreats as a case study. They teach you to observe whatever comes up without reacting to it. But what happens when what comes up is trauma?

I'm really happy if you benefitted from your Goenka experience. It's also true that it has harmed many people, and the method itself is not built well for trauma survivors. That's why I wouldn't recommend it in general, although I can never tell anyone what would work specifically for them.

My bias here is that healing starts with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com).

I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like."""


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

base = SOURCE.read_text(encoding='utf-8')
if base.count(SECTION_END) != 1:
    raise SystemExit(f'expected one first-section boundary, found {base.count(SECTION_END)}')
_, rest = base.split(SECTION_END, 1)
repaired = NEW_INTRO + SECTION_END + rest
candidate = ROOT / 'state/candidates/spiritual-bypassing-r20-primer-architecture.md'
candidate.parent.mkdir(parents=True, exist_ok=True)
candidate.write_text(repaired, encoding='utf-8')

visible_intro = visible_text(NEW_INTRO)
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-primer-r20-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'PRIMER_ARCHITECTURE','section_id':'primer','text':visible_intro}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({
    'out':str(OUT),
    'section_words':len(visible_intro.split()),
    'section_sha256':hashlib.sha256(visible_intro.encode()).hexdigest(),
    'candidate':str(candidate.relative_to(ROOT)),
}, indent=2))
