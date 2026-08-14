#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r24-full-primer-dedup.md"
OUT = Path('/tmp/spiritual-bypassing-full-r25-upstream-cleanup-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-primer-architecture-owner-2026-08-14'

OLD_DARK = """Some teachers compare intense practice without emotional groundwork to revving an engine without oil.

Day five is where I get stuck. If I started dissociating then, I wouldn’t know what the instruction wants me to do with that. Is it a warning, or am I supposed to sit there and observe the warning too?"""
NEW_DARK = """Some teachers compare intense practice without emotional groundwork to revving an engine without oil. That's the part I keep thinking about. If I start dissociating on day five, is that a warning or just another thing I'm supposed to observe?"""

OLD_METTA = """I know “cozy blanket” sounds almost comically soft next to ten days of vipassana. That is partly the point.

My own experience was weird."""
NEW_METTA = """My own experience was weird."""


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

base = SOURCE.read_text(encoding='utf-8')
if base.count(OLD_DARK) != 1 or base.count(OLD_METTA) != 1:
    raise SystemExit('expected one dark-side span and one metta heading-restatement span')
repaired = base.replace(OLD_DARK, NEW_DARK, 1).replace(OLD_METTA, NEW_METTA, 1)
candidate = ROOT / 'state/candidates/spiritual-bypassing-r25-upstream-cleanup.md'
candidate.write_text(repaired, encoding='utf-8')
visible = visible_text(repaired)
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-full-r25-upstream-cleanup-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'FULL_R25_UPSTREAM_CLEANUP','section_id':'FULL_ARTICLE','text':visible}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'out':str(OUT),'words':len(visible.split()),'sha256':hashlib.sha256(visible.encode()).hexdigest(),'candidate':str(candidate.relative_to(ROOT))}, indent=2))
