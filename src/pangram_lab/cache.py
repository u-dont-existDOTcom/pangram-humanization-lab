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

    Measurements live under model/version/text-hash. A measurement key labels one
    observation inside that content identity; it must not silently turn identical
    text into a new paid request. Callers that deliberately need an independent
    repeat must opt in explicitly at the PangramClient layer.
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

    def records_for_text(self, model: str, version: str, text: str) -> list[dict]:
        """Return every valid cache record for the same model/version/text bytes.

        This is deliberately independent of measurement_key. It is the safety
        primitive that prevents a renamed experiment variant from buying the same
        exact Pangram measurement again by accident.
        """
        directory = self.path_for(model, version, text, "base").parent
        if not directory.is_dir():
            return []
        expected_hash = text_sha256(text)
        records: list[dict] = []
        for path in sorted(directory.glob("*.json")):
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(obj, dict):
                continue
            if obj.get("model") != model or obj.get("expected_version") != version:
                continue
            if obj.get("text_sha256") != expected_hash:
                continue
            records.append(obj)
        return records

    def save_pending(self, model: str, version: str, text: str, measurement_key: str, task_id: str, *, source: str = "live", submitted_model: str = "") -> Path:
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
            "submitted_model": submitted_model or old.get("submitted_model", ""),
            "source": source,
            "created_utc": old.get("created_utc") or utc_now(),
            "updated_utc": utc_now(),
            "result": old.get("result"),
            "last_error": "",
        }
        _atomic_write_json(path, value)
        return path

    def save_success(self, model: str, version: str, text: str, measurement_key: str, task_id: str, result: dict, *, source: str = "live", submitted_model: str = "") -> Path:
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
            "submitted_model": submitted_model or old.get("submitted_model", ""),
            "source": source,
            "created_utc": old.get("created_utc") or utc_now(),
            "updated_utc": utc_now(),
            "result": result,
            "last_error": "",
        }
        _atomic_write_json(path, value)
        return path

    def save_wrong_version(self, model: str, version: str, text: str, measurement_key: str, task_id: str, result: dict, *, submitted_model: str = "", source: str = "live") -> Path:
        old = self.lookup(model, version, text, measurement_key) or {}
        value = {
            "format": "pangram-cache-v2",
            "model": model,
            "expected_version": version,
            "text_sha256": text_sha256(text),
            "text": text,
            "measurement_key": measurement_key,
            "status": "terminal_wrong_version",
            "task_id": task_id,
            "submitted_model": submitted_model or old.get("submitted_model", ""),
            "source": source,
            "created_utc": old.get("created_utc") or utc_now(),
            "updated_utc": utc_now(),
            "result": result,
            "last_error": f"terminal version {result.get('version')!r} did not match expected {version!r}",
        }
        # Preserve the incompatible terminal response under its own measurement key
        # before the canonical measurement is replaced by a corrected submission.
        archive_key = f"{measurement_key}.wrong-version.{task_id}"
        archive_path = self.path_for(model, version, text, archive_key)
        archive_value = dict(value)
        archive_value["measurement_key"] = archive_key
        _atomic_write_json(archive_path, archive_value)
        _atomic_write_json(self.path_for(model, version, text, measurement_key), value)
        return archive_path

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
