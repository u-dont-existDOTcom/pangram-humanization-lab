from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


def _git(repo:Path,*args:str,check:bool=True)->subprocess.CompletedProcess:
    return subprocess.run(['git',*args],cwd=repo,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=check)


@dataclass(frozen=True)
class WorktreeRef:
    repair_id: str
    path: Path
    base_commit: str


class WorktreeManager:
    def __init__(self,repo_root:Path,worktree_root:Path):
        self.repo_root=Path(repo_root).resolve()
        self.worktree_root=Path(worktree_root).resolve()

    def create(self,repair_id:str)->WorktreeRef:
        if not repair_id or '/' in repair_id or '..' in repair_id:
            raise ValueError('unsafe repair id')
        base=_git(self.repo_root,'rev-parse','HEAD').stdout.strip()
        path=self.worktree_root/repair_id
        if path.exists():
            raise FileExistsError(path)
        path.parent.mkdir(parents=True,exist_ok=True)
        _git(self.repo_root,'worktree','add','--detach',str(path),base)
        return WorktreeRef(repair_id,path,base)

    def discard(self,ref:WorktreeRef)->None:
        _git(self.repo_root,'worktree','remove','--force',str(ref.path),check=False)
        shutil.rmtree(ref.path,ignore_errors=True)
        _git(self.repo_root,'worktree','prune',check=False)

    def promote(self,ref:WorktreeRef,commit_sha:str)->str:
        status_lines=[line for line in _git(self.repo_root,'status','--porcelain').stdout.splitlines() if line.strip()]
        # Runtime worktrees live under .state and are intentionally untracked. They do not count
        # as user/main-worktree edits; every other tracked or untracked change blocks promotion.
        dirty=[line for line in status_lines if not (line.startswith('?? ') and line[3:].startswith('.state/'))]
        if dirty:
            raise RuntimeError('main worktree is dirty; refuse repair promotion')
        current=_git(self.repo_root,'rev-parse','HEAD').stdout.strip()
        if current != ref.base_commit:
            raise RuntimeError('main branch moved since repair worktree creation')
        # Candidate commit must be descended from the captured base.
        anc=_git(self.repo_root,'merge-base','--is-ancestor',ref.base_commit,commit_sha,check=False)
        if anc.returncode != 0:
            raise RuntimeError('candidate commit is not descended from repair base')
        _git(self.repo_root,'merge','--ff-only',commit_sha)
        return _git(self.repo_root,'rev-parse','HEAD').stdout.strip()
