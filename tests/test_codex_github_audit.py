from pathlib import Path

from scripts.audit_codex_github import audit_repository


ROOT = Path(__file__).resolve().parents[1]


def test_repository_visible_codex_github_baseline_has_no_errors():
    findings = audit_repository(ROOT)
    errors = [finding.message for finding in findings if finding.level == "ERROR"]
    assert errors == []
