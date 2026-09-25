#!/usr/bin/env python3
import json, os, time, urllib.request, urllib.error, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parent
cases=json.loads((ROOT/"cases-blind.json").read_text())["cases"]
template=(ROOT/"global-tell-prompt.txt").read_text()
api_key=os.environ["OPENROUTER_API_KEY"]
endpoint="https://openrouter.ai/api/v1/chat/completions"
models=["anthropic/claude-opus-5.5","openai/gpt-6-sol"]

print(json.dumps({
  "event":"compare_start",
  "models":models,
  "case_count":len(cases),
  "prompt_sha256":hashlib.sha256((ROOT/"global-tell-prompt.txt").read_bytes()).hexdigest(),
  "cases_sha256":hashlib.sha256((ROOT/"cases-blind.json").read_bytes()).hexdigest()
}),flush=True)

for model in models:
  for c in cases:
    msg=template.replace("<PREVIOUS>",c["previous"]).replace("<TARGET>",c["target"]).replace("<NEXT>",c["next"])
    payload={
      "model":model,
      "temperature":0,
      "messages":[{"role":"user","content":msg}],
      "response_format":{"type":"json_object"}
    }
    req=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={
      "Authorization":"Bearer "+api_key,
      "Content-Type":"application/json",
      "HTTP-Referer":"https://github.com/u-dont-existDOTcom/pangram-humanization-lab",
      "X-Title":"Joel Global Tell Ledger Comparison"
    },method="POST")
    started=time.time()
    try:
      with urllib.request.urlopen(req,timeout=240) as resp:
        raw=json.loads(resp.read().decode())
      content=raw["choices"][0]["message"]["content"]
      try:
        parsed=json.loads(content); parse_error=None
      except Exception as exc:
        parsed=None; parse_error=f"{type(exc).__name__}: {exc}"
      row={
        "event":"compare_result",
        "requested_model":model,
        "case_id":c["case_id"],
        "provider_model":raw.get("model"),
        "response_id":raw.get("id"),
        "content":content,
        "parsed":parsed,
        "parse_error":parse_error,
        "usage":raw.get("usage"),
        "elapsed_seconds":round(time.time()-started,3)
      }
    except urllib.error.HTTPError as exc:
      body=exc.read().decode(errors="replace")
      row={
        "event":"compare_transport_error",
        "requested_model":model,
        "case_id":c["case_id"],
        "http_status":exc.code,
        "error":str(exc),
        "response_body":body[:3000],
        "elapsed_seconds":round(time.time()-started,3)
      }
    except Exception as exc:
      row={
        "event":"compare_transport_error",
        "requested_model":model,
        "case_id":c["case_id"],
        "error_type":type(exc).__name__,
        "error":str(exc)[:2000],
        "elapsed_seconds":round(time.time()-started,3)
      }
    print(json.dumps(row,ensure_ascii=False),flush=True)

print(json.dumps({"event":"compare_end"}),flush=True)
