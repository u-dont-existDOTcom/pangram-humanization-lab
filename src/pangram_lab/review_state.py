from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ReviewStateMismatch(RuntimeError):
    pass


class ReviewState:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.path = self.root / "state" / "LESSON-INBOX.json"
        self.state = self._load()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _id(source_path: str, source_ref: str, source_sha256: str) -> str:
        raw = f"{source_ref}\0{source_path}\0{source_sha256}".encode("utf-8")
        return "Q-" + hashlib.sha256(raw).hexdigest()[:16]

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"format": "lesson-review-v1", "entries": []}
        obj = json.loads(self.path.read_text(encoding="utf-8"))
        if obj.get("format") != "lesson-review-v1" or not isinstance(obj.get("entries"), list):
            raise ValueError("invalid review state")
        return obj

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)

    def register(self, source_path: str, source_ref: str, source_sha256: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        entry_id = self._id(source_path, source_ref, source_sha256)
        for entry in self.state["entries"]:
            if entry.get("id") == entry_id:
                return entry
        metadata = dict(metadata or {})
        if {"text", "source_text", "source_body", "article", "content"}.intersection(metadata):
            raise ValueError("review metadata may not include source content")
        entry = {"id": entry_id, "source_path": source_path, "source_ref": source_ref, "source_sha256": source_sha256, "status": "pending", "created_at_utc": self._now(), **metadata}
        self.state["entries"].append(entry)
        self._persist()
        return entry

    def pending(self) -> list[dict[str, Any]]:
        return [entry for entry in self.state["entries"] if entry.get("status") == "pending"]

    def resolve(self, source_path: str, source_ref: str, source_sha256: str, *, ledger_entry_ids: list[str]) -> dict[str, Any]:
        exact = None
        same_path_ref = []
        for entry in self.state["entries"]:
            if entry.get("source_path") == source_path and entry.get("source_ref") == source_ref:
                same_path_ref.append(entry)
                if entry.get("source_sha256") == source_sha256:
                    exact = entry
        if exact is None:
            if same_path_ref:
                raise ReviewStateMismatch("source path/ref is registered with a different hash")
            raise ReviewStateMismatch("source artifact is not registered")
        exact["status"] = "resolved"
        exact["ledger_entry_ids"] = list(ledger_entry_ids)
        exact["resolved_at_utc"] = self._now()
        self._persist()
        return exact
