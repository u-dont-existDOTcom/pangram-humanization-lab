from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_WORKFLOW = ROOT / ".github" / "workflows" / "pangram-paid-dispatch.yml"


def test_default_branch_registration_is_manual_and_fail_closed() -> None:
    workflow = REGISTRATION_WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "RUN_PAID_PANGRAM_FIXED_BATCH" in workflow
    assert "DO_NOT_RUN" in workflow
    assert "automation/pangram-fixed-batch" in workflow
    assert "permissions: {}" in workflow
    assert "exit 1" in workflow
    assert "PANGRAM_API_KEY" not in workflow
    assert "actions/checkout@" not in workflow
    assert "push:" not in workflow
    assert "pull_request:" not in workflow
