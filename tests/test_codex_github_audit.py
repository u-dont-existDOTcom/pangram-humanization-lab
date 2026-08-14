from pathlib import Path

import pytest

from scripts.audit_codex_github import _audit_workflows, audit_repository


ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_SHA = "d23441a48e516b6c34aea4fa41551a30e30af803"


def test_repository_visible_codex_github_baseline_has_no_errors():
    findings = audit_repository(ROOT)
    errors = [
        finding["message"]
        for finding in findings
        if finding["severity"] == "error"
    ]
    assert errors == []


def test_policy_source_is_not_mistaken_for_pull_request_target_trigger():
    findings = audit_repository(ROOT)
    false_positives = [
        finding
        for finding in findings
        if finding["code"] == "actions.pull-request-target.checkout"
        and finding.get("path") == ".github/workflows/repository-workflow-policy.yml"
    ]
    assert false_positives == []


@pytest.mark.parametrize(
    "trigger",
    [
        "on:\n  pull_request_target:",
        "on:\n  pull_request_target: {}",
        "on: pull_request_target",
        "on: [push, pull_request_target]",
        "on: {push: {}, pull_request_target: {}}",
        "on:\n  - push\n  - pull_request_target",
    ],
)
def test_privileged_trigger_forms_with_checkout_are_rejected(tmp_path: Path, trigger: str):
    workflow = tmp_path / ".github" / "workflows" / "probe.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        f"""name: probe
{trigger}

permissions:
  contents: read

jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@{CHECKOUT_SHA}
""",
        encoding="utf-8",
    )
    findings = []
    _audit_workflows(tmp_path, [workflow], findings)
    assert any(
        finding["code"] == "actions.pull-request-target.checkout"
        for finding in findings
    )


def test_shell_literal_is_not_mistaken_for_privileged_trigger(tmp_path: Path):
    workflow = tmp_path / ".github" / "workflows" / "probe.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        f"""name: probe
on: [push]

permissions:
  contents: read

jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@{CHECKOUT_SHA}
      - run: echo 'pull_request_target:'
""",
        encoding="utf-8",
    )
    findings = []
    _audit_workflows(tmp_path, [workflow], findings)
    assert not any(
        finding["code"] == "actions.pull-request-target.checkout"
        for finding in findings
    )
