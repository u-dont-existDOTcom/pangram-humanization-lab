from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


class AssemblyError(RuntimeError):
    """Raised when an assembly operation cannot be applied unambiguously."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _byte_len(text: str) -> int:
    return len(text.encode("utf-8"))


def _require_once(text: str, needle: str, label: str) -> int:
    count = text.count(needle)
    if count != 1:
        raise AssemblyError(f"{label} must occur exactly once; found {count}")
    return text.index(needle)


def _replacement_text(root: Path, operation: dict[str, Any]) -> str:
    rel = operation.get("replacement_file")
    if not isinstance(rel, str) or not rel:
        raise AssemblyError(f"operation {operation.get('id', '<unknown>')} requires replacement_file")
    path = root / rel
    if not path.is_file():
        raise AssemblyError(f"replacement file does not exist: {rel}")
    return path.read_text(encoding="utf-8")


def _record(operation: dict[str, Any], old: str, new: str) -> dict[str, Any]:
    return {
        "id": operation["id"],
        "type": operation["type"],
        "old_sha256": sha256_text(old),
        "new_sha256": sha256_text(new),
        "old_bytes": _byte_len(old),
        "new_bytes": _byte_len(new),
    }


def apply_operations(
    text: str,
    operations: list[dict[str, Any]],
    root: Path,
) -> tuple[str, list[dict[str, Any]]]:
    current = text
    records: list[dict[str, Any]] = []

    for operation in operations:
        op_id = operation.get("id")
        op_type = operation.get("type")
        if not isinstance(op_id, str) or not op_id:
            raise AssemblyError("every operation requires a non-empty id")
        if not isinstance(op_type, str) or not op_type:
            raise AssemblyError(f"operation {op_id} requires a type")

        if op_type == "replace_exact":
            old = operation.get("old")
            if not isinstance(old, str) or not old:
                raise AssemblyError(f"operation {op_id} requires non-empty old text")
            _require_once(current, old, f"operation {op_id} old text")
            new = _replacement_text(root, operation)
            current = current.replace(old, new, 1)

        elif op_type == "delete_exact":
            old = operation.get("old")
            if not isinstance(old, str) or not old:
                raise AssemblyError(f"operation {op_id} requires non-empty old text")
            _require_once(current, old, f"operation {op_id} old text")
            new = ""
            current = current.replace(old, new, 1)

        elif op_type == "replace_between":
            start = operation.get("start_anchor")
            end = operation.get("end_anchor")
            if not isinstance(start, str) or not start or not isinstance(end, str) or not end:
                raise AssemblyError(f"operation {op_id} requires non-empty start_anchor and end_anchor")
            start_at = _require_once(current, start, f"operation {op_id} start anchor")
            end_at = _require_once(current, end, f"operation {op_id} end anchor")
            interior_start = start_at + len(start)
            if end_at < interior_start:
                raise AssemblyError(f"operation {op_id} end anchor precedes start anchor")
            old = current[interior_start:end_at]
            new = _replacement_text(root, operation)
            current = current[:interior_start] + new + current[end_at:]

        elif op_type == "replace_section":
            start = operation.get("start_anchor")
            end = operation.get("end_anchor")
            if not isinstance(start, str) or not start or not isinstance(end, str) or not end:
                raise AssemblyError(f"operation {op_id} requires non-empty start_anchor and end_anchor")
            start_at = _require_once(current, start, f"operation {op_id} start anchor")
            end_at = _require_once(current, end, f"operation {op_id} end anchor")
            if end_at <= start_at:
                raise AssemblyError(f"operation {op_id} end anchor must follow start anchor")
            old = current[start_at:end_at]
            new = _replacement_text(root, operation)
            current = current[:start_at] + new + current[end_at:]

        else:
            raise AssemblyError(f"unsupported operation type for {op_id}: {op_type}")

        records.append(_record(operation, old, new))

    return current, records
