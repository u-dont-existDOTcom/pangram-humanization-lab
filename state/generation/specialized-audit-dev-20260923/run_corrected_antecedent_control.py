#!/usr/bin/env python3
import hashlib, json, os, time, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent
obj=json.loads((ROOT/"corrected-antecedent-control.json").read_text())
case=obj["case"]
prompts=json.loads((ROOT/"audit-prompts.json").read_text())
base=os.environ["UDA_MODEL_GATEWAY_URL"].rstrip("/")
token=os.environ["UDA_MODEL_GATEWAY_TOKEN"]
model=os.environ["UDA_MODEL_GATEWAY_MODEL"]
user=prompts[case["axis"]]+"\n\nPREVIOUS CONTEXT:\n"+case["previous"]+"\n\nTARGET:\n"+case["target"]+"\n\nNEXT CONTEXT:\n"+case["next"]
payload={"model":model,"temperature":0,"messages":[{"role":"user","content":user}]}
req=urllib.request.Request(base+"/v1/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
print(json.dumps({"event":"corrected_control_start","case_id":case["case_id"],"model":model,"case_sha256":hashlib.sha256((ROOT/"corrected-antecedent-control.json").read_bytes()).hexdigest()}),flush=True)
try:
    with urllib.request.urlopen(req,timeout=180) as resp:
        raw=json.loads(resp.read().decode())
    content=raw["choices"][0]["message"]["content"]
    try: parsed=json.loads(content); parse_error=None
    except Exception as exc: parsed=None; parse_error=f"{type(exc).__name__}: {exc}"
    row={"event":"corrected_control_result","case_id":case["case_id"],"model":raw.get("model"),"response_id":raw.get("id"),"content":content,"parsed":parsed,"parse_error":parse_error,"usage":raw.get("usage")}
except Exception as exc:
    row={"event":"corrected_control_transport_error","case_id":case["case_id"],"error_type":type(exc).__name__,"error":str(exc)}
print(json.dumps(row,ensure_ascii=False),flush=True)
print(json.dumps({"event":"corrected_control_end"}),flush=True)
