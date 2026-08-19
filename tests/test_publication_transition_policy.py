from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "publication-secret-audit.yml"
SCRIPT = ROOT / "scripts" / "audit-publication-secrets.sh"
PROFILE = ROOT / ".github" / "codex-repository.json"


def test_publication_audit_is_manual_bounded_and_read_only_after_transition():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "pull_request:" not in text
    assert "push:" not in text
    assert "schedule:" not in text
    assert "contents: read" in text
    assert "issues: read" in text
    assert "pull-requests: read" in text
    assert "actions: read" in text
    assert "persist-credentials: false" in text
    assert "timeout-minutes: 45" in text


def test_publication_secret_scanner_is_pinned_and_redacted():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'GITLEAKS_VERSION="8.29.1"' in text
    assert 'GITLEAKS_SHA256="e4eb209d04e20339d77122a3bdf9cd41351255cfb27ebcb75e85325e04f88924"' in text
    assert "--redact=100" in text
    assert "--log-opts='--all'" in text
    assert "+refs/heads/*:refs/remotes/origin/*" in text
    assert "+refs/pull/*/head:refs/remotes/pull-heads/*" in text
    assert "+refs/pull/*/head:refs/remotes/pull/*" not in text
    assert "gh issue list" in text
    assert "gh pr list" in text
    assert "issues/comments" in text
    assert "pulls/comments" in text
    assert "gh run view" in text
    assert 'current_run_id="${GITHUB_RUN_ID:-}"' in text
    assert '"$run_id" == "$current_run_id"' in text


def test_generic_api_key_false_positive_handling_is_narrow_and_source_verified():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'finding.get("RuleID") != "generic-api-key"' in text
    assert "measurement_key|first_human_measurement_key" in text
    assert 'FIXTURE_LITERAL = "PANGRAM-SECRET-FIXTURE-4927"' in text
    assert '["git", "show", f"{commit}:{file_name}"]' in text
    assert "--exclude-rule=generic-api-key" not in text
    assert '"git_raw_findings"' in text
    assert '"git_known_false_positives_ignored"' in text
    assert '"git_secret_findings"' in text


def test_profile_records_confirmed_public_visibility():
    import json

    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert data["visibility"] == "public"
    transition = data["publication_transition"]
    assert transition["target_visibility"] == "public"
    assert transition["status"] == "public_readback_confirmed"
    assert transition["hosted_readback_visibility"] == "public"
    assert transition["owner_approved_test_corpus_disclosure"] is True
    assert transition["excluded_repository"] == "u-dont-existDOTcom/AskRigor-lessons"
