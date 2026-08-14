#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r18-visible-light-signpost.md"
OUT = Path('/tmp/spiritual-bypassing-visible-boundary-r19-relocate-pushthrough-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-visible-dedup-owner-2026-08-14'

OLD_EARLY = "I put those links at the end.\n\nThere are plenty of “dark night” stories"
NEW_EARLY = "I put those links at the end. Critics describe a “push through” culture.\n\nThere are plenty of “dark night” stories"
OLD_LATE = "\n\nCritics describe a “push through” culture.\n\nFor me, this is where equanimity can turn into spiritual bypassing."
NEW_LATE = "\n\nFor me, this is where equanimity can turn into spiritual bypassing."


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

base = SOURCE.read_text(encoding='utf-8')
if base.count(OLD_EARLY) != 1 or base.count(OLD_LATE) != 1:
    raise SystemExit('expected exactly one relocation source and destination')
repaired = base.replace(OLD_EARLY, NEW_EARLY, 1).replace(OLD_LATE, NEW_LATE, 1)
visible = visible_text(repaired)
candidate = ROOT / 'state/candidates/spiritual-bypassing-r19-visible-relocate-pushthrough.md'
candidate.parent.mkdir(parents=True, exist_ok=True)
candidate.write_text(repaired, encoding='utf-8')
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-visible-boundary-r19-relocate-pushthrough-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'RELOCATE_PUSHTHROUGH','section_id':'FULL_ARTICLE','text':visible}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'out':str(OUT),'words':len(visible.split()),'sha256':hashlib.sha256(visible.encode()).hexdigest(),'candidate':str(candidate.relative_to(ROOT))}, indent=2))
