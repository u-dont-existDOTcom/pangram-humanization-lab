#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r25-upstream-cleanup.md"
OUT = Path('/tmp/spiritual-bypassing-full-r27-engine-risk-routing-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-primer-architecture-owner-2026-08-14'

OLD_RISK = """Anyone with a recent history of mental instability is not allowed into a Goenka retreat, nor most Theravada Buddhist retreats, because the risk of destabilization is already known to be high ([three times greater long-term dysfunction likelihood compared with an ayahuasca retreat](https://g.co/gemini/share/3ea68c3b75a0))."""
NEW_RISK = OLD_RISK + " Some teachers compare intense practice without emotional groundwork to revving an engine without oil."

OLD_LATER = """There are plenty of “dark night” stories on [r/vipassana](http://Reddit.com/r/vipassana) too. Some teachers compare intense practice without emotional groundwork to revving an engine without oil. That's the part I keep thinking about. If I start dissociating on day five, is that a warning or just another thing I'm supposed to observe?"""
NEW_LATER = """There are plenty of “dark night” stories on [r/vipassana](http://Reddit.com/r/vipassana) too.

If I start dissociating on day five, is that a warning or just another thing I'm supposed to observe?"""


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

base = SOURCE.read_text(encoding='utf-8')
if base.count(OLD_RISK) != 1 or base.count(OLD_LATER) != 1:
    raise SystemExit(f'expected one risk span ({base.count(OLD_RISK)}) and one later span ({base.count(OLD_LATER)})')
repaired = base.replace(OLD_RISK, NEW_RISK, 1).replace(OLD_LATER, NEW_LATER, 1)
candidate = ROOT / 'state/candidates/spiritual-bypassing-r27-engine-risk-routing.md'
candidate.write_text(repaired, encoding='utf-8')
visible = visible_text(repaired)
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-full-r27-engine-risk-routing-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'FULL_R27_ENGINE_RISK','section_id':'FULL_ARTICLE','text':visible}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'out':str(OUT),'words':len(visible.split()),'sha256':hashlib.sha256(visible.encode()).hexdigest(),'candidate':str(candidate.relative_to(ROOT))}, indent=2))
