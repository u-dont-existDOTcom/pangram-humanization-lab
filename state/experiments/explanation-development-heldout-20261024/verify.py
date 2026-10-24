from pathlib import Path
import json,hashlib,re,math
p=Path(__file__).resolve().parent
d=json.loads((p/'RESULT.json').read_text()); inputs=json.loads((p/'INPUTS.json').read_text())
frozen=(p/'v2-predictions.frozen.json').read_bytes()
assert hashlib.sha256(frozen).hexdigest()==d['holdout']['summary']['prediction_hash']
rows=d['holdout']['rows']; assert len(rows)==15 and len({r['family'] for r in rows})==15
assert sum(r['correct'] for r in rows)==11
assert sum(r['human'] for r in rows)==10
assert math.isclose(sum((r['p_human']-r['human'])**2 for r in rows)/15,d['holdout']['summary']['brier'])
assert len(d['api_observations'])==8
for x in d['api_observations']:
 t=inputs[x['id']];r=x['result']
 assert hashlib.sha256(t.encode()).hexdigest()==x['input_sha256']
 assert r['text']==t and ''.join(y['text'] for y in r['windows'])==t
 assert r['stage']=='STAGE_SUCCESS' and str(r['version'])=='4.1'
 assert len([z for z in re.split(r'\n\s*\n',t) if z.strip()])==1
 assert x['local_words']==len(t.split())
 assert x['all_segments_human']==all(y['label'].lower().startswith('human') for y in r['windows'])
assert sum(x['local_words'] for x in d['api_observations'])==644
assert sum(x['all_segments_human'] for x in d['api_observations'])==1
for name,sha in json.loads((p/'MANIFEST.json').read_text()).items():
 assert hashlib.sha256((p/name).read_bytes()).hexdigest()==sha,name
print('PASS: frozen forecasts; 15 exact outcomes; 8 exact API inputs, versions and window coverage; 644 words; manifest.')
