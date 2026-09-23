#!/usr/bin/env python3
import json, os, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
prompt=(ROOT/"antecedent-prompt-v2.txt").read_text()
obj=json.loads((ROOT/"antecedent-v2-human-control.json").read_text())
c=obj["case"]
base=os.environ["UDA_MODEL_GATEWAY_URL"].rstrip("/")
token=os.environ["UDA_MODEL_GATEWAY_TOKEN"]
model=os.environ["UDA_MODEL_GATEWAY_MODEL"]
user=prompt+"\n\nPREVIOUS CONTEXT:\n"+c["previous"]+"\n\nTARGET:\n"+c["target"]+"\n\nNEXT CONTEXT:\n"+c["next"]
payload={"model":model,"temperature":0,"messages":[{"role":"user","content":user}]}
req=urllib.request.Request(base+"/v1/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
print(json.dumps({"event":"antecedent_human_start","case_id":c["case_id"],"model":model}),flush=True)
with urllib.request.urlopen(req,timeout=180) as resp:
    raw=json.loads(resp.read().decode())
content=raw["choices"][0]["message"]["content"]
try: parsed=json.loads(content); parse_error=None
except Exception as exc: parsed=None; parse_error=f"{type(exc).__name__}: {exc}"
print(json.dumps({"event":"antecedent_human_result","case_id":c["case_id"],"model":raw.get("model"),"response_id":raw.get("id"),"content":content,"parsed":parsed,"parse_error":parse_error,"usage":raw.get("usage")},ensure_ascii=False),flush=True)
print(json.dumps({"event":"antecedent_human_end"}),flush=True)
