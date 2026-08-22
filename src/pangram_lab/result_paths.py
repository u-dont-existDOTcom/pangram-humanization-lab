from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

_SAFE_EXPERIMENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,179}$")
_RESULTS_FORMAT = "pangram-fixed-batch-results-v1"


def _validate_experiment_id(experiment_id: str) -> str:
    if not isinstance(experiment_id, str) or not _SAFE_EXPERIMENT_ID.fullmatch(experiment_id):
        raise ValueError(
            "experiment_id must be a safe filename segment using only letters, numbers, dot, underscore, or hyphen"
        )
    return experiment_id


def canonical_result_path(root: Path | str, experiment_id: str) -> Path:
    experiment_id = _validate_experiment_id(experiment_id)
    return Path(root) / "state" / "experiments" / f"{experiment_id}-results.json"


def _spec_identity(spec: dict[str, Any]) -> dict[str, Any]:
    # A text_source spec is fingerprinted by its immutable source identity and
    # expected UTF-8 SHA-256. Runtime resolution adds variant["text"], but that
    # derived copy must not change the registered experiment identity.
    identity = json.loads(json.dumps(spec, ensure_ascii=False))
    variants = identity.get("variants")
    if isinstance(variants, list):
        for variant in variants:
            if isinstance(variant, dict) and variant.get("text_source") is not None:
                variant.pop("text", None)
    return identity


def spec_sha256(spec: dict[str, Any]) -> str:
    payload = json.dumps(
        _spec_identity(spec),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def resolve_result_path(root: Path | str, spec: dict[str, Any], requested: Path | str | None = None) -> Path:
    root = Path(root).resolve()
    expected = canonical_result_path(root, spec["experiment_id"]).resolve()
    if requested is None:
        return expected
    requested_path = Path(requested)
    if not requested_path.is_absolute():
        requested_path = root / requested_path
    requested_path = requested_path.resolve()
    if requested_path != expected:
        raise ValueError(
            f"result path must be derived from experiment_id; expected {expected.relative_to(root)}, got {requested_path}"
        )
    return expected


def _legacy_rows_match_complete_spec(spec: dict[str, Any], saved: dict[str, Any]) -> bool:
    rows = saved.get("results")
    variants = spec.get("variants")
    if not isinstance(rows, list) or not isinstance(variants, list) or len(rows) != len(variants):
        return False
    for row, variant in zip(rows, variants):
        if not isinstance(row, dict) or not isinstance(variant, dict):
            return False
        if row.get("id") != variant.get("id"):
            return False
        text = variant.get("text")
        if not isinstance(text, str):
            return False
        if row.get("text_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
            return False
        if row.get("section_id") != variant.get("section_id"):
            return False
    return True


def load_compatible_existing_result(spec: dict[str, Any], path: Path | str) -> dict[str, Any] | None:
    path = Path(path)
    if not path.exists():
        return None
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"existing result path is not readable fixed-batch JSON: {path}") from exc
    if not isinstance(saved, dict) or saved.get("format") != _RESULTS_FORMAT:
        raise ValueError(f"existing result path is not {_RESULTS_FORMAT}: {path}")
    if saved.get("experiment_id") != spec.get("experiment_id"):
        raise ValueError("existing result path belongs to a different experiment_id")

    expected_spec_sha = spec_sha256(spec)
    recorded_spec_sha = saved.get("spec_sha256")
    if recorded_spec_sha is not None:
        if recorded_spec_sha != expected_spec_sha:
            raise ValueError("experiment_id already exists with a different fixed-batch spec; use a new experiment_id")
        return saved

    if not _legacy_rows_match_complete_spec(spec, saved):
        raise ValueError(
            "legacy result without spec fingerprint cannot be safely resumed or replaced; use a new experiment_id"
        )
    return saved


def new_result_envelope(spec: dict[str, Any]) -> dict[str, Any]:
    envelope: dict[str, Any] = {
        "format": _RESULTS_FORMAT,
        "experiment_id": spec["experiment_id"],
        "spec_sha256": spec_sha256(spec),
        "results": [],
    }
    if spec.get("audit_id") is not None:
        envelope["audit_id"] = spec["audit_id"]
    return envelope


def result_is_complete(spec: dict[str, Any], saved: dict[str, Any]) -> bool:
    if saved.get("status") == "section_call_cap_reached":
        return False
    rows = saved.get("results")
    variants = spec.get("variants")
    return isinstance(rows, list) and isinstance(variants, list) and len(rows) == len(variants)
