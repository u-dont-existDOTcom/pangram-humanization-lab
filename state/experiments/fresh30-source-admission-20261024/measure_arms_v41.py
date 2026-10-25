#!/usr/bin/env python3
"""Three immutable one-paragraph Pangram 4.1 predictions; no arbitrary retries."""
from __future__ import annotations
import hashlib,json,os,subprocess
from pathlib import Path
from pangram_lab.cache import PangramCache
from pangram_lab.pangram4 import PangramClient
R=Path(__file__).resolve().parent
REPO=R.parents[2]
F=json.loads((R/"ARM-DETECTOR-PREDICTIONS.json").read_text())
assert F["results"] is None and len(F["predictions"])==3
C=PangramCache(R/"PANGRAM-BASELINE-CACHE")
MODEL,VERSION="pangram-4","4.1"
MEASUREMENTS="ARM-DETECTOR-RESULTS.json"
def git(*args):
    v=subprocess.run(["git","-C",str(REPO),*args],capture_output=True,text=True)
    if v.returncode:raise RuntimeError("Git checkpoint failure "+str(args[:2])+": "+v.stderr[:220])
    return v.stdout.strip()
assert git("branch","--show-current")=="research/fresh30-admission-20261024"
assert not git("diff","--name-only") and not git("diff","--cached","--name-only")
def stage_commit(message,paths):
    git("add","--",*[str(p.relative_to(REPO)) for p in paths])
    if git("diff","--cached","--name-only"):
        git("-c","user.name=ChatGPT research automation","-c","user.email=chatgpt-automation@users.noreply.github.com",
            "commit","-m",message)
        git("push","origin","research/fresh30-admission-20261024")
def cache_sync(reason):
    stage_commit("Pangram 4.1 targeted A/B paid-task "+reason,[R/"PANGRAM-BASELINE-CACHE"])
key_file=os.environ.get("PANGRAM_KEY_FILE")
if not key_file:raise RuntimeError("PANGRAM_KEY_FILE is required; no embedded credential")
key=Path(key_file).read_text(encoding="utf-8").strip()
if key.startswith("PANGRAM_API_KEY="):key=key.split("=",1)[1].strip().strip('"').strip("'")
if not key or "\n" in key:raise RuntimeError("Ambiguous credential format")
P=PangramClient(api_key=key,model=MODEL,expected_version=VERSION,sync=cache_sync)
P.probe_auth()
outpath=R/MEASUREMENTS
if outpath.exists():
    out=json.loads(outpath.read_text())
    assert out["schema"]=="pangram4.1-targeted-arm-results-v1" and out["source_prediction"]=="ARM-DETECTOR-PREDICTIONS.json"
    readings=out["readings"]
else:
    readings=[]
for f in F["predictions"]:
    case,arm=f["case"],f["arm"]
    if any(r["case"]==case and r["arm"]==arm for r in readings):
        print("REUSE_ALREADY_RECORDED",case,arm,flush=True)
        continue
    rr=json.loads((R/"PILOT-RESTRICTED-RESULTS"/case/("arm_"+arm+".json")).read_text())
    text=rr["result"]
    sha=hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert sha==f["sha256"] and "\n" not in text.strip()
    measurement="fresh30-restricted-"+case+"-"+arm+"-20261025"
    rec=C.lookup(MODEL,VERSION,text,measurement)
    print(("REUSE_CACHE" if rec else "NEW_FROZEN_POST"),case,arm,sha[:16],flush=True)
    got=P.detect_cached(text,C,measurement)
    assert got["stage"]=="STAGE_SUCCESS" and got["version"]==VERSION and got["text"]==text
    windows=got.get("windows") or []
    assert windows
    is_human=(got.get("headline")=="Human Written" and all(w.get("label")=="Human Written" for w in windows))
    saved=C.lookup(MODEL,VERSION,text,measurement)
    readings.append({"case":case,"arm":arm,"text_sha256":sha,
       "frozen_forecast_p_all_human":f["p_all_human"],"forecast":f["predicted"],
       "stage":got["stage"],"version":got["version"],"headline":got["headline"],
       "categorical_all_Human":is_human,"fraction_human":got.get("fraction_human"),
       "fraction_ai":got.get("fraction_ai"),
       "fraction_ai_assisted":got.get("fraction_ai_assisted"),
       "windows":[{"label":w.get("label"),"confidence":w.get("confidence")} for w in windows],
       "paid_task_reuse":saved.get("source")!="live",
       "task_record_id_present":bool(saved.get("task_id"))})
    out={"schema":"pangram4.1-targeted-arm-results-v1",
      "source_prediction":"ARM-DETECTOR-PREDICTIONS.json",
      "readings":readings,
      "existing_baseline_controls":{"T16":"AI Generated/High Pangram 4.1",
       "T26":"AI Generated/High Pangram 4.1, A byte-identical with baseline — no repeat"},
      "actual_version":"4.1",
      "one_paragraph_per_new_call":True,
      "max_new_paid_tasks":3,
      "new_post_count":sum(1 for x in readings if not x["paid_task_reuse"]),
      "source_gold_preserved":True,
      "owner_style_approval":False,
      "scope":"Two AI-starting families only; cannot infer general transfer from local scores."}
    outpath.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    stage_commit("Record immutable Pangram 4.1 "+case+" "+arm+" result",[outpath])
    print("RESULT",case,arm,got["headline"],"all_Human",is_human,flush=True)
print("COMPLETE",len(readings),"Human",sum(x["categorical_all_Human"] for x in readings),
      "AI/mixed",sum(not x["categorical_all_Human"] for x in readings),flush=True)
