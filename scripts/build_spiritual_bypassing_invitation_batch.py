#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

OUT = Path('/tmp/spiritual-bypassing-visible-diagnostic-r14-2026-08-14.json')
AUDIT_ID = 'spiritual-bypassing-visible-owner-repair-2026-08-14'

EVIDENCE = '''Day five is where I get stuck. If I started dissociating then, I wouldn’t know what the instruction wants me to do with that. Is it a warning, or am I supposed to sit there and observe the warning too? There are plenty of “dark night” stories on r/vipassana. Critics talk about a “push through” culture. Some teachers compare intense practice without emotional groundwork to revving an engine without oil.'''

MECHANISM = '''Day five is where I get stuck. If I started dissociating then, I wouldn’t know what the instruction wants me to do with that. Is it a warning, or am I supposed to sit there and observe the warning too? The feeling comes up and, instead of healing what’s underneath it, you try to observe it away—to see it as insubstantial, not yours, and let it go. It can do the same thing with injustice: ignore it and call that inner peace.'''

spec = {
    'format': 'pangram-fixed-batch-v1',
    'experiment_id': 'spiritual-bypassing-visible-diagnostic-r14-2026-08-14',
    'audit_id': AUDIT_ID,
    'variants': [
        {'id': 'EVIDENCE_ONLY', 'section_id': 'day-five-diagnostic', 'text': EVIDENCE},
        {'id': 'MECHANISM_ONLY', 'section_id': 'day-five-diagnostic', 'text': MECHANISM},
    ],
}
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(OUT)
