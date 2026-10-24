from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent
r=json.loads((p/'RESULT.json').read_text()); rows=r['offline']['rows']; s=r['offline']['summary']
assert len(rows)==12 and sum(x['correct'] for x in rows)==9
assert sum(x['human'] for x in rows)==8
assert abs(sum((x['p_all_human']-x['human'])**2 for x in rows)/12-s['brier'])<1e-12
assert hashlib.sha256((p/'PREDICTIONS.frozen.json').read_bytes()).hexdigest()==s['forecast_sha256']
for x in rows: assert hashlib.sha256(x['text'].encode()).hexdigest()==x['sha256']
b=next(x['text'] for x in r['archived_controlled_contrasts'] if x['name']=='t102b_untangle_old')
for x in r['archived_controlled_contrasts']:
 assert hashlib.sha256(x['text'].encode()).hexdigest()==x['result']['sha256']
 if x['name']=='t102_untangle_p': assert x['text'].replace(x['added_span']+' ','')==b
 elif x['name']=='t102c_untangle_u02': assert x['text'].replace(x['added_span']+' ','')==b
 elif x['name']=='t102c_untangle_u03': assert x['text'].replace(' '+x['added_span'],'')==b
assert r['live_api']['accepted_submissions']==0 and r['live_api']['prepared_cells']==8
inputs=json.loads((p/'UNEXECUTED-API-INPUTS.json').read_text()); protocol=json.loads((p/'UNEXECUTED-API-PROTOCOL.json').read_text())
for v in protocol['variants']: assert hashlib.sha256(inputs[v['id']].encode()).hexdigest()==v['sha256'] and 1<=v['paragraphs']<=3
for n,sha in json.loads((p/'MANIFEST.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==sha
print('PASS:12 forecasts, source hashes,3 exact insertion-only contrasts,8 unexecuted cells, zero new API calls and manifest.')
