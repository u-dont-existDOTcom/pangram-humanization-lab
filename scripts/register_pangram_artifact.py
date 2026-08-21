from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RegistrationError(RuntimeError):
    pass


def _validate_id(label: str, value: str) -> None:
    if not _ID_RE.fullmatch(value):
        raise RegistrationError(f"{label} has an invalid form: {value!r}")


def build_registration(
    *,
    text_path: Path,
    expected_text_sha256: str,
    experiment_id: str,
    audit_id: str,
    section_id: str,
    variant_id: str,
    spec_path: str,
) -> tuple[bytes, bytes]:
    for label, value in (
        ("experiment_id", experiment_id),
        ("audit_id", audit_id),
        ("section_id", section_id),
        ("variant_id", variant_id),
    ):
        _validate_id(label, value)
    if not _SHA256_RE.fullmatch(expected_text_sha256):
        raise RegistrationError("expected text SHA-256 must be 64 lowercase hexadecimal characters")
    if not spec_path.startswith("experiments/") or not spec_path.endswith(".json"):
        raise RegistrationError("spec_path must be a JSON path under experiments/")

    literal = text_path.read_bytes()
    actual_text_sha256 = hashlib.sha256(literal).hexdigest()
    if actual_text_sha256 != expected_text_sha256:
        raise RegistrationError(
            f"text SHA-256 mismatch: expected={expected_text_sha256} actual={actual_text_sha256}"
        )
    try:
        text = literal.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RegistrationError(f"detector text is not valid UTF-8: {exc}") from exc

    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": experiment_id,
        "audit_id": audit_id,
        "variants": [
            {
                "id": variant_id,
                "section_id": section_id,
                "text": text,
            }
        ],
    }
    spec_bytes = (
        json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")

    request = {
        "format": "pangram-paid-run-request-v1",
        "request_id": experiment_id,
        "spec_path": spec_path,
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
        "confirmation": "RUN_PAID_PANGRAM_FIXED_BATCH",
    }
    request_bytes = (
        json.dumps(request, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")
    return spec_bytes, request_bytes


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a hash-bound Pangram fixed-batch spec/request pair.")
    parser.add_argument("--text", required=True, type=Path)
    parser.add_argument("--expected-text-sha256", required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--audit-id", required=True)
    parser.add_argument("--section-id", required=True)
    parser.add_argument("--variant-id", required=True)
    parser.add_argument("--spec-path", required=True)
    parser.add_argument("--spec-out", required=True, type=Path)
    parser.add_argument("--request-out", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        spec_bytes, request_bytes = build_registration(
            text_path=args.text,
            expected_text_sha256=args.expected_text_sha256,
            experiment_id=args.experiment_id,
            audit_id=args.audit_id,
            section_id=args.section_id,
            variant_id=args.variant_id,
            spec_path=args.spec_path,
        )
        args.spec_out.parent.mkdir(parents=True, exist_ok=True)
        args.request_out.parent.mkdir(parents=True, exist_ok=True)
        args.spec_out.write_bytes(spec_bytes)
        args.request_out.write_bytes(request_bytes)
    except (OSError, RegistrationError) as exc:
        print(f"registration failed: {exc}", file=sys.stderr)
        return 2

    print(f"spec_sha256={hashlib.sha256(spec_bytes).hexdigest()}")
    print(f"text_sha256={args.expected_text_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
