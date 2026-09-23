#!/usr/bin/env python3
import hashlib,json,os,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent
cases=json.loads((ROOT/"antecedent-v3-cases.json").read_text())["cases"]
prompt=(ROOT/"antecedent-prompt-v3.txt").read_text()
base=os.environ["UDA_MODEL_GATEWAY_URL"].rstrip("/")
token=os.environ["UDA_MODEL_GATEWAY_TOKEN"]
model=os.environ["UDA_MODEL_GATEWAY_MODEL"]
endpoint=base+"/v1/chat/completions"
print(json.dumps({"event":"antecedent_v3_start","case_count":len(cases),"model":model,"prompt_sha256":hashlib.sha256((ROOT/"antecedent-prompt-v3.txt").read_bytes()).hexdigest(),"cases_sha256":hashlib.sha256((ROOT/"antecedent-v3-cases.json").read_bytes()).hexdigest()}),flush=True)
for c in cases:
    msg=prompt+"\n\nPREVIOUS CONTEXT:\n"+c["previous"]+"\n\nTARGET:\n"+c["target"]+"\n\nNEXT CONTEXT:\n"+c["next"]
    started=time.time()
    req=urllib.request.Request(endpoint,data=json.dumps({"model":model,"temperature":0,"messages":[{"role":"user","content":msg}]}).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=180) as resp: raw=json.loads(resp.read().decode())
        content=raw["choices"][0]["message"]["content"]
        try: parsed=json.loads(content); err=None
        except Exception as exc: parsed=None; err=f"{type(exc).__name__}: {exc}"
        row={"event":"antecedent_v3_result","case_id":c["case_id"],"model":raw.get("model"),"response_id":raw.get("id"),"content":content,"parsed":parsed,"parse_error":err,"usage":raw.get("usage"),"elapsed_seconds":round(time.time()-started,3)}
    except Exception as exc:
        row={"event":"antecedent_v3_transport_error","case_id":c["case_id"],"error_type":type(exc).__name__,"error":str(exc)[:1000],"elapsed_seconds":round(time.time()-started,3)}
    print(json.dumps(row,ensure_ascii=False),flush=True)
print(json.dumps({"event":"antecedent_v3_end"}),flush=True)
