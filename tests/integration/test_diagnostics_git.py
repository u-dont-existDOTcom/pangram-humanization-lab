from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from authorial_flow.config import RuntimeConfig
from authorial_flow.diagnostics import (
    DIAGNOSTICS_BRANCH,
    build_diagnostic_record,
    load_queued_diagnostics,
    publish_diagnostic,
    publish_queued_diagnostics,
    select_diagnostics_remote,
)


def _git(path: Path, *args: str, git_dir: bool = False) -> str:
    command = ["git"]
    if git_dir:
        command.extend(["--git-dir", str(path)])
    else:
        command.extend(["-C", str(path)])
    command.extend(args)
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def _source_and_remote(tmp_path: Path) -> tuple[Path, Path, RuntimeConfig]:
    source = tmp_path / "source"
    remote = tmp_path / "diagnostics.git"
    source.mkdir()
    _git(source, "init", "-b", "install/authorial-flow-graph-v1-1.3.0-dev1")
    _git(source, "config", "user.name", "Test User")
    _git(source, "config", "user.email", "test@example.invalid")
    (source / ".gitignore").write_text(".state/\n", encoding="utf-8")
    (source / "source.txt").write_text("source branch sentinel\n", encoding="utf-8")
    _git(source, "add", ".gitignore", "source.txt")
    _git(source, "commit", "-m", "source baseline")
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
    _git(source, "remote", "add", "authorial-release", str(remote))
    return source, remote, RuntimeConfig.from_root(source)


def _remote_file(remote: Path, ref_path: str) -> str:
    return _git(remote, "show", ref_path, git_dir=True)


def test_publish_creates_orphan_diagnostics_branch_without_mutating_source_checkout(
    tmp_path: Path,
) -> None:
    source, remote, cfg = _source_and_remote(tmp_path)
    record = build_diagnostic_record(
        cfg,
        phase="manual-status",
        outcome="snapshot",
        result={"failure_record_ref": "e" * 64},
        now=1786518307.0,
    )
    before_head = _git(source, "rev-parse", "HEAD")
    before_branch = _git(source, "branch", "--show-current")
    before_status = _git(source, "status", "--porcelain=v1", "--untracked-files=all")

    published = publish_diagnostic(
        cfg,
        record,
        remote_url=str(remote),
        branch=DIAGNOSTICS_BRANCH,
        timeout_seconds=10,
    )

    assert published.status == "published"
    assert published.run_id == record["run_id"]
    assert published.branch == DIAGNOSTICS_BRANCH
    assert published.queued_count == 0
    assert len(published.commit_sha) == 40
    assert published.failure_kind == ""
    assert published.attempts == 1
    assert _git(source, "rev-parse", "HEAD") == before_head
    assert _git(source, "branch", "--show-current") == before_branch
    assert _git(source, "status", "--porcelain=v1", "--untracked-files=all") == before_status

    latest = json.loads(_remote_file(remote, f"{DIAGNOSTICS_BRANCH}:LATEST.json"))
    run_path = f"runs/2026-08-12/{record['run_id']}.json"
    archived = json.loads(_remote_file(remote, f"{DIAGNOSTICS_BRANCH}:{run_path}"))
    assert latest == record
    assert archived == record
    names = _git(remote, "ls-tree", "-r", "--name-only", DIAGNOSTICS_BRANCH, git_dir=True).splitlines()
    assert names == ["LATEST.json", run_path]
    assert load_queued_diagnostics(cfg) == ()
    assert not list((cfg.state_dir / "diagnostics" / "tmp").glob("*"))


def test_git_transport_stabilizes_messages_without_losing_utf8_paths(
    tmp_path: Path, monkeypatch,
) -> None:
    import authorial_flow.diagnostics as diagnostics

    checkout = tmp_path / "Téléchargements" / "diagnostics-checkout"
    checkout.mkdir(parents=True)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text(
        """#!/bin/sh
if [ "$1" = "fetch" ]; then
    if [ -z "${LC_ALL+x}" ] && [ "$LC_MESSAGES" = "C" ] && [ "$LANGUAGE" = "C" ] && [ "$LC_CTYPE" = "fr_FR.UTF-8" ]; then
        printf "%s\\n" "fatal: couldn't find remote ref refs/heads/diagnostics/authorial-flow-graph-v1" >&2
    else
        printf "%s\\n" "fatal: référence distante introuvable" >&2
    fi
    exit 128
fi
exit 0
""",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("LC_ALL", "fr_FR.UTF-8")
    monkeypatch.delenv("LC_CTYPE", raising=False)
    monkeypatch.setenv("LC_MESSAGES", "fr_FR.UTF-8")
    monkeypatch.setenv("LANGUAGE", "fr")

    mode = diagnostics._prepare_diagnostics_checkout(
        checkout,
        remote_url="https://github.com/u-dont-existDOTcom/pangram-humanization-lab.git",
        branch=DIAGNOSTICS_BRANCH,
        timeout_seconds=10,
    )

    assert mode == "orphan"
    assert os.environ["LC_ALL"] == "fr_FR.UTF-8"


def test_repeated_and_sequential_publication_is_idempotent_and_append_only(tmp_path: Path) -> None:
    _, remote, cfg = _source_and_remote(tmp_path)
    first = build_diagnostic_record(cfg, phase="runtime-run", outcome="bounded_machine_stop", now=1.0)
    second = build_diagnostic_record(cfg, phase="runtime-resume", outcome="accepted", now=2.0)

    first_result = publish_diagnostic(cfg, first, remote_url=str(remote), timeout_seconds=10)
    duplicate_result = publish_diagnostic(cfg, first, remote_url=str(remote), timeout_seconds=10)
    assert duplicate_result.status == "already_published", duplicate_result
    second_result = publish_diagnostic(cfg, second, remote_url=str(remote), timeout_seconds=10)

    assert first_result.status == "published"
    assert duplicate_result.commit_sha == first_result.commit_sha
    assert second_result.status == "published"
    assert int(_git(remote, "rev-list", "--count", DIAGNOSTICS_BRANCH, git_dir=True)) == 2
    names = set(_git(remote, "ls-tree", "-r", "--name-only", DIAGNOSTICS_BRANCH, git_dir=True).splitlines())
    assert f"runs/1970-01-01/{first['run_id']}.json" in names
    assert f"runs/1970-01-01/{second['run_id']}.json" in names
    assert json.loads(_remote_file(remote, f"{DIAGNOSTICS_BRANCH}:LATEST.json")) == second


def test_failed_remote_queues_without_raw_error_and_later_flushes(tmp_path: Path) -> None:
    source, remote, cfg = _source_and_remote(tmp_path)
    record = build_diagnostic_record(cfg, phase="installer-preflight", outcome="failed", now=3.0)
    missing_remote = tmp_path / "SECRET-REMOTE-PATH" / "missing.git"

    queued = publish_diagnostic(
        cfg,
        record,
        remote_url=str(missing_remote),
        timeout_seconds=2,
    )

    assert queued.status == "queued"
    assert queued.failure_kind == "REMOTE_MISSING"
    assert queued.commit_sha == ""
    assert queued.queued_count == 1
    assert len(load_queued_diagnostics(cfg)) == 1
    status_text = (cfg.state_dir / "diagnostics" / "status.json").read_text(encoding="utf-8")
    assert "SECRET-REMOTE-PATH" not in status_text
    assert str(missing_remote) not in status_text

    flushed = publish_queued_diagnostics(cfg, remote_url=str(remote), timeout_seconds=10)
    assert flushed.status == "published"
    assert flushed.queued_count == 0
    assert load_queued_diagnostics(cfg) == ()
    assert json.loads(_remote_file(remote, f"{DIAGNOSTICS_BRANCH}:LATEST.json")) == record
    assert _git(source, "status", "--porcelain=v1", "--untracked-files=all") == ""


def test_remote_discovery_accepts_only_canonical_repository_identity(tmp_path: Path) -> None:
    source, _, cfg = _source_and_remote(tmp_path)
    _git(source, "remote", "remove", "authorial-release")
    _git(source, "remote", "add", "wrong", "https://github.com/example/public-repo.git")
    assert select_diagnostics_remote(cfg) is None

    canonical = "https://github.com/u-dont-existDOTcom/pangram-humanization-lab.git"
    _git(source, "remote", "add", "authorial-release", canonical)
    selected = select_diagnostics_remote(cfg)
    assert selected is not None
    assert selected.name == "authorial-release"
    assert selected.url == canonical

    os.environ["AUTHORIAL_DIAGNOSTICS_REMOTE"] = "wrong"
    try:
        assert select_diagnostics_remote(cfg) is None
    finally:
        os.environ.pop("AUTHORIAL_DIAGNOSTICS_REMOTE", None)


def test_non_fast_forward_race_refetches_and_preserves_both_commits(
    tmp_path: Path, monkeypatch,
) -> None:
    import authorial_flow.diagnostics as diagnostics

    _, remote, cfg = _source_and_remote(tmp_path)
    record = build_diagnostic_record(cfg, phase="runtime-run", outcome="accepted", now=4.0)
    original = diagnostics._git_result
    injected = False

    def race_once(args, *, cwd, timeout_seconds, check=True):
        nonlocal injected
        if args and args[0] == "push" and not injected:
            injected = True
            external = tmp_path / "external-publisher"
            external.mkdir()
            _git(external, "init", "-b", "external")
            _git(external, "config", "user.name", "External Publisher")
            _git(external, "config", "user.email", "external@example.invalid")
            (external / "EXTERNAL.json").write_text('{"external":true}\n', encoding="utf-8")
            _git(external, "add", "EXTERNAL.json")
            _git(external, "commit", "-m", "concurrent diagnostic")
            _git(external, "push", str(remote), f"HEAD:refs/heads/{DIAGNOSTICS_BRANCH}")
        return original(args, cwd=cwd, timeout_seconds=timeout_seconds, check=check)

    monkeypatch.setattr(diagnostics, "_git_result", race_once)
    result = publish_diagnostic(cfg, record, remote_url=str(remote), timeout_seconds=10)

    assert result.status == "published"
    assert result.attempts == 2
    names = set(_git(remote, "ls-tree", "-r", "--name-only", DIAGNOSTICS_BRANCH, git_dir=True).splitlines())
    assert "EXTERNAL.json" in names
    assert f"runs/1970-01-01/{record['run_id']}.json" in names
    assert int(_git(remote, "rev-list", "--count", DIAGNOSTICS_BRANCH, git_dir=True)) == 2
