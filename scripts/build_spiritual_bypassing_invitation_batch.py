#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r27-engine-risk-routing.md"
OUT = Path('/tmp/spiritual-bypassing-dark-r29-fidelity-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-primer-architecture-owner-2026-08-14'

OLD = "Some teachers compare intense practice without emotional groundwork to revving an engine without oil."
NEW = OLD + " Things can seize up."
START = "# The Dark Side of Deep Dives: When Intensity Meets Unhealed Wounds"
END = "\n\n---\n\n# Loving Kindness: The Cozy Blanket Before the Storm"


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()

base = SOURCE.read_text(encoding='utf-8')
if base.count(OLD) != 1 or base.count(START) != 1 or base.count(END) != 1:
    raise SystemExit('expected unique fidelity target and section boundaries')
repaired = base.replace(OLD, NEW, 1)
candidate = ROOT / 'state/candidates/spiritual-bypassing-r29-fidelity-restored.md'
candidate.write_text(repaired, encoding='utf-8')
_, after_start = repaired.split(START, 1)
dark_body, _ = after_start.split(END, 1)
dark = START + dark_body
visible_dark = visible_text(dark)
spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-dark-r29-fidelity-2026-08-14',
    'audit_id':AUDIT_ID,
    'variants':[{'id':'DARK_FIDELITY_RESTORE','section_id':'dark-side','text':visible_dark}],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'out':str(OUT),'section_words':len(visible_dark.split()),'section_sha256':hashlib.sha256(visible_dark.encode()).hexdigest(),'candidate':str(candidate.relative_to(ROOT))}, indent=2))
