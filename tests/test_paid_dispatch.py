import json
from pathlib import Path

import pytest

from scripts.validate_paid_dispatch import (
    PAID_RUN_CONFIRMATION,
    DispatchValidationError,
    validate_dispatch,
)


def write_spec(root: Path, *, audit_id="audit-1", section_id="opening") -> Path:
    path = root / "experiments" / "batch.json"
    path.parent.mkdir(parents=True)
    obj = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "verified-batch",
        "audit_id": audit_id,
        "variants": [
            {"id": "A", "section_id": section_id, "text": "Exact reader-visible text."}
        ],
    }
    path.write_text(json.dumps(obj), encoding="utf-8")
    return path


def test_validated_dispatch_returns_canonical_repository_paths(tmp_path: Path):
    write_spec(tmp_path)
    result = validate_dispatch(
        tmp_path,
        spec_raw="experiments/batch.json",
        output_raw="",
        confirmation=PAID_RUN_CONFIRMATION,
    )
    assert result["spec_path"] == "experiments/batch.json"
    assert result["result_path"] == "state/experiments/verified-batch-results.json"
    assert result["audit_id"] == "audit-1"
    assert result["variant_count"] == 1


def test_dispatch_requires_exact_paid_run_confirmation(tmp_path: Path):
    write_spec(tmp_path)
    with pytest.raises(DispatchValidationError, match="confirmation"):
        validate_dispatch(
            tmp_path,
            spec_raw="experiments/batch.json",
            output_raw="",
            confirmation="yes",
        )


def test_dispatch_rejects_spec_outside_experiments(tmp_path: Path):
    outside = tmp_path / "batch.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(DispatchValidationError, match="experiments"):
        validate_dispatch(
            tmp_path,
            spec_raw="batch.json",
            output_raw="",
            confirmation=PAID_RUN_CONFIRMATION,
        )


@pytest.mark.parametrize(
    ("audit_id", "section_id", "match"),
    [(None, "opening", "audit_id"), ("audit-1", None, "section_id")],
)
def test_dispatch_requires_accounted_audit_identity(
    tmp_path: Path, audit_id: str | None, section_id: str | None, match: str
):
    write_spec(tmp_path, audit_id=audit_id, section_id=section_id)
    with pytest.raises((DispatchValidationError, ValueError), match=match):
        validate_dispatch(
            tmp_path,
            spec_raw="experiments/batch.json",
            output_raw="",
            confirmation=PAID_RUN_CONFIRMATION,
        )


def test_dispatch_rejects_noncanonical_output_path(tmp_path: Path):
    write_spec(tmp_path)
    with pytest.raises((DispatchValidationError, ValueError), match="canonical|output"):
        validate_dispatch(
            tmp_path,
            spec_raw="experiments/batch.json",
            output_raw="state/experiments/other-results.json",
            confirmation=PAID_RUN_CONFIRMATION,
        )
