#!/usr/bin/env python3
import runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r09.py', run_name='__main__')
source=Path('/tmp/spiritual-bypassing-r09.md')
out=Path('/tmp/spiritual-bypassing-r10.md')
text=source.read_text(encoding='utf-8')
old='Some people love Goenka retreats. I also know people who came out in pieces. Both are real. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.'
new='Some people love Goenka retreats. I also know people who came out in pieces. Both are real. Take what’s useful here and leave the rest. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.'
if text.count(old) != 1:
    raise SystemExit(f'expected one r10 target, found {text.count(old)}')
out.write_text(text.replace(old,new,1),encoding='utf-8')
print(out)
