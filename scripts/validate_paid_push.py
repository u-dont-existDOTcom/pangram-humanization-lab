#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

try:
    from scripts.validate_paid_dispatch import (
        PAID_RUN_CONFIRMATION,
        DispatchValidationError,
        _repository_path,
        validate_dispatch,
    )
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    from validate_paid_dispatch import (  # type: ignore[no-redef]
        PAID_RUN_CONFIRMATION,
        DispatchValidationError,
        _repository_path,
        validate_dispatch,
    )


PAID_REQUEST_FORMAT = "pangram-paid-run-request-v1"
PAID_TRIGGER_FORMAT = "pangram-paid-trigger-v1"
_REQUEST_PREFIX = ("requests", "pangram")
_TRIGGER_PREFIX = ("triggers", "pangram")
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
_TRIGGER_KEYS = {
    "format",
    "request_id",
    "request_path",
    "request_sha256",
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


def _strict_json_object(
    path: Path,
    *,
    label: str,
    required_keys: set[str],
) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PaidPushValidationError(f"{label} is unreadable: {exc}") from exc
    if len(raw) > 16_384:
        raise PaidPushValidationError(f"{label} exceeds the 16 KiB limit")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        obj: dict[str, Any] = {}
        for key, value in pairs:
            if key in obj:
                raise PaidPushValidationError(
                    f"{label} contains duplicate key {key!r}"
                )
            obj[key] = value
        return obj

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PaidPushValidationError(
            f"{label} is not valid UTF-8 JSON: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise PaidPushValidationError(f"{label} must be a JSON object")
    if set(value) != required_keys:
        missing = sorted(required_keys - set(value))
        extra = sorted(set(value) - required_keys)
        raise PaidPushValidationError(
            f"{label} keys must match the v1 contract; missing={missing}, extra={extra}"
        )
    return value


def _request_object(path: Path) -> dict[str, Any]:
    return _strict_json_object(
        path,
        label="paid request",
        required_keys=_REQUEST_KEYS,
    )


def _trigger_object(path: Path) -> dict[str, Any]:
    return _strict_json_object(
        path,
        label="paid trigger",
        required_keys=_TRIGGER_KEYS,
    )


def _validate_request_identity(
    root: Path,
    *,
    request_raw: str,
) -> tuple[Path, Path, dict[str, Any]]:
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
    return request_relative, request_path, request


def _validate_registered_request(
    root: Path,
    *,
    request_relative: Path,
    request_path: Path,
    request: dict[str, Any],
) -> dict[str, Any]:
    spec_raw = request["spec_path"]
    if not isinstance(spec_raw, str):
        raise PaidPushValidationError("spec_path must be a string")
    try:
        spec_relative, spec_path = _repository_path(root, spec_raw, label="spec path")
    except DispatchValidationError as exc:
        raise PaidPushValidationError(str(exc)) from exc
    _reject_symlink_components(root, spec_relative, label="spec path")
    if not spec_path.is_file():
        raise PaidPushValidationError("registered spec must name an existing regular file")

    digest = request["spec_sha256"]
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise PaidPushValidationError(
            "spec_sha256 must be 64 lowercase hexadecimal characters"
        )
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
    if validated["experiment_id"] != request["request_id"]:
        raise PaidPushValidationError(
            "request_id must equal the fixed-batch experiment_id"
        )
    return validated


def _validate_trigger_push(
    root: Path,
    *,
    changed: list[tuple[str, str]],
    trigger_changes: list[tuple[str, str]],
) -> dict[str, Any]:
    if len(trigger_changes) != 1 or len(changed) != 1:
        raise PaidPushValidationError(
            "a registered paid trigger push must change exactly one newly added trigger file; bundled changes are forbidden"
        )

    trigger_status, trigger_raw = trigger_changes[0]
    if trigger_status != "A":
        raise PaidPushValidationError(
            "paid trigger files are immutable and must be newly added"
        )
    try:
        trigger_relative, trigger_path = _repository_path(
            root, trigger_raw, label="paid trigger path"
        )
    except DispatchValidationError as exc:
        raise PaidPushValidationError(str(exc)) from exc
    if (
        len(trigger_relative.parts) != 3
        or trigger_relative.parts[:2] != _TRIGGER_PREFIX
        or trigger_relative.suffix.lower() != ".json"
    ):
        raise PaidPushValidationError(
            "paid trigger path must be triggers/pangram/<request-id>.json"
        )
    _reject_symlink_components(root, trigger_relative, label="paid trigger path")
    if not trigger_path.is_file():
        raise PaidPushValidationError("paid trigger must name an existing regular file")

    trigger = _trigger_object(trigger_path)
    if trigger["format"] != PAID_TRIGGER_FORMAT:
        raise PaidPushValidationError(
            f"paid trigger format must equal {PAID_TRIGGER_FORMAT}"
        )
    trigger_id = trigger["request_id"]
    if not isinstance(trigger_id, str) or not _REQUEST_ID_RE.fullmatch(trigger_id):
        raise PaidPushValidationError("trigger request_id has an invalid or unsafe form")
    if trigger_relative.stem != trigger_id:
        raise PaidPushValidationError(
            "trigger request_id must match the trigger filename"
        )
    if trigger.get("confirmation") != PAID_RUN_CONFIRMATION:
        raise PaidPushValidationError(
            f"paid trigger confirmation must equal {PAID_RUN_CONFIRMATION}"
        )

    request_raw = trigger["request_path"]
    if not isinstance(request_raw, str):
        raise PaidPushValidationError("trigger request_path must be a string")
    request_relative, request_path, request = _validate_request_identity(
        root,
        request_raw=request_raw,
    )
    if request["request_id"] != trigger_id:
        raise PaidPushValidationError(
            "trigger request_id must match the registered request_id"
        )

    request_digest = trigger["request_sha256"]
    if not isinstance(request_digest, str) or not _SHA256_RE.fullmatch(request_digest):
        raise PaidPushValidationError(
            "request_sha256 must be 64 lowercase hexadecimal characters"
        )
    try:
        actual_request_digest = hashlib.sha256(request_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise PaidPushValidationError(f"registered request is unreadable: {exc}") from exc
    if actual_request_digest != request_digest:
        raise PaidPushValidationError(
            "request_sha256 digest does not match the exact registered request bytes"
        )

    validated = _validate_registered_request(
        root,
        request_relative=request_relative,
        request_path=request_path,
        request=request,
    )
    result_path = root / validated["result_path"]
    if result_path.is_symlink() or result_path.exists():
        raise PaidPushValidationError(
            "the registered request already has a result; refusing a second paid trigger"
        )
    return {
        "paid_request": True,
        "spec_path": validated["spec_path"],
        "result_path": validated["result_path"],
    }


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
    trigger_changes = [
        (status, raw_path)
        for status, raw_path in changed
        if Path(raw_path).parts[:2] == _TRIGGER_PREFIX
    ]

    if trigger_changes:
        if request_changes:
            raise PaidPushValidationError(
                "a registered paid trigger must not be bundled with a new or modified paid request"
            )
        return _validate_trigger_push(
            root,
            changed=changed,
            trigger_changes=trigger_changes,
        )

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

    request_relative, request_path, request = _validate_request_identity(
        root,
        request_raw=request_raw,
    )

    spec_raw = request["spec_path"]
    if not isinstance(spec_raw, str):
        raise PaidPushValidationError("spec_path must be a string")
    try:
        spec_relative, _ = _repository_path(root, spec_raw, label="spec path")
    except DispatchValidationError as exc:
        raise PaidPushValidationError(str(exc)) from exc

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

    validated = _validate_registered_request(
        root,
        request_relative=request_relative,
        request_path=request_path,
        request=request,
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
            "Validate a push-bound paid Pangram request or one-shot registered trigger without detector or secret access"
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
