#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r16-visible-dedup.md"
OUT = Path('/tmp/spiritual-bypassing-visible-boundary-r18-light-signpost-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-visible-dedup-owner-2026-08-14'

OLD = "Goenka is a good example because people with a recent history of mental instability are screened out, but the people who get in are still taught basically one response to whatever surfaces—observe it and don't react."
NEW = "Goenka is a good example of the kind of spiritual bypassing I'm talking about because people with a recent history of mental instability are screened out, but the people who get in are still taught basically one response to whatever surfaces—observe it and don't react."


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

base = SOURCE.read_text(encoding='utf-8')
if base.count(OLD) != 1:
    raise SystemExit(f'expected one opening signpost target, found {base.count(OLD)}')
repaired = base.replace(OLD, NEW, 1)
visible = visible_text(repaired)
candidate = ROOT / 'state/candidates/spiritual-bypassing-r18-visible-light-signpost.md'
candidate.parent.mkdir(parents=True, exist_ok=True)
candidate.write_text(repaired, encoding='utf-8')
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-visible-boundary-r18-light-signpost-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'LIGHT_SIGNPOST','section_id':'FULL_ARTICLE','text':visible}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'out':str(OUT),'words':len(visible.split()),'sha256':hashlib.sha256(visible.encode()).hexdigest(),'candidate':str(candidate.relative_to(ROOT))}, indent=2))
