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

    def _remote_tracking_ref(self, branch: str) -> str:
        return f"refs/remotes/origin/{branch}"

    def _fetch_current_branch(self, branch: str) -> str | None:
        """Refresh the matching origin ref without changing the checked-out tree.

        A missing remote branch is normal for the first durability push, so a
        failed fetch is left for the subsequent push to diagnose.  Successful
        fetches let us distinguish an ordinary remote-only advance from a true
        two-sided divergence before a paid browser boundary.
        """
        remote_ref = self._remote_tracking_ref(branch)
        completed = _run(
            [
                "git",
                "fetch",
                "--no-tags",
                "origin",
                f"refs/heads/{branch}:{remote_ref}",
            ],
            self.root,
            check=False,
        )
        if completed.returncode:
            return None
        return remote_ref

    def _is_ancestor(self, older: str, newer: str) -> bool:
        completed = _run(
            ["git", "merge-base", "--is-ancestor", older, newer],
            self.root,
            check=False,
        )
        if completed.returncode not in (0, 1):
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise GitSyncError(f"cannot compare local and remote durability history: {detail}")
        return completed.returncode == 0

    def _changed_paths(self, older: str, newer: str) -> tuple[str, ...]:
        completed = _run(
            ["git", "diff", "--name-only", "-z", older, newer],
            self.root,
        )
        return tuple(path for path in completed.stdout.split("\0") if path)

    def _incorporate_safe_remote_advance(self, branch: str) -> bool:
        """Fast-forward remote-only evidence commits without reloading code.

        Only changes below ``state/`` are safe to absorb inside a running CLI
        process.  Source, scripts, configuration, documentation, and tests may
        affect the current execution contract and therefore require a clean
        operator update/restart instead of being changed underneath imports.
        """
        remote_ref = self._fetch_current_branch(branch)
        if remote_ref is None:
            return False

        local_head = _run(["git", "rev-parse", "HEAD"], self.root).stdout.strip()
        remote_head = _run(["git", "rev-parse", remote_ref], self.root).stdout.strip()
        if local_head == remote_head or self._is_ancestor(remote_head, local_head):
            return False
        if not self._is_ancestor(local_head, remote_head):
            raise GitSyncError(
                "local and GitHub durability histories have diverged; local state is preserved. "
                "Inspect both histories and reconcile them without force-pushing before another "
                "paid Pangram action."
            )

        changed_paths = self._changed_paths(local_head, remote_head)
        runtime_paths = tuple(path for path in changed_paths if not path.startswith("state/"))
        if runtime_paths:
            preview = ", ".join(runtime_paths[:5])
            suffix = "" if len(runtime_paths) <= 5 else ", ..."
            raise GitSyncError(
                "GitHub contains a fast-forward update that changes runtime-affecting paths "
                f"({preview}{suffix}); local state is preserved. Run `git pull --ff-only`, "
                "restart pangram-local so the updated code is loaded, then retry."
            )

        completed = _run(
            ["git", "merge", "--ff-only", remote_ref],
            self.root,
            check=False,
        )
        if completed.returncode:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise GitSyncError(
                "GitHub has a state-only fast-forward, but it could not be incorporated without "
                f"touching local bytes; local state is preserved: {detail}"
            )
        print("[github] incorporated state-only remote advance", flush=True)
        return True

    def _push_current_branch(self, branch: str) -> subprocess.CompletedProcess[str]:
        return _run(
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

    def ensure_remote_durable(self, reason: str) -> None:
        self.ensure_repo()
        if not self.require_remote:
            return
        if not self.has_remote():
            raise GitSyncError(
                "origin is not configured; refusing to continue to paid detector calls"
            )
        branch = self.current_branch()
        self._incorporate_safe_remote_advance(branch)
        completed = self._push_current_branch(branch)
        if completed.returncode:
            # Close the race where another state-only durability commit lands
            # after the first fetch but before our push.
            incorporated = self._incorporate_safe_remote_advance(branch)
            if incorporated:
                completed = self._push_current_branch(branch)
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
