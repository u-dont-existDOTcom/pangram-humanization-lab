from pathlib import Path

from scripts.audit_codex_github import audit_repository


ROOT = Path(__file__).resolve().parents[1]


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
