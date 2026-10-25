#!/usr/bin/env python3
"""At most six first-pass, one-paragraph Pangram baseline eligibility checks.

Predictions are committed in BASELINE-DETECTOR-FORECASTS.json; raw credentials
are never logged or saved. All possible paid states are checkpointed to Git.
"""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path
from pangram_lab.cache import PangramCache
from pangram_lab.pangram4 import PangramClient
R=Path(__file__).resolve().parent
REPO=R.parents[2]
F=json.loads((R/"BASELINE-DETECTOR-FORECASTS.json").read_text())
assert F["outcomes"] is None and len(F["sample"])==6
cache=PangramCache(R/"PANGRAM-BASELINE-CACHE")
MODEL="pangram-4"
VERSION="4.1"

def git(*args):
    p=subprocess.run(["git","-C",str(REPO),*args],capture_output=True,text=True)
    if p.returncode:raise RuntimeError("Git checkpoint command failed: "+" ".join(args[:2])+" "+p.stderr[:300])
    return p.stdout.strip()
def checkpoint(label):
    path=str((R/"PANGRAM-BASELINE-CACHE").relative_to(REPO))
    git("add","--",path)
    if git("diff","--cached","--name-only"):
        git("-c","user.name=ChatGPT research automation",
            "-c","user.email=chatgpt-automation@users.noreply.github.com",
            "commit","-m","Pangram 4.1 exact baseline measurement checkpoint: "+label)
        git("push","origin","research/fresh30-admission-20261024")
def checkpoint_report():
    git("add","--",str((R/"BASELINE-DETECTOR-OBSERVATIONS.json").relative_to(REPO)))
    if git("diff","--cached","--name-only"):
        git("-c","user.name=ChatGPT research automation",
            "-c","user.email=chatgpt-automation@users.noreply.github.com",
            "commit","-m","Record prior-frozen baseline forecasts vs Pangram 4.1 outcomes")
        git("push","origin","research/fresh30-admission-20261024")

assert git("branch","--show-current")=="research/fresh30-admission-20261024"
assert not git("diff","--name-only")
assert not git("diff","--cached","--name-only")
pth=os.environ.get("PANGRAM_KEY_FILE")
if not pth:raise RuntimeError("Configure PANGRAM_KEY_FILE without echoing its contents")
key=Path(pth).read_text(encoding="utf-8").strip()
if key.startswith("PANGRAM_API_KEY="):key=key.split("=",1)[1].strip().strip('"').strip("'")
if not key or "\n" in key:raise RuntimeError("Invalid key format, no detector submission")
client=PangramClient(api_key=key,model=MODEL,expected_version=VERSION,sync=checkpoint)
client.probe_auth()
observed=[]
for item in F["sample"]:
    cid=item["id"]
    rr=R/"PILOT-RESTRICTED-RESULTS"/cid/"baseline.json"
    obj=json.loads(rr.read_text())
    txt=obj["result"]
    digest=hashlib.sha256(txt.encode("utf-8")).hexdigest()
    assert digest==item["sha256"] and "\n" not in txt.strip(),cid
    mk="fresh30-v3-baseline-"+cid+"-20261025"
    old=cache.lookup(MODEL,VERSION,txt,mk)
    if old:print("EXISTING_CACHE",cid,old.get("status"),flush=True)
    else:print("FROZEN_ELIGIBILITY_SUBMISSION",cid,digest[:16],flush=True)
    value=client.detect_cached(txt,cache,mk)
    assert value.get("stage")=="STAGE_SUCCESS" and value.get("version")==VERSION
    assert value.get("text")==txt, "Provider exact text mismatch"
    windows=[{"label":w.get("label"),"confidence":w.get("confidence")} for w in value.get("windows") or []]
    allhuman=(value.get("fraction_human")==1.0 and
      value.get("fraction_ai")==0.0 and value.get("fraction_ai_assisted")==0.0)
    hit=cache.lookup(MODEL,VERSION,txt,mk)
    observed.append({"id":cid,"sha256":digest,"actual_version":VERSION,
      "forecast_probability_all_human":item["p_all_human"],
      "forecast_verdict":item["decision"],
      "detector_stage":value.get("stage"),"headline":value.get("headline"),
      "fraction_human":value.get("fraction_human"),"fraction_ai":value.get("fraction_ai"),
      "fraction_ai_assisted":value.get("fraction_ai_assisted"),"all_human":allhuman,
      "windows":windows,"cache_source":hit.get("source"),
      "task_recorded":bool(hit.get("task_id"))})
    print("MEASURED",cid,"version",VERSION,"headline",value.get("headline"),
      "all_human",allhuman,flush=True)
    report={"schema":"fresh30-baseline-detector-result-v1","requested_model":MODEL,
       "verified_backend_version":VERSION,"forecast_source":"BASELINE-DETECTOR-FORECASTS.json",
       "selection_rule":F["selection_rule"],"source_count":len(F["sample"]),
       "measured_count":len(observed),"measurements":observed,
       "note":"One paragraph per call, cache/checkpoint and no automatic duplicate submit. Observations apply to model-transformed baselines only, not the owner source or both writing arms."}
    (R/"BASELINE-DETECTOR-OBSERVATIONS.json").write_text(
       json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    checkpoint_report()
print("DONE",len(observed),"full-Human",sum(x["all_human"] for x in observed),
 "non-Human",sum(not x["all_human"] for x in observed),flush=True)
