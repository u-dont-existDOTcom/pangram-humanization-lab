#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

from scripts.validate_paid_dispatch import (
    PAID_RUN_CONFIRMATION,
    DispatchValidationError,
    _repository_path,
    validate_dispatch,
)


PAID_REQUEST_FORMAT = "pangram-paid-run-request-v1"
_REQUEST_PREFIX = ("requests", "pangram")
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_REQUEST_KEYS = {
    "format",
    "request_id",
    "spec_path",
    "spec_sha256",
    "confirmation",
}


class PaidPushValidationError(ValueError):
    pass


def _reject_symlink_components(root: Path, relative: Path, *, label: str) -> None:
    current = root
    for component in relative.parts:
        current /= component
        if current.is_symlink():
            raise PaidPushValidationError(f"{label} must not contain symlink components")


def _request_object(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PaidPushValidationError(f"paid request is unreadable: {exc}") from exc
    if len(raw) > 16_384:
        raise PaidPushValidationError("paid request exceeds the 16 KiB limit")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        obj: dict[str, Any] = {}
        for key, value in pairs:
            if key in obj:
                raise PaidPushValidationError(
                    f"paid request contains duplicate key {key!r}"
                )
            obj[key] = value
        return obj

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PaidPushValidationError(f"paid request is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise PaidPushValidationError("paid request must be a JSON object")
    if set(value) != _REQUEST_KEYS:
        missing = sorted(_REQUEST_KEYS - set(value))
        extra = sorted(set(value) - _REQUEST_KEYS)
        raise PaidPushValidationError(
            f"paid request keys must match the v1 contract; missing={missing}, extra={extra}"
        )
    return value


def validate_paid_push(
    root: Path | str,
    *,
    changes: Iterable[tuple[str, str]],
) -> dict[str, Any]:
    root = Path(root).resolve()
    changed = list(changes)
    request_changes = [
        (status, raw_path)
        for status, raw_path in changed
        if Path(raw_path).parts[:2] == _REQUEST_PREFIX
    ]
    if not request_changes:
        return {"paid_request": False}

    if len(request_changes) != 1 or len(changed) != 2:
        raise PaidPushValidationError(
            "a paid push must change exactly two files—the added request and its added spec; "
            "bundled changes are forbidden"
        )

    request_status, request_raw = request_changes[0]
    if request_status != "A":
        raise PaidPushValidationError(
            "paid request files are immutable and must be newly added"
        )

    try:
        request_relative, request_path = _repository_path(
            root, request_raw, label="paid request path"
        )
    except DispatchValidationError as exc:
        raise PaidPushValidationError(str(exc)) from exc
    if (
        len(request_relative.parts) != 3
        or request_relative.parts[:2] != _REQUEST_PREFIX
        or request_relative.suffix.lower() != ".json"
    ):
        raise PaidPushValidationError(
            "paid request path must be requests/pangram/<request-id>.json"
        )
    _reject_symlink_components(root, request_relative, label="paid request path")
    if not request_path.is_file():
        raise PaidPushValidationError("paid request must name an existing regular file")

    request = _request_object(request_path)
    if request["format"] != PAID_REQUEST_FORMAT:
        raise PaidPushValidationError(
            f"paid request format must equal {PAID_REQUEST_FORMAT}"
        )

    request_id = request["request_id"]
    if not isinstance(request_id, str) or not _REQUEST_ID_RE.fullmatch(request_id):
        raise PaidPushValidationError("request_id has an invalid or unsafe form")
    if request_relative.stem != request_id:
        raise PaidPushValidationError("request_id must match the request filename")

    spec_raw = request["spec_path"]
    if not isinstance(spec_raw, str):
        raise PaidPushValidationError("spec_path must be a string")
    try:
        spec_relative, spec_path = _repository_path(root, spec_raw, label="spec path")
    except DispatchValidationError as exc:
        raise PaidPushValidationError(str(exc)) from exc
    _reject_symlink_components(root, spec_relative, label="spec path")

    matching_spec_changes = [
        status for status, raw_path in changed if raw_path == spec_relative.as_posix()
    ]
    if matching_spec_changes != ["A"]:
        raise PaidPushValidationError(
            "the referenced spec must be newly added in the same push"
        )
    if {raw_path for _, raw_path in changed} != {
        request_relative.as_posix(),
        spec_relative.as_posix(),
    }:
        raise PaidPushValidationError(
            "the push must contain exactly the request and its referenced spec"
        )

    digest = request["spec_sha256"]
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise PaidPushValidationError("spec_sha256 must be 64 lowercase hexadecimal characters")
    try:
        actual_digest = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise PaidPushValidationError(f"spec is unreadable: {exc}") from exc
    if actual_digest != digest:
        raise PaidPushValidationError(
            "spec_sha256 digest does not match the exact checked-out spec bytes"
        )

    confirmation = request["confirmation"]
    if not isinstance(confirmation, str):
        raise PaidPushValidationError("confirmation must be a string")
    try:
        validated = validate_dispatch(
            root,
            spec_raw=spec_relative.as_posix(),
            output_raw="",
            confirmation=confirmation,
        )
    except DispatchValidationError as exc:
        raise PaidPushValidationError(str(exc)) from exc
    if validated["experiment_id"] != request_id:
        raise PaidPushValidationError(
            "request_id must equal the fixed-batch experiment_id"
        )

    return {
        "paid_request": True,
        "spec_path": validated["spec_path"],
        "result_path": validated["result_path"],
    }


def discover_changes(root: Path, *, base: str, head: str) -> list[tuple[str, str]]:
    if not _GIT_SHA_RE.fullmatch(base) or not _GIT_SHA_RE.fullmatch(head):
        raise PaidPushValidationError("base and head must be full 40-character Git SHAs")
    if base == "0" * 40:
        raise PaidPushValidationError("automatic paid runs require an existing branch base")

    try:
        checked_out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PaidPushValidationError(f"cannot resolve checked-out HEAD: {exc}") from exc
    if checked_out.lower() != head.lower():
        raise PaidPushValidationError("checked-out HEAD does not match the push event head")

    try:
        raw = subprocess.run(
            [
                "git",
                "diff",
                "--name-status",
                "--no-renames",
                "-z",
                base,
                head,
                "--",
            ],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PaidPushValidationError(f"cannot inventory pushed files: {exc}") from exc

    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 2:
        raise PaidPushValidationError("unexpected git diff name-status record")
    changes: list[tuple[str, str]] = []
    for index in range(0, len(fields), 2):
        try:
            status = fields[index].decode("ascii")
            path = fields[index + 1].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PaidPushValidationError("changed paths must be valid UTF-8") from exc
        if status not in {"A", "M", "D", "T", "U"}:
            raise PaidPushValidationError(f"unsupported git change status {status!r}")
        changes.append((status, path))
    return changes


def write_github_output(path: Path, result: dict[str, Any]) -> None:
    paid_request = result.get("paid_request") is True
    lines = [f"paid_request={'true' if paid_request else 'false'}"]
    if paid_request:
        lines.extend(
            [
                f"spec_path={result['spec_path']}",
                f"result_path={result['result_path']}",
            ]
        )
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a push-bound paid Pangram request without detector or secret access"
        )
    )
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    try:
        result = validate_paid_push(
            root,
            changes=discover_changes(root, base=args.base, head=args.head),
        )
    except PaidPushValidationError as exc:
        parser.error(str(exc))
    if args.github_output is not None:
        write_github_output(args.github_output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
