from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
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


def _load_spec(path: Path) -> tuple[str, dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssemblyError(f"invalid assembly spec JSON: {exc}") from exc
    if spec.get("schema_version") != 1:
        raise AssemblyError("assembly spec schema_version must be 1")
    operations = spec.get("operations")
    if not isinstance(operations, list):
        raise AssemblyError("assembly spec operations must be a list")
    return raw, spec


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _materialize(
    baseline_path: Path,
    spec_path: Path,
    output_path: Path,
    manifest_path: Path,
    diff_path: Path,
) -> dict[str, Any]:
    baseline = baseline_path.read_text(encoding="utf-8")
    spec_raw, spec = _load_spec(spec_path)
    final, records = apply_operations(baseline, spec["operations"], spec_path.parent)

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "baseline_sha256": sha256_text(baseline),
        "final_sha256": sha256_text(final),
        "spec_sha256": sha256_text(spec_raw),
        "baseline_bytes": _byte_len(baseline),
        "final_bytes": _byte_len(final),
        "operation_count": len(records),
        "operations": records,
    }
    for key in ("article", "baseline"):
        if key in spec:
            manifest[key] = spec[key]

    diff_text = "".join(
        difflib.unified_diff(
            baseline.splitlines(keepends=True),
            final.splitlines(keepends=True),
            fromfile=str(baseline_path),
            tofile=str(output_path),
        )
    )

    _write_text(output_path, final)
    _write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    _write_text(diff_path, diff_text)
    return manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministically assemble the current Romance master.")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--diff", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = _materialize(args.baseline, args.spec, args.output, args.manifest, args.diff)
    except (AssemblyError, OSError) as exc:
        print(f"assembly failed: {exc}", file=sys.stderr)
        return 2
    print(f"final_sha256={manifest['final_sha256']}")
    print(f"final_bytes={manifest['final_bytes']}")
    print(f"operations={manifest['operation_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
