#!/usr/bin/env python3
import hashlib, json, os, time, urllib.error, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
LAB=ROOT.parents[2]
samples=json.loads((ROOT/"blind-samples.json").read_text())["samples"]
prompt_path=LAB/"state"/"generation"/"critic-contrastive-dev-20260923"/"contrastive-prompt-v3.txt"
prompt=prompt_path.read_text()
base=os.environ["UDA_MODEL_GATEWAY_URL"].rstrip("/")
token=os.environ["UDA_MODEL_GATEWAY_TOKEN"]
model=os.environ["UDA_MODEL_GATEWAY_MODEL"]
endpoint=base+"/v1/chat/completions"
print(json.dumps({"event":"holdout_v3_start","sample_count":len(samples),"model":model,"prompt_sha256":hashlib.sha256(prompt_path.read_bytes()).hexdigest(),"blind_sha256":hashlib.sha256((ROOT/"blind-samples.json").read_bytes()).hexdigest()}),flush=True)
for s in samples:
    started=time.time()
    payload={"model":model,"temperature":0,"messages":[{"role":"user","content":prompt+s["text"]}]}
    req=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=120) as resp:
            raw=json.loads(resp.read().decode())
        content=raw["choices"][0]["message"]["content"]
        try:
            parsed=json.loads(content); parse_error=None
        except Exception as exc:
            parsed=None; parse_error=f"{type(exc).__name__}: {exc}"
        row={"event":"holdout_v3_result","sample_id":s["sample_id"],"sample_sha256":s["sha256"],"word_count":s["word_count"],"model":raw.get("model"),"response_id":raw.get("id"),"content":content,"parsed":parsed,"parse_error":parse_error,"usage":raw.get("usage"),"elapsed_seconds":round(time.time()-started,3)}
    except urllib.error.HTTPError as exc:
        body=exc.read().decode(errors="replace")
        row={"event":"holdout_v3_transport_error","sample_id":s["sample_id"],"sample_sha256":s["sha256"],"http_status":exc.code,"error":str(exc),"response_body":body[:2000],"elapsed_seconds":round(time.time()-started,3)}
    except Exception as exc:
        row={"event":"holdout_v3_transport_error","sample_id":s["sample_id"],"sample_sha256":s["sha256"],"error_type":type(exc).__name__,"error":str(exc)[:1000],"elapsed_seconds":round(time.time()-started,3)}
    print(json.dumps(row,ensure_ascii=False),flush=True)
print(json.dumps({"event":"holdout_v3_end"}),flush=True)
