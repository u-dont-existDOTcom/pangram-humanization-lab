from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT
    / "ops"
    / "pangram-private-executor"
    / "template"
    / "scripts"
    / "validate_request_push.py"
)
WORKFLOW_PATH = (
    ROOT
    / "ops"
    / "pangram-private-executor"
    / "template"
    / ".github"
    / "workflows"
    / "execute-pangram.yml"
)
BOOTSTRAP_PATH = ROOT / "ops" / "pangram-private-executor" / "bootstrap.sh"


def load_validator():
    spec = importlib.util.spec_from_file_location("private_executor_validator", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(root: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    return cp.stdout.strip()


def init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    (root / "README.md").write_text("base\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "base")
    return root


def request_obj(request_id: str = "sample-run") -> dict[str, str]:
    return {
        "format": "pangram-private-executor-request-v1",
        "request_id": request_id,
        "public_repo": "u-dont-existDOTcom/pangram-humanization-lab",
        "public_branch": "automation/pangram-fixed-batch",
        "spec_path": f"experiments/{request_id}.json",
        "spec_sha256": "a" * 64,
        "confirmation": "RUN_PAID_PANGRAM_FIXED_BATCH",
    }


def commit_request(root: Path, obj: dict[str, str], *, extra_file: bool = False):
    request_dir = root / "requests"
    request_dir.mkdir(exist_ok=True)
    path = request_dir / f"{obj['request_id']}.json"
    path.write_text(json.dumps(obj) + "\n", encoding="utf-8")
    git(root, "add", path.relative_to(root).as_posix())
    if extra_file:
        (root / "extra.txt").write_text("unexpected\n", encoding="utf-8")
        git(root, "add", "extra.txt")
    git(root, "commit", "-m", "request")


def test_valid_request_push_is_accepted(tmp_path):
    validator = load_validator()
    root = init_repo(tmp_path)
    base = git(root, "rev-parse", "HEAD")
    commit_request(root, request_obj())
    head = git(root, "rev-parse", "HEAD")

    result = validator.validate(root, base=base, head=head)

    assert result == {
        "request_id": "sample-run",
        "spec_path": "experiments/sample-run.json",
        "spec_sha256": "a" * 64,
    }


def test_multi_file_trigger_fails_closed(tmp_path):
    validator = load_validator()
    root = init_repo(tmp_path)
    base = git(root, "rev-parse", "HEAD")
    commit_request(root, request_obj(), extra_file=True)
    head = git(root, "rev-parse", "HEAD")

    with pytest.raises(validator.ValidationError, match="exactly one request"):
        validator.validate(root, base=base, head=head)


def test_other_public_repository_is_rejected(tmp_path):
    validator = load_validator()
    root = init_repo(tmp_path)
    base = git(root, "rev-parse", "HEAD")
    obj = request_obj()
    obj["public_repo"] = "attacker/repo"
    commit_request(root, obj)
    head = git(root, "rev-parse", "HEAD")

    with pytest.raises(validator.ValidationError, match="public_repo"):
        validator.validate(root, base=base, head=head)


def test_path_escape_is_rejected(tmp_path):
    validator = load_validator()
    root = init_repo(tmp_path)
    base = git(root, "rev-parse", "HEAD")
    obj = request_obj()
    obj["spec_path"] = "experiments/../outside.json"
    commit_request(root, obj)
    head = git(root, "rev-parse", "HEAD")

    with pytest.raises(validator.ValidationError, match="repository-relative"):
        validator.validate(root, base=base, head=head)


def test_workflow_never_runs_on_pull_requests_or_github_hosted_runner():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "pull_request:" not in workflow
    assert "runs-on: [self-hosted, linux, x64, pangram]" in workflow
    assert "PANGRAM_API_KEY: ${{ secrets.PANGRAM_API_KEY }}" in workflow
    assert "automation/pangram-fixed-batch" in workflow


def test_bootstrap_pins_official_runner_installer_and_github_host_key():
    bootstrap = BOOTSTRAP_PATH.read_text(encoding="utf-8")
    assert "258d6c857db3519913f7deb6004b60172f8043ae" in bootstrap
    assert "raw.githubusercontent.com/actions/runner/${RUNNER_INSTALLER_COMMIT}" in bootstrap
    assert "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl" in bootstrap
    assert "ssh-keyscan" not in bootstrap
    assert "set -x" not in bootstrap
