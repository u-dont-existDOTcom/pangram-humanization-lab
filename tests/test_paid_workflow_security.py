import json
from pathlib import Path

import pytest

from scripts.validate_paid_dispatch import (
    PAID_RUN_CONFIRMATION,
    DispatchValidationError,
    _write_github_output,
    validate_dispatch,
)


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pangram-paid-dispatch.yml"


def _write_spec(
    root: Path,
    *,
    audit_id: str = "audit-1",
    section_id: str = "opening",
) -> None:
    path = root / "experiments" / "batch.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "format": "pangram-fixed-batch-v1",
                "experiment_id": "verified-batch",
                "audit_id": audit_id,
                "variants": [
                    {
                        "id": "A",
                        "section_id": section_id,
                        "text": "Exact reader-visible text.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("audit_id", "section_id"),
    [
        ("audit-1\nspec_path=experiments/other.json", "opening"),
        ("audit-1", "opening\r\nresult_path=state/experiments/other.json"),
    ],
)
def test_dispatch_rejects_output_control_characters(
    tmp_path: Path, audit_id: str, section_id: str
) -> None:
    _write_spec(tmp_path, audit_id=audit_id, section_id=section_id)
    with pytest.raises(DispatchValidationError, match="audit_id|section_id|control"):
        validate_dispatch(
            tmp_path,
            spec_raw="experiments/batch.json",
            output_raw="",
            confirmation=PAID_RUN_CONFIRMATION,
        )


def test_github_output_contains_only_validated_runner_paths(tmp_path: Path) -> None:
    _write_spec(tmp_path)
    result = validate_dispatch(
        tmp_path,
        spec_raw="experiments/batch.json",
        output_raw="",
        confirmation=PAID_RUN_CONFIRMATION,
    )
    output = tmp_path / "github-output"
    _write_github_output(output, result)
    assert output.read_text(encoding="utf-8").splitlines() == [
        "spec_path=experiments/batch.json",
        "result_path=state/experiments/verified-batch-results.json",
    ]


def test_paid_workflow_is_exact_ref_bound_and_delays_credentials() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" not in workflow
    assert (
        "if: github.event_name == 'push' && "
        "github.ref == 'refs/heads/automation/pangram-fixed-batch' && "
        "needs.verify.outputs.paid_request == 'true'"
    ) in workflow
    assert "python scripts/validate_paid_push.py" in workflow
    assert '--base "$BASE_SHA"' in workflow
    assert '--head "$HEAD_SHA"' in workflow
    assert workflow.count("persist-credentials: false") >= 2
    assert workflow.count("contents: write") == 1
    assert workflow.count("${{ secrets.PANGRAM_API_KEY }}") == 1
    assert "audit_id: ${{ steps.preflight.outputs.audit_id }}" not in workflow
    assert "experiment_id: ${{ steps.preflight.outputs.experiment_id }}" not in workflow
