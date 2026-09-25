#!/usr/bin/env python3
import concurrent.futures, hashlib, json, os, time, urllib.error, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
cases=json.loads((ROOT/'cases-blind.json').read_text())['cases']
prompt=(ROOT/'global-tell-prompt.txt').read_text()
base=os.environ['UDA_MODEL_GATEWAY_URL'].rstrip('/')
token=os.environ['UDA_MODEL_GATEWAY_TOKEN']
models=['openai-gpt-6-sol','openai-gpt-6-astra']

def req(path, payload=None, timeout=600):
    headers={'Authorization':'Bearer '+token}
    data=None; method='GET'
    if payload is not None:
        data=json.dumps(payload).encode(); method='POST'; headers['Content-Type']='application/json'
    q=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    with urllib.request.urlopen(q,timeout=timeout) as r: return json.loads(r.read().decode())

catalog=req('/v1/models',timeout=60)
ids={x.get('id','') for x in catalog.get('data',[])}
missing=[m for m in models if m not in ids]
if missing:
    near=sorted(x for x in ids if 'gpt-6' in x.lower())
    print(json.dumps({'event':'model_catalog_error','missing':missing,'gpt6_models':near}),flush=True)
    raise SystemExit(2)

print(json.dumps({'event':'venice_max_start','models':models,'reasoning':{'effort':'max'},'max_completion_tokens':48000,'prompt_sha256':hashlib.sha256((ROOT/'global-tell-prompt.txt').read_bytes()).hexdigest(),'cases_sha256':hashlib.sha256((ROOT/'cases-blind.json').read_bytes()).hexdigest()}),flush=True)

def one(model,c):
    msg=prompt.replace('<PREVIOUS>',c['previous']).replace('<TARGET>',c['target']).replace('<NEXT>',c['next'])
    payload={'model':model,'reasoning':{'effort':'max'},'max_completion_tokens':48000,'messages':[{'role':'user','content':msg}],'response_format':{'type':'json_object'}}
    t=time.time()
    try:
        raw=req('/v1/chat/completions',payload,timeout=600)
        content=raw['choices'][0]['message']['content']
        try: parsed=json.loads(content); err=None
        except Exception as exc: parsed=None; err=f'{type(exc).__name__}: {exc}'
        return {'event':'venice_max_result','model':model,'case_id':c['case_id'],'provider_model':raw.get('model'),'response_id':raw.get('id'),'content':content,'parsed':parsed,'parse_error':err,'usage':raw.get('usage'),'elapsed_seconds':round(time.time()-t,3)}
    except Exception as exc:
        return {'event':'venice_max_transport_error','model':model,'case_id':c['case_id'],'error_type':type(exc).__name__,'error':str(exc)[:1500],'elapsed_seconds':round(time.time()-t,3)}

jobs=[(m,c) for m in models for c in cases]
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    futs={ex.submit(one,m,c):(m,c['case_id']) for m,c in jobs}
    for fut in concurrent.futures.as_completed(futs):
        row=fut.result(); rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
print(json.dumps({'event':'venice_max_end','result_count':sum(r['event']=='venice_max_result' for r in rows),'error_count':sum(r['event']!='venice_max_result' for r in rows)}),flush=True)