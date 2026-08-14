#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r21-primer-simple.md"
OUT = Path('/tmp/spiritual-bypassing-full-r21-primer-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-primer-architecture-owner-2026-08-14'


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

candidate = SOURCE.read_text(encoding='utf-8')
visible = visible_text(candidate)
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-full-r21-primer-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'FULL_PRIMER_R21','section_id':'FULL_ARTICLE','text':visible}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({
    'out':str(OUT),
    'words':len(visible.split()),
    'sha256':hashlib.sha256(visible.encode()).hexdigest(),
    'candidate':str(SOURCE.relative_to(ROOT)),
}, indent=2))
