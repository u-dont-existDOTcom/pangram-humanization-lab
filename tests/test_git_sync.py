import subprocess
from pathlib import Path

import pytest

from pangram_lab.git_sync import GitSync, GitSyncError


def run(*args,cwd):
    return subprocess.run(args,cwd=cwd,text=True,capture_output=True,check=True)


def init_remote_pair(tmp_path: Path) -> tuple[Path, Path, Path]:
    remote = tmp_path / "remote.git"
    seed = tmp_path / "seed"
    local = tmp_path / "local"
    collaborator = tmp_path / "collaborator"

    run("git", "init", "--bare", str(remote), cwd=tmp_path)
    run("git", "init", "-b", "main", str(seed), cwd=tmp_path)
    run("git", "config", "user.email", "test@example.com", cwd=seed)
    run("git", "config", "user.name", "Test", cwd=seed)
    (seed / "state").mkdir()
    (seed / "state" / "baseline.json").write_text("{}\n")
    (seed / "notes.txt").write_text("original\n")
    run("git", "add", ".", cwd=seed)
    run("git", "commit", "-m", "baseline", cwd=seed)
    run("git", "remote", "add", "origin", str(remote), cwd=seed)
    run("git", "push", "-u", "origin", "main", cwd=seed)

    run("git", "clone", "--branch", "main", str(remote), str(local), cwd=tmp_path)
    run(
        "git",
        "clone",
        "--branch",
        "main",
        str(remote),
        str(collaborator),
        cwd=tmp_path,
    )
    for checkout in (local, collaborator):
        run("git", "config", "user.email", "test@example.com", cwd=checkout)
        run("git", "config", "user.name", "Test", cwd=checkout)
    return remote, local, collaborator


def test_local_commit_sync_commits_durable_state(tmp_path):
    run('git','init','-b','main',cwd=tmp_path)
    run('git','config','user.email','test@example.com',cwd=tmp_path); run('git','config','user.name','Test',cwd=tmp_path)
    (tmp_path/'a.txt').write_text('a')
    gs=GitSync(tmp_path, require_remote=False)
    gs.sync('initial')
    assert run('git','log','--oneline','-1',cwd=tmp_path).stdout.strip()


def test_remote_state_only_advance_is_fast_forwarded_without_touching_dirty_bytes(
    tmp_path: Path,
) -> None:
    remote, local, collaborator = init_remote_pair(tmp_path)
    dirty = local / "notes.txt"
    dirty.write_text("owner bytes that must survive\n")

    (collaborator / "state" / "remote-result.json").write_text('{"complete": true}\n')
    run("git", "add", "state/remote-result.json", cwd=collaborator)
    run("git", "commit", "-m", "remote evidence", cwd=collaborator)
    run("git", "push", "origin", "main", cwd=collaborator)

    GitSync(local).ensure_remote_durable("test state-only remote advance")

    assert dirty.read_text() == "owner bytes that must survive\n"
    assert (local / "state" / "remote-result.json").read_text() == '{"complete": true}\n'
    local_head = run("git", "rev-parse", "HEAD", cwd=local).stdout.strip()
    remote_head = run(
        "git", "--git-dir", str(remote), "rev-parse", "refs/heads/main", cwd=tmp_path
    ).stdout.strip()
    assert local_head == remote_head


def test_remote_runtime_advance_requires_restart_before_browser_work(tmp_path: Path) -> None:
    _, local, collaborator = init_remote_pair(tmp_path)
    local_head = run("git", "rev-parse", "HEAD", cwd=local).stdout.strip()
    (collaborator / "src").mkdir()
    (collaborator / "src" / "runtime.py").write_text("UPDATED = True\n")
    run("git", "add", "src/runtime.py", cwd=collaborator)
    run("git", "commit", "-m", "runtime update", cwd=collaborator)
    run("git", "push", "origin", "main", cwd=collaborator)

    with pytest.raises(GitSyncError, match="runtime-affecting paths"):
        GitSync(local).ensure_remote_durable("test runtime update")

    assert run("git", "rev-parse", "HEAD", cwd=local).stdout.strip() == local_head


def test_two_sided_divergence_fails_closed_without_merging(tmp_path: Path) -> None:
    _, local, collaborator = init_remote_pair(tmp_path)
    (local / "state" / "local.json").write_text('{"side": "local"}\n')
    run("git", "add", "state/local.json", cwd=local)
    run("git", "commit", "-m", "local evidence", cwd=local)
    local_head = run("git", "rev-parse", "HEAD", cwd=local).stdout.strip()

    (collaborator / "state" / "remote.json").write_text('{"side": "remote"}\n')
    run("git", "add", "state/remote.json", cwd=collaborator)
    run("git", "commit", "-m", "remote evidence", cwd=collaborator)
    run("git", "push", "origin", "main", cwd=collaborator)

    with pytest.raises(GitSyncError, match="histories have diverged"):
        GitSync(local).ensure_remote_durable("test true divergence")

    assert run("git", "rev-parse", "HEAD", cwd=local).stdout.strip() == local_head
    assert not (local / "state" / "remote.json").exists()
