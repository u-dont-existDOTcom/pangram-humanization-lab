from __future__ import annotations

import hashlib
import json
from pathlib import Path
from .cache import PangramCache


def _sha(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _save_result(cache: PangramCache, result: dict, text: str, *, source: str) -> bool:
    version=str(result.get("version") or result.get("api_version") or "")
    if version != "4.0" or result.get("dry_run") is True:
        return False
    task_id=str(result.get("task_id") or "imported")
    if str(result.get("stage") or "STAGE_SUCCESS") != "STAGE_SUCCESS":
        return False
    existing=cache.lookup("pangram-4","4.0",text,"base")
    if existing and existing.get("status") == "success":
        return False
    cache.save_success("pangram-4","4.0",text,"base",task_id,result,source=source)
    return True


def import_legacy_tree(root: Path, cache: PangramCache) -> dict:
    root=Path(root)
    report={"source":str(root),"v4_success_imported":0,"v3_records_seen":0,"pending_imported":0,"files_scanned":0}
    if not root.exists(): return report
    # Newer standalone harness state files.
    for state_path in root.rglob("state.json"):
        report["files_scanned"] += 1
        try: data=json.loads(state_path.read_text(encoding="utf-8"))
        except Exception: continue
        if (data.get("config") or {}).get("dry_run") is True or "_dry" in state_path.parts: continue
        model=(data.get("config") or {}).get("pangram_model","pangram-4")
        version=(data.get("config") or {}).get("expected_pangram_version","4.0")
        if model != "pangram-4" or version != "4.0": continue
        for item in (data.get("results") or {}).values():
            if not isinstance(item,dict): continue
            text=item.get("text")
            result=item.get("pangram")
            if isinstance(text,str) and isinstance(result,dict) and _save_result(cache,result,text,source=f"legacy:{state_path}"):
                report["v4_success_imported"] += 1
        for task in (data.get("pangram_tasks") or {}).values():
            if not isinstance(task,dict) or task.get("status") != "pending": continue
            # Pending tasks without text cannot be safely imported from this table alone.
    # Old autonomous campaign states. Resolve raw response files to preserve exact text.
    for state_path in root.rglob("campaign-state.json"):
        report["files_scanned"] += 1
        try: data=json.loads(state_path.read_text(encoding="utf-8"))
        except Exception: continue
        for m in (data.get("measurements") or {}).values():
            if not isinstance(m,dict): continue
            res=m.get("result") or {}
            version=str(res.get("api_version") or "")
            if version and version != "4.0":
                report["v3_records_seen"] += 1; continue
            raw_ref=res.get("raw_response_file")
            candidates=[]
            if raw_ref:
                candidates += [state_path.parent/raw_ref, state_path.parent/"raw"/Path(raw_ref).name]
            raw_obj=None
            for p in candidates:
                if p.is_file():
                    try: raw_obj=json.loads(p.read_text(encoding="utf-8")); break
                    except Exception: pass
            if isinstance(raw_obj,dict) and isinstance(raw_obj.get("text"),str) and _save_result(cache,raw_obj,raw_obj["text"],source=f"legacy:{state_path}"):
                report["v4_success_imported"] += 1
    # Generic v4 raw-response recovery catches handoff/calibration folders.
    for p in root.rglob("*.json"):
        if p.name in {"state.json","campaign-state.json"}: continue
        try:
            obj=json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        if isinstance(obj,dict) and str(obj.get("version") or "") == "4.0" and isinstance(obj.get("text"),str):
            before=cache.lookup("pangram-4","4.0",obj["text"],"base")
            if before is None and _save_result(cache,obj,obj["text"],source=f"legacy-raw:{p}"):
                report["v4_success_imported"] += 1
    return report
