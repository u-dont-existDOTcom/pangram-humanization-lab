#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r24-primer-owner-mechanism.md"
OUT = Path('/tmp/spiritual-bypassing-full-r24-primer-dedup-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-primer-architecture-owner-2026-08-14'

OLD = """For me, this is where equanimity can turn into spiritual bypassing. The feeling comes up and, instead of healing what’s underneath it, you try to observe it away—to see it as insubstantial, not yours, and let it go. It can do the same thing with injustice: ignore it and call that inner peace. Remember some of the Buddhist responses to the Myanmar coup?"""
NEW = """For me, this is where equanimity can turn into spiritual bypassing. It can do the same thing with injustice: ignore it and call that inner peace. Remember some of the Buddhist responses to the Myanmar coup?"""


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

base = SOURCE.read_text(encoding='utf-8')
if base.count(OLD) != 1:
    raise SystemExit(f'expected one duplicate mechanism span, found {base.count(OLD)}')
repaired = base.replace(OLD, NEW, 1)
candidate = ROOT / 'state/candidates/spiritual-bypassing-r24-full-primer-dedup.md'
candidate.write_text(repaired, encoding='utf-8')
visible = visible_text(repaired)
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-full-r24-primer-dedup-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'FULL_R24_PRIMER_DEDUP','section_id':'FULL_ARTICLE','text':visible}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'out':str(OUT),'words':len(visible.split()),'sha256':hashlib.sha256(visible.encode()).hexdigest(),'candidate':str(candidate.relative_to(ROOT))}, indent=2))
