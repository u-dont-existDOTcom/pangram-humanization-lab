#!/usr/bin/env python3
import json, runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r12.py', run_name='__main__')
base = Path('/tmp/spiritual-bypassing-r12.md').read_text(encoding='utf-8')

minimal = ("A metta-heavy retreat would be my first choice. Trauma-informed mindfulness—maybe "
           "Mindfulness-Based Stress Reduction plus therapy—is another. [Insight Meditation Society]"
           "(http://dharma.org) and [Plum Village](http://plumvillage.org) are two places I’d look, "
           "along with a teacher who understands trauma. Your path is yours to shape.")

lines = base.splitlines()
h = lines.index('# Trauma-Informed Retreat Alternatives')
thanks = next(i for i, line in enumerate(lines) if line.startswith('Thanks for reading. Drop your thoughts'))
intro = lines[h + 2]
lines[h + 2:thanks] = [intro, '', minimal, '']
variant = '\n'.join(lines) + '\n'

spec = {
    'format':'pangram-fixed-batch-v1',
    'experiment_id':'spiritual-bypassing-r14-minimal-alternatives-2026-08-13',
    'variants':[
        {'id':'CONTROL_R12','text':base},
        {'id':'MINIMAL_SOURCE_FAITHFUL','text':variant},
    ],
}
Path('/tmp/spiritual-bypassing-r14-batch.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

candidate = Path('state/candidates/spiritual-bypassing-r14-source-faithful.md')
candidate.parent.mkdir(parents=True, exist_ok=True)
candidate.write_text(variant, encoding='utf-8')
