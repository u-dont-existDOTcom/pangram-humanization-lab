from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .lesson_closeout import _git_bytes, record_finding


class CloseoutRequestError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_once(path: Path, marker: str, block: str) -> None:
    current = path.read_text(encoding="utf-8")
    if marker in current:
        return
    addition = f"\n{marker}\n{block.rstrip()}\n"
    path.write_text(current.rstrip() + addition, encoding="utf-8")


def _load_request(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("schema_version") != 1:
        raise CloseoutRequestError("request schema_version must be 1")
    required = ["request_id", "source_path", "source_ref", "source_sha256", "finding", "disposition"]
    for field in required:
        if not isinstance(obj.get(field), str) or not obj[field].strip():
            raise CloseoutRequestError(f"request field {field} is required")
    return obj


def process_request(repo: Path | str, request_path: Path | str) -> dict[str, Any]:
    repo = Path(repo).resolve()
    request_path = Path(request_path)
    if not request_path.is_absolute():
        request_path = repo / request_path
    request = _load_request(request_path)
    if request.get("status") == "processed" and request.get("ledger_entry_ids"):
        ledger = json.loads((repo / "state" / "LESSON-LEDGER.json").read_text(encoding="utf-8"))
        wanted = request["ledger_entry_ids"][0]
        for entry in ledger.get("entries", []):
            if entry.get("id") == wanted:
                return entry
        raise CloseoutRequestError("processed request references a missing ledger entry")

    source_bytes = _git_bytes(repo, request["source_ref"], request["source_path"])
    actual_sha = hashlib.sha256(source_bytes).hexdigest()
    if actual_sha != request["source_sha256"].lower():
        raise CloseoutRequestError(f"source hash mismatch: request={request['source_sha256']} actual={actual_sha}")

    disposition = request["disposition"]
    promoted_to = list(request.get("promoted_to") or [])
    reason = str(request.get("reason") or "")

    if disposition == "promoted":
        summary_target = str(request.get("summary_target") or "")
        lesson_block = str(request.get("lesson_block") or "")
        index_block = str(request.get("index_block") or "")
        if not summary_target or summary_target not in promoted_to:
            raise CloseoutRequestError("promoted request requires summary_target in promoted_to")
        if "state/LESSON-INDEX.md" not in promoted_to:
            raise CloseoutRequestError("promoted request must target state/LESSON-INDEX.md")
        if not lesson_block.strip() or not index_block.strip():
            raise CloseoutRequestError("promoted request requires explicit lesson_block and index_block")
        marker = f"<!-- closeout-request:{request['request_id']} -->"
        _append_once(repo / summary_target, marker, lesson_block)
        _append_once(repo / "state" / "LESSON-INDEX.md", marker, index_block)

    entry = record_finding(
        repo,
        source=request["source_path"],
        finding=request["finding"],
        disposition=disposition,
        reason=reason,
        promoted_to=promoted_to,
        source_ref=request["source_ref"],
    )
    if entry["source_sha256"] != actual_sha:
        raise CloseoutRequestError("recorded ledger hash does not match verified request hash")

    request["status"] = "processed"
    request["processed_at_utc"] = _now()
    request["ledger_entry_ids"] = [entry["id"]]
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return entry
