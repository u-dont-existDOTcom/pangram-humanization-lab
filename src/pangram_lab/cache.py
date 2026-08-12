from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_measurement_key(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in value)[:180]


def _atomic_write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class PangramCache:
    """Content-addressed durable Pangram cache.

    The base measurement is reusable by model/version/text hash. Exact repeats use
    deterministic measurement keys so an interrupted repeat resumes instead of
    silently becoming another paid call.
    """

    def __init__(self, root: Path):
        self.root = Path(root)

    def path_for(self, model: str, version: str, text: str, measurement_key: str = "base") -> Path:
        h = text_sha256(text)
        return self.root / model / version / h / f"{_safe_measurement_key(measurement_key)}.json"

    def lookup(self, model: str, version: str, text: str, measurement_key: str = "base") -> dict | None:
        path = self.path_for(model, version, text, measurement_key)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_pending(self, model: str, version: str, text: str, measurement_key: str, task_id: str, *, source: str = "live") -> Path:
        path = self.path_for(model, version, text, measurement_key)
        old = self.lookup(model, version, text, measurement_key) or {}
        value = {
            "format": "pangram-cache-v2",
            "model": model,
            "expected_version": version,
            "text_sha256": text_sha256(text),
            "text": text,
            "measurement_key": measurement_key,
            "status": "pending",
            "task_id": task_id,
            "source": source,
            "created_utc": old.get("created_utc") or utc_now(),
            "updated_utc": utc_now(),
            "result": old.get("result"),
            "last_error": "",
        }
        _atomic_write_json(path, value)
        return path

    def save_success(self, model: str, version: str, text: str, measurement_key: str, task_id: str, result: dict, *, source: str = "live") -> Path:
        path = self.path_for(model, version, text, measurement_key)
        old = self.lookup(model, version, text, measurement_key) or {}
        value = {
            "format": "pangram-cache-v2",
            "model": model,
            "expected_version": version,
            "text_sha256": text_sha256(text),
            "text": text,
            "measurement_key": measurement_key,
            "status": "success",
            "task_id": task_id,
            "source": source,
            "created_utc": old.get("created_utc") or utc_now(),
            "updated_utc": utc_now(),
            "result": result,
            "last_error": "",
        }
        _atomic_write_json(path, value)
        return path


    def save_submit_ambiguous(self, model: str, version: str, text: str, measurement_key: str, *, error: str, source: str = "live") -> Path:
        path = self.path_for(model, version, text, measurement_key)
        old = self.lookup(model, version, text, measurement_key) or {}
        value = {
            "format": "pangram-cache-v2", "model": model, "expected_version": version,
            "text_sha256": text_sha256(text), "text": text, "measurement_key": measurement_key,
            "status": "submit_ambiguous", "task_id": "", "source": source,
            "created_utc": old.get("created_utc") or utc_now(), "updated_utc": utc_now(),
            "result": old.get("result"), "last_error": error,
        }
        _atomic_write_json(path, value)
        return path

    def save_failure(self, model: str, version: str, text: str, measurement_key: str, *, task_id: str = "", error: str, source: str = "live") -> Path:
        path = self.path_for(model, version, text, measurement_key)
        old = self.lookup(model, version, text, measurement_key) or {}
        value = {
            "format": "pangram-cache-v2",
            "model": model,
            "expected_version": version,
            "text_sha256": text_sha256(text),
            "text": text,
            "measurement_key": measurement_key,
            "status": "failed",
            "task_id": task_id or old.get("task_id", ""),
            "source": source,
            "created_utc": old.get("created_utc") or utc_now(),
            "updated_utc": utc_now(),
            "result": old.get("result"),
            "last_error": error,
        }
        _atomic_write_json(path, value)
        return path
