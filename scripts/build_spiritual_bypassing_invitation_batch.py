#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r27-engine-risk-routing.md"
OUT = Path('/tmp/spiritual-bypassing-primer-r28-scope-complete-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-primer-architecture-owner-2026-08-14'

OLD = """Goenka retreats are a useful case study because people are taught basically one response to whatever surfaces: observe it and don't react."""
NEW = """Goenka retreats are the case study here. They teach basically one response to whatever surfaces: observe it and don't react. I want to look at whether that matches what the Buddha was actually teaching, and what happens when the thing surfacing is trauma."""

SECTION_END = "\n\n---\n\n# The Dark Side of Deep Dives: When Intensity Meets Unhealed Wounds"


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

base = SOURCE.read_text(encoding='utf-8')
if base.count(OLD) != 1 or base.count(SECTION_END) != 1:
    raise SystemExit(f'expected one scope span ({base.count(OLD)}) and one section boundary ({base.count(SECTION_END)})')
repaired = base.replace(OLD, NEW, 1)
intro, _ = repaired.split(SECTION_END, 1)
candidate = ROOT / 'state/candidates/spiritual-bypassing-r28-scope-complete.md'
candidate.write_text(repaired, encoding='utf-8')
visible_intro = visible_text(intro)
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-primer-r28-scope-complete-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'PRIMER_SCOPE_COMPLETE','section_id':'primer','text':visible_intro}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'out':str(OUT),'section_words':len(visible_intro.split()),'section_sha256':hashlib.sha256(visible_intro.encode()).hexdigest(),'candidate':str(candidate.relative_to(ROOT))}, indent=2))
