from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class GitSyncError(RuntimeError): pass


def _run(args, cwd: Path, check=True):
    cp=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
    if check and cp.returncode:
        raise GitSyncError(f"command failed ({' '.join(args)}): {cp.stderr.strip() or cp.stdout.strip()}")
    return cp


class GitSync:
    def __init__(self, root: Path, *, require_remote: bool = True):
        self.root=Path(root); self.require_remote=require_remote

    def ensure_repo(self):
        if not (self.root/".git").exists():
            _run(["git","init","-b","main"],self.root)
        if not _run(["git","config","user.email"],self.root,check=False).stdout.strip():
            _run(["git","config","user.email","pangram-lab@local"],self.root)
        if not _run(["git","config","user.name"],self.root,check=False).stdout.strip():
            _run(["git","config","user.name","Pangram Lab"],self.root)

    def has_remote(self) -> bool:
        return bool(_run(["git","remote","get-url","origin"],self.root,check=False).stdout.strip())

    def ensure_github(self, repo_name: str = "pangram-humanization-lab"):
        self.ensure_repo()
        if self.has_remote():
            return
        gh=shutil.which("gh")
        if not gh:
            raise GitSyncError("GitHub CLI (gh) is not installed. Install/authenticate gh, then rerun; no Pangram calls will start before GitHub backup is configured.")
        if _run([gh,"auth","status"],self.root,check=False).returncode:
            print("[github] GitHub login required. Starting `gh auth login`…", flush=True)
            subprocess.run([gh,"auth","login"],cwd=self.root,check=True)
        subprocess.run([gh,"auth","setup-git"],cwd=self.root,check=True)
        owner=_run([gh,"api","user","-q",".login"],self.root).stdout.strip()
        full=f"{owner}/{repo_name}"
        if _run([gh,"repo","view",full],self.root,check=False).returncode:
            print(f"[github] creating private repository {full}", flush=True)
            cp=subprocess.run([gh,"repo","create",full,"--private","--source",str(self.root),"--remote","origin"],cwd=self.root,text=True,capture_output=True)
            if cp.returncode:
                raise GitSyncError(cp.stderr.strip() or cp.stdout.strip())
        else:
            url=f"https://github.com/{full}.git"
            _run(["git","remote","add","origin",url],self.root)
        print(f"[github] repository: {full}", flush=True)

    def sync(self, reason: str):
        self.ensure_repo()
        _run(["git","add","-A"],self.root)
        diff=_run(["git","diff","--cached","--quiet"],self.root,check=False)
        if diff.returncode != 0:
            msg="state: "+reason[:160]
            _run(["git","commit","-m",msg],self.root)
            print(f"[github] committed: {msg}", flush=True)
        if self.require_remote:
            if not self.has_remote():
                raise GitSyncError("origin is not configured; refusing to continue to paid detector calls")
            cp=_run(["git","push","-u","origin","HEAD"],self.root,check=False)
            if cp.returncode:
                raise GitSyncError(f"GitHub push failed; local state is preserved and next paid call is blocked until sync succeeds: {cp.stderr.strip()}")
            print(f"[github] pushed durable state ({reason})", flush=True)
