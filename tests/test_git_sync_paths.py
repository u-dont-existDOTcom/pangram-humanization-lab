from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pangram_lab.git_sync import GitSync, GitSyncError


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _committed_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    sync = GitSync(root, require_remote=False)
    sync.ensure_repo()
    (root / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    _git(root, "add", "baseline.txt")
    _git(root, "commit", "-m", "baseline")
    return root


def test_sync_paths_commits_only_evidence_and_preserves_unrelated_staging(
    tmp_path: Path,
) -> None:
    root = _committed_repo(tmp_path)
    evidence = root / "state" / "gui-runs" / "pangram-4" / ("a" * 64)
    evidence.mkdir(parents=True)
    (evidence / "result.json").write_text('{"status":"complete"}\n', encoding="utf-8")

    unrelated = root / "unrelated.txt"
    unrelated.write_text("leave staged\n", encoding="utf-8")
    _git(root, "add", "unrelated.txt")

    GitSync(root, require_remote=False).sync_paths(
        [evidence],
        "pangram local complete aaaaaaaaaaaaaaaa",
    )

    assert _git(root, "show", "HEAD:state/gui-runs/pangram-4/" + "a" * 64 + "/result.json")
    committed_names = set(_git(root, "show", "--format=", "--name-only", "HEAD").splitlines())
    assert committed_names == {"state/gui-runs/pangram-4/" + "a" * 64 + "/result.json"}
    assert _git(root, "status", "--porcelain") == "A  unrelated.txt"


def test_sync_paths_rejects_outside_repository(tmp_path: Path) -> None:
    root = _committed_repo(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")

    with pytest.raises(GitSyncError, match="outside the repository"):
        GitSync(root, require_remote=False).sync_paths([outside], "unsafe")


def test_sync_paths_rejects_repository_root(tmp_path: Path) -> None:
    root = _committed_repo(tmp_path)

    with pytest.raises(GitSyncError, match="entire repository root"):
        GitSync(root, require_remote=False).sync_paths([root], "unsafe")


def test_current_branch_fails_closed_on_detached_head(tmp_path: Path) -> None:
    root = _committed_repo(tmp_path)
    _git(root, "checkout", "--detach", "HEAD")

    with pytest.raises(GitSyncError, match="detached HEAD"):
        GitSync(root, require_remote=False).current_branch()
