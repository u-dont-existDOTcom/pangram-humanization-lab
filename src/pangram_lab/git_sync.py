from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Iterable


class GitSyncError(RuntimeError):
    pass


def _run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise GitSyncError(f"command failed ({' '.join(args)}): {detail}")
    return completed


class GitSync:
    def __init__(self, root: Path, *, require_remote: bool = True):
        self.root = Path(root).resolve()
        self.require_remote = require_remote

    def ensure_repo(self) -> None:
        if not (self.root / ".git").exists():
            _run(["git", "init", "-b", "main"], self.root)
        if not _run(["git", "config", "user.email"], self.root, check=False).stdout.strip():
            _run(["git", "config", "user.email", "pangram-lab@local"], self.root)
        if not _run(["git", "config", "user.name"], self.root, check=False).stdout.strip():
            _run(["git", "config", "user.name", "Pangram Lab"], self.root)

    def has_remote(self) -> bool:
        return bool(
            _run(
                ["git", "remote", "get-url", "origin"],
                self.root,
                check=False,
            ).stdout.strip()
        )

    def ensure_github(self, repo_name: str = "pangram-humanization-lab") -> None:
        self.ensure_repo()
        if self.has_remote():
            return
        gh = shutil.which("gh")
        if not gh:
            raise GitSyncError(
                "GitHub CLI (gh) is not installed. Install/authenticate gh, then rerun; "
                "no Pangram calls will start before GitHub backup is configured."
            )
        if _run([gh, "auth", "status"], self.root, check=False).returncode:
            print("[github] GitHub login required. Starting `gh auth login`…", flush=True)
            subprocess.run([gh, "auth", "login"], cwd=self.root, check=True)
        subprocess.run([gh, "auth", "setup-git"], cwd=self.root, check=True)
        owner = _run([gh, "api", "user", "-q", ".login"], self.root).stdout.strip()
        full = f"{owner}/{repo_name}"
        if _run([gh, "repo", "view", full], self.root, check=False).returncode:
            print(f"[github] creating private repository {full}", flush=True)
            completed = subprocess.run(
                [
                    gh,
                    "repo",
                    "create",
                    full,
                    "--private",
                    "--source",
                    str(self.root),
                    "--remote",
                    "origin",
                ],
                cwd=self.root,
                text=True,
                capture_output=True,
            )
            if completed.returncode:
                raise GitSyncError(completed.stderr.strip() or completed.stdout.strip())
        else:
            _run(
                ["git", "remote", "add", "origin", f"https://github.com/{full}.git"],
                self.root,
            )
        print(f"[github] repository: {full}", flush=True)

    def current_branch(self) -> str:
        self.ensure_repo()
        branch = _run(
            ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
            self.root,
            check=False,
        ).stdout.strip()
        if not branch:
            raise GitSyncError(
                "detached HEAD is not allowed for Pangram evidence durability; switch to a named branch"
            )
        return branch

    def _normalized_relative_paths(self, paths: Iterable[Path]) -> tuple[str, ...]:
        root = self.root.resolve()
        normalized: list[str] = []
        seen: set[str] = set()
        for supplied in paths:
            candidate = Path(supplied)
            absolute = candidate if candidate.is_absolute() else root / candidate
            resolved = absolute.resolve(strict=False)
            try:
                relative = resolved.relative_to(root)
            except ValueError as exc:
                raise GitSyncError(
                    f"refusing to sync a path outside the repository: {resolved}"
                ) from exc
            if relative == Path("."):
                raise GitSyncError("refusing path-scoped sync of the entire repository root")
            value = relative.as_posix()
            if value not in seen:
                normalized.append(value)
                seen.add(value)
        if not normalized:
            raise GitSyncError("at least one repository path is required for scoped evidence sync")
        return tuple(normalized)

    def ensure_remote_durable(self, reason: str) -> None:
        self.ensure_repo()
        if not self.require_remote:
            return
        if not self.has_remote():
            raise GitSyncError(
                "origin is not configured; refusing to continue to paid detector calls"
            )
        branch = self.current_branch()
        completed = _run(
            [
                "git",
                "push",
                "-u",
                "origin",
                f"HEAD:refs/heads/{branch}",
            ],
            self.root,
            check=False,
        )
        if completed.returncode:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise GitSyncError(
                "GitHub push failed; local state is preserved and the next paid call is blocked "
                f"until sync succeeds: {detail}"
            )
        print(f"[github] pushed durable state ({reason})", flush=True)

    def sync_paths(self, paths: Iterable[Path], reason: str) -> None:
        """Commit only the supplied evidence paths, preserving unrelated staged work."""
        self.ensure_repo()
        relative_paths = self._normalized_relative_paths(paths)
        _run(["git", "add", "-A", "--", *relative_paths], self.root)
        changed = _run(
            ["git", "diff", "--cached", "--quiet", "--", *relative_paths],
            self.root,
            check=False,
        )
        if changed.returncode not in (0, 1):
            detail = changed.stderr.strip() or changed.stdout.strip()
            raise GitSyncError(f"cannot inspect staged Pangram evidence paths: {detail}")
        if changed.returncode == 1:
            message = "state: " + reason[:160]
            _run(
                ["git", "commit", "--only", "-m", message, "--", *relative_paths],
                self.root,
            )
            print(f"[github] committed scoped evidence: {message}", flush=True)
        self.ensure_remote_durable(reason)

    def sync(self, reason: str) -> None:
        self.ensure_repo()
        _run(["git", "add", "-A"], self.root)
        diff = _run(["git", "diff", "--cached", "--quiet"], self.root, check=False)
        if diff.returncode != 0:
            message = "state: " + reason[:160]
            _run(["git", "commit", "-m", message], self.root)
            print(f"[github] committed: {message}", flush=True)
        self.ensure_remote_durable(reason)
