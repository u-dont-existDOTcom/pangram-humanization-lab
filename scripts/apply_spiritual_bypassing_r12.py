#!/usr/bin/env python3
import runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r09.py', run_name='__main__')
source = Path('/tmp/spiritual-bypassing-r09.md')
out = Path('/tmp/spiritual-bypassing-r12.md')
lines = source.read_text(encoding='utf-8').splitlines()

# Fidelity repair 1: remove the invented autobiographical framing from the opening.
assert lines[0] == '# A Primer on Spiritual Bypassing'
assert lines[1] == ''
assert lines[2].startswith('I have a problem with Goenka retreats')
lines[2] = ('I have a problem with Goenka retreats: people with a recent history of mental '
            'instability are screened out, but the people who get in are still taught basically '
            'one response to whatever surfaces—observe it and don’t react.')

# Fidelity repair 2: restore the source-level spiritual-bypassing claim. Locate the paragraph
# immediately before the preserved metta transition, rather than reproducing the superseded text.
anchor = 'I would rather have people learn how to meet suffering with love before any of that starts.'
i = lines.index(anchor)
assert i >= 2 and lines[i - 1] == ''
assert 'spiritual bypassing' in lines[i - 2]
lines[i - 2] = ('That is where spiritual bypassing enters the picture for me. Equanimity can become '
                'a way to avoid emotional mess instead of healing it. It can also become a way to '
                'ignore injustice while calling that inner peace. Remember some of the Buddhist '
                'responses to the Myanmar coup?')

out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(out)
