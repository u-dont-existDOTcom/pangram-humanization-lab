#!/usr/bin/env python3
"""Read-only source, scope, response and scoring integrity check. No model/API calls."""
from pathlib import Path
import json,hashlib,importlib.util
R=Path(__file__).resolve().parent
SHA=lambda t:hashlib.sha256(t.encode()).hexdigest()
def load(n):return json.loads((R/n).read_text())
spec=importlib.util.spec_from_file_location('bounded',R/'run_bounded.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
inputs=load('INPUTS.json')['cases'];candidates={x['id']:x for x in load('CANDIDATES.json')['cases']};result=load('RESULTS.json');rows={x['id']:x for x in result['rows']}
assert len(inputs)==len(candidates)==len(rows)==12
calls=0;expected={'literal_owner_scope_preserved':0,'no_change':0,'changed':0,'small_cleanup_candidates':0,'no_clear_style_gain':0,'fidelity_rejected':0,'changed_with_no_material_delta_reported':0,'style_rank_and_verbal_disagreements':0,'model_calls':0,'new_Pangram_calls':0}
for c in inputs:
 assert SHA(c['baseline'])==c['baseline_sha256'] and SHA(c['original_paragraph'])==c['source_reference']['source_paragraph_sha256']
 assert SHA(c['context'])==c['context_sha256']
 assert c['baseline'] in c['context']
 cid=c['id'];candidate=candidates[cid];r=rows[cid]
 out=m.assemble(c,candidate['edits']);assert out==candidate['candidate'] and SHA(out)==candidate['candidate_sha256']
 assert (out!=c['baseline'])==candidate['changed']
 expected['literal_owner_scope_preserved']+=1
 expected['changed']+=candidate['changed'];expected['no_change']+=not candidate['changed']
 for rec in (R/'OUTPUTS'/cid).rglob('RECORD.json'):
  d=json.loads(rec.read_text());text=(rec.parent/'PROMPT.txt').read_text();assert SHA(text)==d['prompt_sha256'];assert SHA(d['result'])==d['response_sha256'];assert d['returncode']==0 and d['parsed'] is not None;calls+=1
 if candidate['changed']:
  st=json.loads((R/'OUTPUTS'/cid/'STYLE/RECORD.json').read_text())['parsed'];dt=json.loads((R/'OUTPUTS'/cid/'DELTA/RECORD.json').read_text())['parsed'];mp=c['anonymous_style_map'];scores={mp[k]:float(st[k]['voice_score_1_to_5']) for k in ['X','Y']};verbal=mp.get(st['preference'],st['preference']);numeric='candidate' if scores['candidate']>scores['baseline'] else 'baseline' if scores['candidate']<scores['baseline'] else 'TIE'
  assert scores==r['style_scores'] and verbal==r['style_verbal_preference'] and numeric==r['style_numeric_preference']
  n=sum(x.get('material') is True for x in dt['differences']);assert n==r['reported_material_deltas']
  expected['changed_with_no_material_delta_reported']+=n==0;expected['style_rank_and_verbal_disagreements']+=verbal!=numeric
  disp='FIDELITY_REJECTED' if n else 'LOCAL_CLEANUP_CANDIDATE' if numeric==verbal=='candidate' else 'NO_CLEAR_STYLE_GAIN';assert r['evidence_disposition']==disp
  key={'FIDELITY_REJECTED':'fidelity_rejected','LOCAL_CLEANUP_CANDIDATE':'small_cleanup_candidates','NO_CLEAR_STYLE_GAIN':'no_clear_style_gain'}[disp];expected[key]+=1
 else:assert r['evidence_disposition']=='UNCHANGED_BASELINE'
expected['model_calls']=calls;assert expected==result['counts']
assert expected['model_calls']==24 and expected['fidelity_rejected']==1
assert rows['F25']['evidence_disposition']=='FIDELITY_REJECTED'
print(json.dumps({'result':'PASS','source_cases':12,'assembled_exactly':12,'prompt_response_pairs':calls,'counts':expected},ensure_ascii=False))
