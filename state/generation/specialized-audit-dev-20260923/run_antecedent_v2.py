#!/usr/bin/env python3
import hashlib, json, os, urllib.request, urllib.error, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
prompt=(ROOT/"antecedent-prompt-v2.txt").read_text()
cases=json.loads((ROOT/"antecedent-v2-cases.json").read_text())["cases"]
base=os.environ["UDA_MODEL_GATEWAY_URL"].rstrip("/")
token=os.environ["UDA_MODEL_GATEWAY_TOKEN"]
model=os.environ["UDA_MODEL_GATEWAY_MODEL"]
endpoint=base+"/v1/chat/completions"
print(json.dumps({"event":"antecedent_v2_start","case_count":len(cases),"model":model,"prompt_sha256":hashlib.sha256((ROOT/"antecedent-prompt-v2.txt").read_bytes()).hexdigest(),"cases_sha256":hashlib.sha256((ROOT/"antecedent-v2-cases.json").read_bytes()).hexdigest()}),flush=True)
for c in cases:
    user=prompt+"\n\nPREVIOUS CONTEXT:\n"+c["previous"]+"\n\nTARGET:\n"+c["target"]+"\n\nNEXT CONTEXT:\n"+c["next"]
    payload={"model":model,"temperature":0,"messages":[{"role":"user","content":user}]}
    req=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    started=time.time()
    try:
        with urllib.request.urlopen(req,timeout=180) as resp: raw=json.loads(resp.read().decode())
        content=raw["choices"][0]["message"]["content"]
        try: parsed=json.loads(content); parse_error=None
        except Exception as exc: parsed=None; parse_error=f"{type(exc).__name__}: {exc}"
        row={"event":"antecedent_v2_result","case_id":c["case_id"],"model":raw.get("model"),"response_id":raw.get("id"),"content":content,"parsed":parsed,"parse_error":parse_error,"usage":raw.get("usage"),"elapsed_seconds":round(time.time()-started,3)}
    except Exception as exc:
        row={"event":"antecedent_v2_transport_error","case_id":c["case_id"],"error_type":type(exc).__name__,"error":str(exc)}
    print(json.dumps(row,ensure_ascii=False),flush=True)
print(json.dumps({"event":"antecedent_v2_end"}),flush=True)
