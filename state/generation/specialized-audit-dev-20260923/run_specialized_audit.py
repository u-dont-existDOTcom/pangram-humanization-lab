#!/usr/bin/env python3
import hashlib, json, os, time, urllib.error, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
cases=json.loads((ROOT/"cases-blind.json").read_text())["cases"]
prompts=json.loads((ROOT/"audit-prompts.json").read_text())
base=os.environ["UDA_MODEL_GATEWAY_URL"].rstrip("/")
token=os.environ["UDA_MODEL_GATEWAY_TOKEN"]
model=os.environ["UDA_MODEL_GATEWAY_MODEL"]
endpoint=base+"/v1/chat/completions"

print(json.dumps({
  "event":"specialized_start",
  "case_count":len(cases),
  "model":model,
  "blind_sha256":hashlib.sha256((ROOT/"cases-blind.json").read_bytes()).hexdigest(),
  "prompts_sha256":hashlib.sha256((ROOT/"audit-prompts.json").read_bytes()).hexdigest()
}),flush=True)

for c in cases:
    started=time.time()
    user=prompts[c["axis"]]+"\n\nPREVIOUS CONTEXT:\n"+c["previous"]+"\n\nTARGET:\n"+c["target"]+"\n\nNEXT CONTEXT:\n"+c["next"]
    payload={"model":model,"temperature":0,"messages":[{"role":"user","content":user}]}
    req=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=180) as resp:
            raw=json.loads(resp.read().decode())
        content=raw["choices"][0]["message"]["content"]
        try:
            parsed=json.loads(content); parse_error=None
        except Exception as exc:
            parsed=None; parse_error=f"{type(exc).__name__}: {exc}"
        row={"event":"specialized_result","case_id":c["case_id"],"axis":c["axis"],"model":raw.get("model"),"response_id":raw.get("id"),"content":content,"parsed":parsed,"parse_error":parse_error,"usage":raw.get("usage"),"elapsed_seconds":round(time.time()-started,3)}
    except urllib.error.HTTPError as exc:
        body=exc.read().decode(errors="replace")
        row={"event":"specialized_transport_error","case_id":c["case_id"],"axis":c["axis"],"http_status":exc.code,"error":str(exc),"response_body":body[:2000],"elapsed_seconds":round(time.time()-started,3)}
    except Exception as exc:
        row={"event":"specialized_transport_error","case_id":c["case_id"],"axis":c["axis"],"error_type":type(exc).__name__,"error":str(exc)[:1000],"elapsed_seconds":round(time.time()-started,3)}
    print(json.dumps(row,ensure_ascii=False),flush=True)

print(json.dumps({"event":"specialized_end"}),flush=True)
