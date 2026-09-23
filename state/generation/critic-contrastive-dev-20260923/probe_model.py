#!/usr/bin/env python3
import json, os, urllib.error, urllib.request
base=os.environ["UDA_MODEL_GATEWAY_URL"].rstrip("/")
token=os.environ["UDA_MODEL_GATEWAY_TOKEN"]
model=os.environ["UDA_MODEL_GATEWAY_MODEL"]
payload={"model":model,"temperature":0,"messages":[{"role":"user","content":"Return exactly MODEL_PROBE_OK."}]}
req=urllib.request.Request(base+"/v1/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
try:
    with urllib.request.urlopen(req,timeout=60) as resp:
        body=json.loads(resp.read().decode())
        print(json.dumps({"status":resp.status,"requested_model":model,"returned_model":body.get("model"),"content":body.get("choices",[{}])[0].get("message",{}).get("content"),"cost":body.get("cost")}),flush=True)
except urllib.error.HTTPError as exc:
    body=exc.read().decode(errors="replace")
    print(json.dumps({"status":exc.code,"requested_model":model,"error":str(exc),"body":body[:2000]}),flush=True)
