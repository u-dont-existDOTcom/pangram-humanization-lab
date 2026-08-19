#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

FORMAT = "pangram-private-executor-request-v1"
CONFIRMATION = "RUN_PAID_PANGRAM_FIXED_BATCH"
PUBLIC_REPO = "u-dont-existDOTcom/pangram-humanization-lab"
PUBLIC_BRANCH = "automation/pangram-fixed-batch"
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
REQUIRED_KEYS = {
    "format",
    "request_id",
    "public_repo",
    "public_branch",
    "spec_path",
    "spec_sha256",
    "confirmation",
}


class ValidationError(ValueError):
    pass


def strict_json(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) > 16_384:
        raise ValidationError("request exceeds 16 KiB")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise ValidationError(f"duplicate JSON key: {key!r}")
            out[key] = value
        return out

    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"request is not strict UTF-8 JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValidationError("request must be a JSON object")
    if set(obj) != REQUIRED_KEYS:
        raise ValidationError(
            f"request keys must match contract; missing={sorted(REQUIRED_KEYS-set(obj))}, "
            f"extra={sorted(set(obj)-REQUIRED_KEYS)}"
        )
    return obj


def changed_files(root: Path, base: str, head: str) -> list[tuple[str, str]]:
    if not GIT_SHA_RE.fullmatch(base) or not GIT_SHA_RE.fullmatch(head):
        raise ValidationError("base/head must be full Git SHAs")
    if base == "0" * 40:
        raise ValidationError("paid requests require an existing branch base")
    cp = subprocess.run(
        ["git", "diff", "--name-status", "--no-renames", "-z", base, head, "--"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    fields = cp.stdout.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 2:
        raise ValidationError("unexpected git diff record")
    out: list[tuple[str, str]] = []
    for index in range(0, len(fields), 2):
        status = fields[index].decode("ascii")
        path = fields[index + 1].decode("utf-8")
        out.append((status, path))
    return out


def validate(root: Path, *, base: str, head: str) -> dict[str, str]:
    changes = changed_files(root, base, head)
    if len(changes) != 1:
        raise ValidationError("paid trigger push must add exactly one request file and nothing else")
    status, raw_path = changes[0]
    if status != "A":
        raise ValidationError("request must be newly added; modification/replay is forbidden")

    relative = Path(raw_path)
    if len(relative.parts) != 2 or relative.parts[0] != "requests" or relative.suffix != ".json":
        raise ValidationError("request path must be requests/<request-id>.json")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValidationError("request path escapes repository") from exc
    if path.is_symlink() or not path.is_file():
        raise ValidationError("request must be a regular file")

    obj = strict_json(path)
    request_id = obj["request_id"]
    if not isinstance(request_id, str) or not REQUEST_ID_RE.fullmatch(request_id):
        raise ValidationError("invalid request_id")
    if relative.stem != request_id:
        raise ValidationError("request_id must match request filename")
    if obj["format"] != FORMAT:
        raise ValidationError(f"format must equal {FORMAT}")
    if obj["public_repo"] != PUBLIC_REPO:
        raise ValidationError(f"public_repo must equal {PUBLIC_REPO}")
    if obj["public_branch"] != PUBLIC_BRANCH:
        raise ValidationError(f"public_branch must equal {PUBLIC_BRANCH}")
    if obj["confirmation"] != CONFIRMATION:
        raise ValidationError(f"confirmation must equal {CONFIRMATION}")

    spec_raw = obj["spec_path"]
    if not isinstance(spec_raw, str) or not SAFE_PATH_RE.fullmatch(spec_raw):
        raise ValidationError("spec_path contains unsupported characters")
    spec = Path(spec_raw)
    if spec.is_absolute() or ".." in spec.parts:
        raise ValidationError("spec_path must be repository-relative")
    if len(spec.parts) < 2 or spec.parts[0] != "experiments" or spec.suffix.lower() != ".json":
        raise ValidationError("spec_path must name JSON under experiments/")

    digest = obj["spec_sha256"]
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise ValidationError("spec_sha256 must be 64 lowercase hex characters")

    return {
        "request_id": request_id,
        "spec_path": spec.as_posix(),
        "spec_sha256": digest,
    }


def write_outputs(path: Path, result: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key in ("request_id", "spec_path", "spec_sha256"):
            handle.write(f"{key}={result[key]}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        result = validate(root, base=args.base, head=args.head)
    except (ValidationError, OSError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    if args.github_output:
        write_outputs(args.github_output, result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
