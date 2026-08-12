from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .plan import validate_plan
from .stats import contrast_stats, factorial_effects


def atomic_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


@dataclass
class Engine:
    root: Path
    codex: object
    pangram: object
    cache: object
    git: object
    max_rounds: int = 6
    max_calls: int = 64

    def _case_dir(self, ai: str, human: str):
        import hashlib
        cid=hashlib.sha256((ai+"\0"+human).encode()).hexdigest()[:20]
        p=self.root/"cases"/cid; p.mkdir(parents=True,exist_ok=True)
        (p/"AI_ENDPOINT.txt").write_text(ai,encoding="utf-8"); (p/"HUMAN_ENDPOINT.txt").write_text(human,encoding="utf-8")
        return p

    def _prompt(self, role, ai, human, prior, payload=None):
        base=(self.root/"prompts"/f"{role}.md").read_text(encoding="utf-8")
        lessons=[]
        for lp in (self.root/"state/WORKING-LESSONS.md", self.root/"legacy/WORKING-LESSONS.md", self.root/"legacy/CONTROLLED-TEST-LEDGER.md"):
            if lp.is_file():
                lessons.append(f"## {lp.name}\n" + lp.read_text(encoding="utf-8"))
        context={"AI_ENDPOINT":ai,"HUMAN_ENDPOINT":human,"prior_round_records":prior}
        if payload is not None: context["payload"]=payload
        return base+"\n\n# Accumulated research constraints/lessons\n"+"\n\n".join(lessons)+"\n\n# Frozen case context\n"+json.dumps(context,ensure_ascii=False,indent=2)

    def _codex_call(self, role: str, prompt: str, schema: Path, out: Path, log: Path, rdir: Path):
        try:
            return self.codex.run_json(role,prompt,schema,out,log)
        except Exception as exc:
            atomic_json(rdir/"failure.json",{"stage":f"codex_{role}","error":str(exc),"log":str(log)})
            self.git.sync(f"{rdir.name} {role} failure")
            raise

    def _design_valid_plan(self, ai: str, human: str, prior: list, rdir: Path, max_attempts: int = 3) -> dict:
        repair_note = ""
        last_exc = None
        for attempt in range(1, max_attempts + 1):
            tag=f"attempt{attempt:02d}"
            print(f"[plan] designer {tag}/{max_attempts}", flush=True)
            prompt=self._prompt("designer",ai,human,prior)
            if repair_note:
                prompt += "\n\n# MACHINE VALIDATION REPAIR\n" + repair_note + "\nReturn a corrected plan only; do not change the experiment's substantive objective merely to satisfy syntax."
            out=rdir/f"plan-{tag}.json"; log=rdir/f"designer-{tag}.log"
            plan=self._codex_call("designer",prompt,self.root/"schemas/plan.schema.json",out,log,rdir)
            atomic_json(out,plan)
            self.git.sync(f"{rdir.name} designer raw output {tag}")
            try:
                validate_plan(plan,ai,human)
            except Exception as exc:
                last_exc=exc
                atomic_json(rdir/f"plan-validation-{tag}.json",{"attempt":attempt,"error":str(exc),"plan":plan})
                self.git.sync(f"{rdir.name} plan validation failure {tag}")
                print(f"[plan] REJECTED locally: {exc}", flush=True)
                repair_note=(
                    f"The previous plan failed deterministic validation with: {exc}. "
                    "Use factor assignments, not factor_bits. Every contrast left_probe/right_probe must be one literal ID present in probes; "
                    "do not put H000 annotations, means, arithmetic, or interaction formulas in those fields. "
                    "AI_ENDPOINT and HUMAN_ENDPOINT are literal exact-text probe IDs."
                )
                continue
            atomic_json(rdir/"plan.json",plan)
            self.git.sync(f"{rdir.name} preregistered valid plan")
            if attempt > 1:
                print(f"[plan] repaired successfully on {tag}", flush=True)
            return plan
        atomic_json(rdir/"failure.json",{"stage":"plan_validation","error":str(last_exc),"attempts":max_attempts})
        self.git.sync(f"{rdir.name} plan validation exhausted")
        raise ValueError(f"Experiment plan remained invalid after {max_attempts} Codex repair attempts: {last_exc}")

    def run(self, ai: str, human: str) -> dict:
        case=self._case_dir(ai,human); self.git.sync("freeze case endpoints")
        history_path=case/"history.json"
        prior=[]
        if history_path.is_file():
            try:
                loaded=json.loads(history_path.read_text(encoding="utf-8"))
                if isinstance(loaded.get("rounds"),list): prior=loaded["rounds"]
            except Exception:
                prior=[]
        completed={str(r.get("round_id") or "") for r in prior if isinstance(r,dict)}
        if prior:
            last=prior[-1].get("analysis") or {}
            if last.get("next_action") in {"stop","needs_owner_input"}:
                print(f"[resume] case already reached {last.get('next_action')} in {prior[-1].get('round_id')}; no Codex or Pangram rerun",flush=True)
                return {"status":"stopped" if last.get("next_action")=="stop" else "owner_input_required","reason":last.get("stop_reason","") or last.get("summary",""),"question":last.get("owner_question",""),"case_dir":str(case)}
        new_submissions=0
        for n in range(1,self.max_rounds+1):
            rid=f"r{n:02d}"; rdir=case/rid; rdir.mkdir(parents=True,exist_ok=True)
            if rid in completed:
                print(f"[resume] SKIP completed {rid}; history and detector evidence already frozen",flush=True)
                continue
            print(f"\n=== {rid}: DESIGN ===",flush=True)
            plan_path=rdir/"plan.json"
            if plan_path.is_file():
                plan=json.loads(plan_path.read_text(encoding="utf-8"))
                validate_plan(plan,ai,human)
                print(f"[resume] using frozen valid plan from {plan_path}",flush=True)
            else:
                plan=self._design_valid_plan(ai,human,prior,rdir)
            print(f"[plan] {plan.get('status')} — {plan.get('summary','')} | factors={len(plan.get('factors') or [])} probes={len(plan.get('probes') or [])} contrasts={len(plan.get('contrasts') or [])}",flush=True)
            if plan["status"]=="stop": return {"status":"stopped","reason":plan.get("summary","designer stop"),"case_dir":str(case)}
            if plan["status"]=="needs_owner_input": return {"status":"owner_input_required","question":plan.get("owner_question",""),"case_dir":str(case)}
            print(f"\n=== {rid}: BLIND EDITORIAL REVIEW (before new Pangram) ===",flush=True)
            review_path=rdir/"review.json"
            if review_path.is_file():
                review=json.loads(review_path.read_text(encoding="utf-8"))
                print(f"[resume] using frozen blind review from {review_path}",flush=True)
            else:
                review=self._codex_call("reviewer",self._prompt("reviewer",ai,human,prior,plan),self.root/"schemas/review.schema.json",review_path,rdir/"reviewer.log",rdir)
                atomic_json(review_path,review); self.git.sync(f"{rid} blind review freeze")
            print(f"[review] {review.get('status')} — approved={len(review.get('approved_probe_ids') or [])} rejected={len(review.get('rejected') or [])}",flush=True)
            if review.get("status")=="needs_owner_input": return {"status":"owner_input_required","question":review.get("owner_question",""),"case_dir":str(case)}
            approved=set(review.get("approved_probe_ids") or [])
            results={}
            print(f"\n=== {rid}: PANGRAM BASE MEASUREMENTS ===",flush=True)
            for p in plan["probes"]:
                if p["id"] not in approved:
                    print(f"[pangram] SKIP {p['id']} — rejected by blind editorial review",flush=True); continue
                before=self.cache.lookup(self.pangram.model,self.pangram.expected_version,p["text"],"base")
                will_submit=(before is None or before.get("status") == "failed")
                if will_submit and new_submissions >= self.max_calls:
                    raise RuntimeError("max Pangram submission budget exceeded before a new paid POST")
                result=self.pangram.detect_cached(p["text"],self.cache,"base")
                if will_submit: new_submissions += 1
                results[p["id"]]=result
                atomic_json(rdir/"results.json",results); self.git.sync(f"{rid} result {p['id']}")
            contrasts=contrast_stats(plan,results); repeats={}
            triggered=set()
            threshold=float(plan.get("repeat_threshold",0.03))
            for c in contrasts:
                if c.get("repeat_eligible") and (abs(c["delta"])>=threshold or c["headline_flip"]):
                    triggered.add(c["left_probe"]); triggered.add(c["right_probe"])
            if triggered:
                print(f"\n=== {rid}: EXACT REPEATS ({', '.join(sorted(triggered))}) ===",flush=True)
            probe_map={p["id"]:p for p in plan["probes"]}
            for pid in sorted(triggered):
                p=probe_map[pid]; key=f"{rid}:{pid}:r2"
                before=self.cache.lookup(self.pangram.model,self.pangram.expected_version,p["text"],key)
                will_submit=(before is None or before.get("status") == "failed")
                if will_submit and new_submissions >= self.max_calls:
                    raise RuntimeError("max Pangram submission budget exceeded before an exact-repeat paid POST")
                repeats[pid]=self.pangram.detect_cached(p["text"],self.cache,key)
                if will_submit: new_submissions+=1
                atomic_json(rdir/"repeats.json",repeats); self.git.sync(f"{rid} exact repeat {pid}")
            stats={"contrasts":contrasts,"factorial":factorial_effects(plan,results),"repeat_threshold":threshold,"new_submissions_so_far":new_submissions}
            atomic_json(rdir/"stats.json",stats); self.git.sync(f"{rid} deterministic stats")
            print(f"\n=== {rid}: CODEX ANALYSIS ===",flush=True)
            analysis=self._codex_call("analyst",self._prompt("analyst",ai,human,prior,{"plan":plan,"review":review,"results":results,"repeats":repeats,"stats":stats}),self.root/"schemas/analysis.schema.json",rdir/"analysis.json",rdir/"analyst.log",rdir)
            atomic_json(rdir/"analysis.json",analysis)
            prior.append({"round_id":rid,"plan_summary":plan.get("summary"),"stats":stats,"analysis":analysis})
            atomic_json(case/"history.json",{"rounds":prior}); self.git.sync(f"{rid} analysis")
            if analysis.get("next_action") in {"stop","needs_owner_input"}:
                return {"status":"stopped" if analysis["next_action"]=="stop" else "owner_input_required","reason":analysis.get("stop_reason",""),"question":analysis.get("owner_question",""),"case_dir":str(case)}
        return {"status":"stopped","reason":f"max rounds {self.max_rounds} reached","case_dir":str(case)}
