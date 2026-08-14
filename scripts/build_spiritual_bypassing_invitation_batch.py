#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r25-upstream-cleanup.md"
OUT = Path('/tmp/spiritual-bypassing-full-r26-dark-routing-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-primer-architecture-owner-2026-08-14'

OLD_EARLY = """I put those links at the end. Critics describe a “push through” culture.

There are plenty of “dark night” stories on [r/vipassana](http://Reddit.com/r/vipassana) too.

Some teachers compare intense practice without emotional groundwork to revving an engine without oil. That's the part I keep thinking about. If I start dissociating on day five, is that a warning or just another thing I'm supposed to observe?"""
NEW_EARLY = """I put those links at the end. Critics describe a “push through” culture. Some teachers compare intense practice without emotional groundwork to revving an engine without oil.

There are plenty of “dark night” stories on [r/vipassana](http://Reddit.com/r/vipassana) too.

If I start dissociating on day five, is that a warning or just another thing I'm supposed to observe?"""


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

base = SOURCE.read_text(encoding='utf-8')
if base.count(OLD_EARLY) != 1:
    raise SystemExit(f'expected one dark routing span, found {base.count(OLD_EARLY)}')
repaired = base.replace(OLD_EARLY, NEW_EARLY, 1)
candidate = ROOT / 'state/candidates/spiritual-bypassing-r26-dark-routing.md'
candidate.write_text(repaired, encoding='utf-8')
visible = visible_text(repaired)
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-full-r26-dark-routing-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'FULL_R26_DARK_ROUTING','section_id':'FULL_ARTICLE','text':visible}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'out':str(OUT),'words':len(visible.split()),'sha256':hashlib.sha256(visible.encode()).hexdigest(),'candidate':str(candidate.relative_to(ROOT))}, indent=2))
