#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from pangram_lab.fixed_batch import load_spec
from pangram_lab.result_paths import resolve_result_path


PAID_RUN_CONFIRMATION = "RUN_PAID_PANGRAM_FIXED_BATCH"
_SAFE_REPOSITORY_PATH = re.compile(r"^[A-Za-z0-9._/-]+$")


class DispatchValidationError(ValueError):
    pass


def _repository_path(root: Path, raw: str, *, label: str) -> tuple[Path, Path]:
    if not isinstance(raw, str) or not raw:
        raise DispatchValidationError(f"{label} is required")
    if raw != raw.strip():
        raise DispatchValidationError(f"{label} must not contain leading or trailing whitespace")
    if not _SAFE_REPOSITORY_PATH.fullmatch(raw):
        raise DispatchValidationError(
            f"{label} must use only letters, numbers, dot, underscore, slash, or hyphen"
        )
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts:
        raise DispatchValidationError(f"{label} must be a repository-relative path")
    root = root.resolve()
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise DispatchValidationError(f"{label} escapes the repository root") from exc
    return relative, resolved


def validate_dispatch(
    root: Path | str,
    *,
    spec_raw: str,
    output_raw: str,
    confirmation: str,
) -> dict[str, Any]:
    root = Path(root).resolve()
    if confirmation != PAID_RUN_CONFIRMATION:
        raise DispatchValidationError(
            f"paid-run confirmation must equal {PAID_RUN_CONFIRMATION}"
        )

    spec_relative, spec_path = _repository_path(root, spec_raw, label="spec path")
    if not spec_relative.parts or spec_relative.parts[0] != "experiments":
        raise DispatchValidationError("spec path must stay under experiments/")
    if spec_relative.suffix.lower() != ".json" or not spec_path.is_file():
        raise DispatchValidationError("spec path must name an existing JSON file")

    try:
        spec = load_spec(spec_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise DispatchValidationError(f"invalid fixed-batch spec: {exc}") from exc

    audit_id = str(spec.get("audit_id") or "").strip()
    if not audit_id:
        raise DispatchValidationError("audit_id is required for a paid workflow dispatch")
    variants = spec.get("variants")
    if not isinstance(variants, list) or not variants:
        raise DispatchValidationError("at least one variant is required")
    for variant in variants:
        if not isinstance(variant, dict) or not str(variant.get("section_id") or "").strip():
            raise DispatchValidationError(
                "every paid workflow variant requires a non-empty section_id"
            )

    requested: Path | None = None
    if output_raw:
        output_relative, _ = _repository_path(root, output_raw, label="result path")
        requested = output_relative
    try:
        result_path = resolve_result_path(root, spec, requested)
    except ValueError as exc:
        raise DispatchValidationError(f"canonical output path validation failed: {exc}") from exc
    try:
        result_relative = result_path.relative_to(root)
    except ValueError as exc:
        raise DispatchValidationError("canonical result path escapes the repository root") from exc

    return {
        "spec_path": spec_relative.as_posix(),
        "result_path": result_relative.as_posix(),
        "experiment_id": spec["experiment_id"],
        "audit_id": audit_id,
        "variant_count": len(variants),
    }


def _write_github_output(path: Path, result: dict[str, Any]) -> None:
    lines = [
        f"spec_path={result['spec_path']}",
        f"result_path={result['result_path']}",
        f"experiment_id={result['experiment_id']}",
        f"audit_id={result['audit_id']}",
        f"variant_count={result['variant_count']}",
    ]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a manual paid Pangram fixed-batch dispatch without detector access"
    )
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out", default="")
    parser.add_argument("--confirmation", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    try:
        result = validate_dispatch(
            root,
            spec_raw=args.spec,
            output_raw=args.out,
            confirmation=args.confirmation,
        )
    except DispatchValidationError as exc:
        parser.error(str(exc))
    if args.github_output is not None:
        _write_github_output(args.github_output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
