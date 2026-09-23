#!/usr/bin/env python3
import json, os, urllib.error, urllib.request
base=os.environ["UDA_MODEL_GATEWAY_URL"].rstrip("/")
token=os.environ["UDA_MODEL_GATEWAY_TOKEN"]
payload={"model":"gpt-5.6-sol","temperature":0,"messages":[{"role":"user","content":"Return exactly VENICE_TRANSPORT_PROBE_OK."}]}
req=urllib.request.Request(base+"/v1/chat/completions",data=json.dumps(payload).encode(),headers={
 "Authorization":"Bearer "+token,
 "Content-Type":"application/json",
},method="POST")
try:
    with urllib.request.urlopen(req,timeout=60) as resp:
        body=resp.read().decode(errors="replace")
        print(json.dumps({"status":resp.status,"body":body[:4000]}),flush=True)
except urllib.error.HTTPError as exc:
    body=exc.read().decode(errors="replace")
    print(json.dumps({"status":exc.code,"reason":str(exc),"body":body[:4000]}),flush=True)
