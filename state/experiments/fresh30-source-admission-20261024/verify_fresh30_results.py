#!/usr/bin/env python3
"""Read-only evidence integrity checks; no models, network, or detector calls."""
import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parent
H=lambda x:hashlib.sha256(x.encode()).hexdigest()
J=lambda p:json.loads((R/p).read_text())
cohort=J('COHORT.json');assert len(cohort['source_texts'])==30
assert len({x['id'] for x in cohort['source_texts']})==30
assert collections.Counter(x['article'] for x in cohort['source_texts'])==dict.fromkeys(['romance','communities','inner-child','hypnosis','nibbana','somatic'],5)
for x in cohort['source_texts']:assert H(x['source_text'])==x['source_sha256'],x['id']
rows=[];checked=0
for c in cohort['source_texts']:
 p=R/'PILOT-RESTRICTED-RESULTS'/c['id']
 for f in p.glob('*.json'):
  x=json.loads(f.read_text())
  if 'result_sha256' in x:assert H(x['result'])==x['result_sha256'];checked+=1
 if (p/'blind_review.json').exists():
  z=J(str((p/'blind_review.json').relative_to(R)))['result'];z=json.loads(z[z.index('{'):z.rindex('}')+1]);mp=json.loads((p/'anonymous-label-map.json').read_text());arm={mp[k]:z[k] for k in ('X','Y')};rows.append({'id':c['id'],'A':arm['A'],'B':arm['B'],'pref':mp.get(z['preference'],z['preference'])})
assert len(rows)==27
assert sum(x['B']['voice_score_1_to_5']>x['A']['voice_score_1_to_5'] for x in rows)==15
assert collections.Counter(x['pref'] for x in rows)=={'A':19,'B':6,'TIE':2}
assert sum(x['A']['fidelity_ok'] for x in rows)==27 and sum(x['B']['fidelity_ok'] for x in rows)==21
unique={}
for f in (R/'PANGRAM-BASELINE-CACHE').rglob('*.json'):
 x=json.loads(f.read_text());d=x.get('result')
 if not d:continue
 assert H(x['text'])==x['text_sha256'] and d['text']==x['text']
 assert d['stage']=='STAGE_SUCCESS' and d['version']=='4.1'
 unique[x['task_id']]=x
assert len(unique)==10 and sum(len(x['text'].split()) for x in unique.values())==823
assert all(len([p for p in x['text'].split('\n\n') if p.strip()])==1 for x in unique.values())
adj=J('BASELINE-DETECTOR-ADJUDICATION.json');assert adj['categorical_Human']==4 and adj['categorical_AI']==2
arm=J('ARM-DETECTOR-RESULTS.json');assert len(arm['readings'])==3
assert all(x['headline']=='AI Generated' and x['fraction_ai']==1.0 for x in arm['readings'])
base=J('PILOT-RESTRICTED-RESULTS/T26/baseline.json')['result'];same=J('PILOT-RESTRICTED-RESULTS/T26/arm_A.json')['result'];assert base==same
pool=J('CANDIDATE-POOL-RESULT.json');assert [x['joint_choice'] for x in pool['cases']]==['old_A','old_A']
for f in (R/'PILOT-CANDIDATE-POOL').glob('*/*/RECORD.json'):
 x=json.loads(f.read_text());assert H(x['result'])==x['result_sha256'];checked+=1
old=J('REVIEWER-CALIBRATION/RESULTS.json');new=J('REVIEWER-CALIBRATION/STYLE-ONLY-RESULTS.json')
assert len(old['cases'])==4 and sum(x['naturalness_matches_owner'] for x in old['cases'])==0
assert sum(x['fidelity_matches_owner'] is True for x in old['cases'])==1
assert len(new['cases'])==4 and sum(x['naturalness_matches_owner'] for x in new['cases'])==3
for f in (R/'REVIEWER-CALIBRATION').glob('**/PROMPT.json'):
 x=json.loads(f.read_text());assert H(x['exact_prompt'])==x['sha256']
print(json.dumps({'result':'PASS','source_hashes':30,'model_output_hashes':checked,'paired_outputs':27,'distinct_detector_tasks':10,'submitted_paragraph_max':1,'baseline_Human_AI':[4,2],'mixed_reviewer_style_matches':[0,4],'separated_style_matches':[3,4],'new_paid_calls':0}))
