from __future__ import annotations


def score(result: dict) -> float:
    try: return float(result.get("fraction_ai",0)) + 0.5*float(result.get("fraction_ai_assisted",0))
    except Exception: return 1.0


def hclass(result: dict) -> str:
    short=str(result.get("prediction_short") or "").lower()
    head=str(result.get("headline") or "").lower()
    if "human" in short and "ai" not in short: return "Human"
    if "human written" in head: return "Human"
    if "mixed" in short or "mixed" in head or float(result.get("fraction_ai_assisted") or 0)>0: return "Mixed"
    return "AI"


def contrast_stats(plan: dict, results: dict) -> list[dict]:
    out=[]
    for c in plan.get("contrasts") or []:
        a=results.get(c["left_probe"]); b=results.get(c["right_probe"])
        if not a or not b: continue
        out.append({**c,"left_score":score(a),"right_score":score(b),"delta":score(b)-score(a),"left_class":hclass(a),"right_class":hclass(b),"headline_flip":hclass(a)!=hclass(b)})
    return out


def factorial_effects(plan: dict, results: dict) -> dict:
    factors=[f["id"] for f in plan.get("factors") or []]
    probes=[]
    for p in plan.get("probes") or []:
        if p["id"] not in results: continue
        assn={a["factor_id"]:a["level"] for a in p.get("assignments") or []}
        if set(assn)==set(factors): probes.append((p,assn,score(results[p["id"]])))
    effects={}
    for fid in factors:
        zero=[s for _,a,s in probes if a[fid]==0]; one=[s for _,a,s in probes if a[fid]==1]
        if zero and one: effects[fid]=sum(one)/len(one)-sum(zero)/len(zero)
    interactions={}
    # Difference-in-differences, averaged over every observed configuration of
    # the remaining factors. This keeps interaction arithmetic deterministic
    # instead of asking Codex to encode formulas as fake contrast IDs.
    for i,a_id in enumerate(factors):
        for b_id in factors[i+1:]:
            others=[f for f in factors if f not in {a_id,b_id}]
            buckets={}
            for _,assn,val in probes:
                key=tuple((f,assn[f]) for f in others)
                buckets.setdefault(key,{})[(assn[a_id],assn[b_id])]=val
            did=[]
            for cells in buckets.values():
                if all(k in cells for k in ((0,0),(1,0),(0,1),(1,1))):
                    did.append(cells[(1,1)]-cells[(1,0)]-cells[(0,1)]+cells[(0,0)])
            if did:
                interactions[f"{a_id}×{b_id}"]=sum(did)/len(did)
    return {"factor_ids":factors,"main_effects":effects,"pairwise_interactions":interactions,"complete_cell_count":len(probes)}
