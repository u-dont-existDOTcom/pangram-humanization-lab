#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r12-visible-repair.md"
OUT = Path('/tmp/spiritual-bypassing-visible-boundary-r15-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-visible-owner-repair-2026-08-14'

OLD = """Day five is where I get stuck. If I started dissociating then, I wouldn’t know what the instruction wants me to do with that. Is it a warning, or am I supposed to sit there and observe the warning too?

There are plenty of “dark night” stories on [r/vipassana](http://Reddit.com/r/vipassana). Critics talk about a “push through” culture. Some teachers compare intense practice without emotional groundwork to revving an engine without oil.

The feeling comes up and, instead of healing what’s underneath it, you try to observe it away—to see it as insubstantial, not yours, and let it go. It can do the same thing with injustice: ignore it and call that inner peace. Remember some of the Buddhist responses to the Myanmar coup?"""

NEW = """There are plenty of “dark night” stories on [r/vipassana](http://Reddit.com/r/vipassana) too. Some teachers compare intense practice without emotional groundwork to revving an engine without oil.

Day five is where I get stuck. If I started dissociating then, I wouldn’t know what the instruction wants me to do with that. Is it a warning, or am I supposed to sit there and observe the warning too?

Critics describe a “push through” culture.

The feeling comes up and, instead of healing what’s underneath it, you try to observe it away—to see it as insubstantial, not yours, and let it go. It can do the same thing with injustice: ignore it and call that inner peace. Remember some of the Buddhist responses to the Myanmar coup?"""


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

base = SOURCE.read_text(encoding='utf-8')
if base.count(OLD) != 1:
    raise SystemExit(f'expected one evidence bundle, found {base.count(OLD)}')
repaired = base.replace(OLD, NEW, 1)
visible = visible_text(repaired)
candidate = ROOT / 'state/candidates/spiritual-bypassing-r15-visible-final.md'
candidate.parent.mkdir(parents=True, exist_ok=True)
candidate.write_text(repaired, encoding='utf-8')
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-visible-boundary-r15-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'DISTRIBUTE_EVIDENCE','section_id':'FULL_ARTICLE','text':visible}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'out':str(OUT),'words':len(visible.split()),'sha256':hashlib.sha256(visible.encode()).hexdigest(),'candidate':str(candidate.relative_to(ROOT))}, indent=2))
