#!/usr/bin/env python3
import json, runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r09.py', run_name='__main__')
base=Path('/tmp/spiritual-bypassing-r09.md').read_text(encoding='utf-8')
old='Some people love Goenka retreats. I also know people who came out in pieces. Both are real. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.'
assert base.count(old)==1
variants={
    'CONTROL_R09': old,
    'INVITE_A': 'Some people love Goenka retreats. I also know people who came out in pieces. Both are real. If yours helped you, I’m not arguing with you. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.',
    'INVITE_B': 'Some people love Goenka retreats. I also know people who came out in pieces. Both are real. Nobody has to reinterpret their own retreat for this article to matter. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.',
    'INVITE_C': 'Some people love Goenka retreats. I also know people who came out in pieces. Both are real. If your experience was good, keep it. I’m writing about what happens when it isn’t. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.',
}
spec={'format':'pangram-fixed-batch-v1','experiment_id':'spiritual-bypassing-invitation-batch-2026-08-13','variants':[]}
for vid, para in variants.items():
    text=base if vid=='CONTROL_R09' else base.replace(old,para,1)
    spec['variants'].append({'id':vid,'text':text})
Path('/tmp/spiritual-bypassing-invitation-batch.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('/tmp/spiritual-bypassing-invitation-batch.json')
