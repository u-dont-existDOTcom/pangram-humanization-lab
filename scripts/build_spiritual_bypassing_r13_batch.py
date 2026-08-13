#!/usr/bin/env python3
import json, runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r12.py', run_name='__main__')
base = Path('/tmp/spiritual-bypassing-r12.md').read_text(encoding='utf-8')

bypass = ('Spiritual bypassing is the catch here. Equanimity can be used to sidestep the emotional '
          'mess instead of healing it. Or to ignore injustice and call that inner peace. Remember '
          'some of the Buddhist responses to the Myanmar coup?')

alternatives = ("I’d start with metta. If that felt steady and I still wanted more, maybe trauma-informed "
                "mindfulness or Mindfulness-Based Stress Reduction with a therapist. If I still wanted a "
                "retreat after that, I’d ask [Insight Meditation Society](http://dharma.org), "
                "[Plum Village](http://plumvillage.org), or whoever I was considering how they handle "
                "destabilization and whether pausing the practice is treated as an ordinary option.\n\n"
                "That matters to me. A trauma-informed retreat shouldn’t turn continuing into a test of character. "
                "Your path is yours to shape.")


def replace_bypass(text: str) -> str:
    lines = text.splitlines()
    anchor = 'I would rather have people learn how to meet suffering with love before any of that starts.'
    i = lines.index(anchor)
    assert lines[i - 1] == '' and 'spiritual bypassing' in lines[i - 2]
    lines[i - 2] = bypass
    return '\n'.join(lines) + '\n'


def replace_alternatives(text: str) -> str:
    lines = text.splitlines()
    h = lines.index('# Trauma-Informed Retreat Alternatives')
    thanks = next(i for i, line in enumerate(lines) if line.startswith('Thanks for reading. Drop your thoughts'))
    intro = lines[h + 2]
    replacement = [intro, '', *alternatives.splitlines(), '']
    lines[h + 2:thanks] = replacement
    return '\n'.join(lines) + '\n'

variants = [
    ('CONTROL_R12', base),
    ('BYPASS_SOURCE_CLOSE', replace_bypass(base)),
    ('ALT_INVITATIONAL', replace_alternatives(base)),
    ('BOTH', replace_alternatives(replace_bypass(base))),
]
spec = {'format':'pangram-fixed-batch-v1','experiment_id':'spiritual-bypassing-r13-interaction-2026-08-13','variants':[]}
for vid, text in variants:
    spec['variants'].append({'id':vid,'text':text})
Path('/tmp/spiritual-bypassing-r13-batch.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
