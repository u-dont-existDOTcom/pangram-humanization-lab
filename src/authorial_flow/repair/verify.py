from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
import shlex
import subprocess
import sys
from typing import Any, Callable

from .protection import ProtectedSnapshot, ProtectionReport, validate_candidate_diff
from .schemas import RepairPlan
from .worktree import WorktreeRef


@dataclass(frozen=True)
class VerificationCommand:
    argv: tuple[str,...]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class VerificationResult:
    pass_: bool
    commands: tuple[VerificationCommand,...]
    protection: ProtectionReport | None=None
    review_provider: str=''
    review_reason: str=''
    fix_attempts: int=0


def safe_plan_test_commands(plan:RepairPlan)->list[list[str]]:
    """Accept only direct local pytest invocations from a machine-authored repair plan."""
    accepted:list[list[str]]=[]
    for raw in plan.tests:
        try:
            argv=shlex.split(str(raw))
        except ValueError:
            continue
        if not argv or any(token in {';','|','||','&&','&','>','>>','<'} or '://' in token or '..' in token for token in argv):
            continue
        executable=argv[0]
        if executable in {'python','python3'}:
            if len(argv)<3 or argv[1:3] != ['-m','pytest']:
                continue
        elif executable != 'pytest':
            continue
        accepted.append(argv)
    return accepted


def validate_repair_plan_commands(plan: RepairPlan) -> str:
    if not plan.repairable or plan.needs_owner_judgment:
        return ""
    if not plan.tests:
        return "MISSING_TEST_COMMAND"
    commands = safe_plan_test_commands(plan)
    if len(commands) != len(plan.tests):
        return "UNSAFE_OR_NON_EXECUTABLE_TEST_COMMAND"
    return ""


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def repair_plan_signature(
    plan: RepairPlan,
    *,
    evidence_ref: str,
    program_version: str,
) -> str:
    commands = [shlex.join(argv) for argv in safe_plan_test_commands(plan)]
    payload = {
        "diagnosis": _normalized_text(plan.diagnosis),
        "patch_summary": _normalized_text(plan.patch_summary),
        "target_files": sorted({_normalized_text(path) for path in plan.target_files}),
        "tests": sorted(commands),
        "evidence_ref": str(evidence_ref or ""),
        "program_version": str(program_version or ""),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


class RepairVerifier:
    def __init__(self,*,reviewer:Any,source_texts:list[str],protected_snapshot:ProtectedSnapshot,
                 commands:list[list[str]]|None=None,additional_commands:list[list[str]]|None=None):
        self.reviewer=reviewer
        self.source_texts=list(source_texts)
        self.protected_snapshot=protected_snapshot
        self.commands=commands
        self.additional_commands=[list(argv) for argv in (additional_commands or [])]

    def _commands_for(self,plan:RepairPlan)->list[list[str]]:
        if self.commands is not None:
            commands=[list(argv) for argv in self.commands]
            commands.extend([list(argv) for argv in self.additional_commands])
            return commands
        commands:list[list[str]]=[
            [sys.executable,'-m','compileall','-q','src','tests'],
        ]
        commands.extend(safe_plan_test_commands(plan))
        commands.extend([
            [sys.executable,'-m','pytest','tests/unit','tests/regression','-q'],
            [sys.executable,'-m','pytest','tests/integration','-q'],
            [sys.executable,'-m','pytest','-q'],
        ])
        commands.extend([list(argv) for argv in self.additional_commands])
        # Preserve order while avoiding redundant exact commands.
        unique:list[list[str]]=[]; seen:set[tuple[str,...]]=set()
        for argv in commands:
            key=tuple(argv)
            if key not in seen:
                seen.add(key); unique.append(argv)
        return unique

    def verify(self,worktree:WorktreeRef,plan:RepairPlan)->VerificationResult:
        results=[]
        for argv in self._commands_for(plan):
            p=subprocess.run(argv,cwd=worktree.path,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            rec=VerificationCommand(tuple(argv),p.returncode,p.stdout,p.stderr)
            results.append(rec)
            if p.returncode != 0:
                return VerificationResult(False,tuple(results),review_reason='verification command failed')

        protection=validate_candidate_diff(
            worktree.path,worktree.base_commit,self.source_texts,protected_snapshot=self.protected_snapshot
        )
        if not protection.pass_:
            return VerificationResult(False,tuple(results),protection,review_reason='protected/source-hardcoding gate failed')

        summary='\n'.join(f"$ {' '.join(r.argv)} => {r.returncode}" for r in results)
        reviewed=self.reviewer.review_diff(plan,protection.diff_text,summary)
        approved=reviewed.decision.verdict == 'APPROVE'
        return VerificationResult(
            approved,tuple(results),protection,
            review_provider=reviewed.provider,review_reason=reviewed.decision.reason,
        )


def verify_with_one_fix(verifier:RepairVerifier,worktree:WorktreeRef,plan:RepairPlan,
                        fixer:Callable[[WorktreeRef,VerificationResult],str])->VerificationResult:
    first=verifier.verify(worktree,plan)
    if first.pass_:
        return first
    fixed_sha=fixer(worktree,first)
    if not fixed_sha:
        return VerificationResult(
            first.pass_,first.commands,first.protection,first.review_provider,
            first.review_reason,1,
        )
    second=verifier.verify(worktree,plan)
    return VerificationResult(
        second.pass_,second.commands,second.protection,second.review_provider,second.review_reason,1
    )
