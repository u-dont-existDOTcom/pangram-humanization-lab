#!/usr/bin/env python3
import runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r08.py', run_name='__main__')
source=Path('/tmp/spiritual-bypassing-r08.md')
out=Path('/tmp/spiritual-bypassing-r09.md')
text=source.read_text(encoding='utf-8')
old='the people most likely to be destabilized are screened out'
new='people with a recent history of mental instability are screened out'
if text.count(old) != 1:
    raise SystemExit(f'expected one r09 target, found {text.count(old)}')
out.write_text(text.replace(old,new,1),encoding='utf-8')
print(out)
