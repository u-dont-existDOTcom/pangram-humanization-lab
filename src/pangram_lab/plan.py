from __future__ import annotations


def validate_plan(plan: dict, ai_text: str, human_text: str) -> None:
    status=plan.get("status")
    if status not in {"planned","stop","needs_owner_input"}:
        raise ValueError(f"Invalid experiment plan status: {status!r}")
    if status != "planned":
        return
    probes=plan.get("probes") or []
    if not 2 <= len(probes) <= 16:
        raise ValueError("planned experiment must contain 2-16 probes")
    ids=[str(p.get("id") or "") for p in probes]
    if len(set(ids)) != len(ids) or any(not x for x in ids):
        raise ValueError("probe ids must be non-empty and unique")
    by_id={p["id"]:p for p in probes}
    if "AI_ENDPOINT" not in by_id or by_id["AI_ENDPOINT"].get("text") != ai_text:
        raise ValueError("AI_ENDPOINT must be present with the exact AI endpoint text")
    if "HUMAN_ENDPOINT" not in by_id or by_id["HUMAN_ENDPOINT"].get("text") != human_text:
        raise ValueError("HUMAN_ENDPOINT must be present with the exact Human endpoint text")
    factors={str(f.get("id") or "") for f in (plan.get("factors") or [])}
    for probe in probes:
        seen=set()
        for assn in probe.get("assignments") or []:
            fid=str(assn.get("factor_id") or "")
            if fid not in factors:
                raise ValueError(f"probe {probe['id']} references unknown factor {fid!r}")
            if fid in seen:
                raise ValueError(f"probe {probe['id']} repeats factor assignment {fid!r}")
            if assn.get("level") not in {0,1}:
                raise ValueError(f"probe {probe['id']} factor {fid!r} level must be 0 or 1")
            seen.add(fid)
    for contrast in plan.get("contrasts") or []:
        for field in ("left_probe","right_probe"):
            ref=str(contrast.get(field) or "")
            if ref not in by_id:
                raise ValueError(f"contrast references unknown probe: {ref!r}")
    threshold=plan.get("repeat_threshold")
    if not isinstance(threshold,(int,float)) or not (0 <= float(threshold) <= 1):
        raise ValueError("repeat_threshold must be between 0 and 1")
