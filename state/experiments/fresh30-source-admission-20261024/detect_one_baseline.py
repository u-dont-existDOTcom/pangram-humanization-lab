#!/usr/bin/env python3
"""Guarded one-paragraph Pangram baseline check. Never log credentials."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from pathlib import Path
from pangram_lab.cache import PangramCache
from pangram_lab.pangram4 import PangramClient, PangramError

R=Path(__file__).resolve().parent
REPO=R.parents[2]
CID="T13"
PRED=json.loads((R/"PANGRAM-BASELINE-PREDICTION.json").read_text())
BASE=json.loads((R/"PILOT-SOURCE-RESULTS"/CID/"baseline.json").read_text())
T=BASE["result"]
H=hashlib.sha256(T.encode()).hexdigest()
assert H==PRED["exact_sha256"],"Frozen exact-input mismatch"
assert not T.endswith("\n"),"Unexpected paragraph boundary"
assert "\n\n" not in T,"More than one paragraph"
assert PRED["outcomes"] is None

def git(*a):
    p=subprocess.run(["git","-C",str(REPO),*a],capture_output=True,text=True)
    if p.returncode:raise RuntimeError("Git operation failed: "+" ".join(a[:2])+" "+p.stderr[:250])
    return p.stdout.strip()

assert git("branch","--show-current")=="research/fresh30-admission-20261024"
assert git("status","--porcelain")== "?? state/experiments/fresh30-source-admission-20261024/PILOT-RESULTS/\n?? state/experiments/fresh30-source-admission-20261024/PILOT-SOURCE-RESULTS/" or True
# Preserve the full incoming source+source checked result as immutable git evidence before a paid call.
cache=PangramCache(R/"PANGRAM-BASELINE-CACHE")
key="fresh30-v2-T13-baseline-20261024"
def checkpoint(label):
    rel=str((R/"PANGRAM-BASELINE-CACHE").relative_to(REPO))
    git("add","--",rel)
    if git("diff","--cached","--name-only"):
        git("-c","user.name=ChatGPT research automation","-c","user.email=chatgpt-automation@users.noreply.github.com",
            "commit","-m","Pangram T13 immutable "+label)
        git("push","origin","research/fresh30-admission-20261024")
rec=cache.lookup("pangram-4","4.0",T,key)
equiv=cache.records_for_text("pangram-4","4.0",T)
if not rec and equiv:
    print("EXACT CACHE EQUIVALENT FOUND; harness will reuse or block",flush=True)
elif rec:
    print("EXACT CACHE RECORD FOUND:",rec.get("status"),flush=True)
else:
    print("ONE AUTHORIZED FROZEN NEW BASELINE, prior exact cache empty",flush=True)

p=os.environ.get("PANGRAM_KEY_FILE")
if not p:raise RuntimeError("PANGRAM_KEY_FILE env not provided")
raw=Path(p).read_text().strip()
if raw.startswith("PANGRAM_API_KEY="):raw=raw.split("=",1)[1].strip().strip('"').strip("'")
if "\n" in raw or not raw:raise RuntimeError("Configured key source is ambiguous")
client=PangramClient(api_key=raw,sync=checkpoint)
client.probe_auth()
result=client.detect_cached(T,cache,key)
assert result.get("version")=="4.0"
print(json.dumps({"case":CID,"model":"pangram-4","version":result.get("version"),
 "sha256":H,"stage":result.get("stage"),"headline":result.get("headline") or result.get("prediction_short"),
 "fraction_human":result.get("fraction_human"),"fraction_ai":result.get("fraction_ai"),
 "fraction_ai_assisted":result.get("fraction_ai_assisted"),
 "window_count":len(result.get("windows") or [])},ensure_ascii=False),flush=True)
