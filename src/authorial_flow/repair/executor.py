from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Mapping

from ..artifacts import ArtifactStore
from ..process_runner import ProcessRunner, ProcessSpec
from ..secrets import child_env
from .evidence import materialize_evidence_bundle
from .schemas import RepairPlan, ImplementationResult
from .worktree import WorktreeRef
from .verify import safe_plan_test_commands




def _repair_child_env(worktree_path:Path, base_env:Mapping[str,str])->dict[str,str]:
    """Return credential-stripped env with the installed project venv first on PATH.

    Repair worktrees intentionally do not contain their own .venv. Git's common-dir
    points back to the installed main checkout, whose venv has the exact dependencies
    used by the running controller. Prefixing that venv keeps Codex RED/GREEN tests
    on the candidate worktree's `src` via pytest's configured pythonpath while avoiding
    accidental use of Zorin's system Python.
    """
    env=child_env(base_env,{'PANGRAM_API_KEY','BRAVE_SEARCH_API_KEY'})
    try:
        raw=subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=worktree_path,text=True).strip()
        common=Path(raw)
        if not common.is_absolute():
            common=(worktree_path/common).resolve()
        venv=common.parent/'.venv'
        venv_bin=venv/'bin'
        if (venv_bin/'python').exists():
            current=str(env.get('PATH') or '')
            env['PATH']=str(venv_bin)+(os.pathsep+current if current else '')
            env['VIRTUAL_ENV']=str(venv)
    except (OSError,subprocess.CalledProcessError):
        pass
    return env

class RepairExecutor:
    """Controlled Codex workspace-write executor scoped to a disposable worktree."""
    def __init__(self,models:list[str|None],*,base_env:Mapping[str,str]|None=None,timeout_seconds:float=2400):
        self.models=list(models); self.base_env=dict(base_env or os.environ); self.timeout_seconds=timeout_seconds

    @staticmethod
    def _proof_refs(proof_path:Path, plan:RepairPlan, store:ArtifactStore)->tuple[str,str,str] | None:
        try:
            proof=json.loads(proof_path.read_text(encoding='utf-8'))
            red=dict(proof['red']); green=dict(proof['green'])
            red_cmd=str(red['command']).strip(); green_cmd=str(green['command']).strip()
            red_rc=int(red['returncode']); green_rc=int(green['returncode'])
        except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError):
            return None
        if not red_cmd or red_cmd != green_cmd or red_rc == 0 or green_rc != 0:
            return None
        if plan.tests and red_cmd not in {str(item).strip() for item in plan.tests}:
            return None
        red_ref=store.put_text(json.dumps(red,ensure_ascii=False,sort_keys=True,indent=2)+'\n','json',{'kind':'repair-red-proof'}).sha256
        green_ref=store.put_text(json.dumps(green,ensure_ascii=False,sort_keys=True,indent=2)+'\n','json',{'kind':'repair-green-proof'}).sha256
        proof_ref=store.put_text(json.dumps(proof,ensure_ascii=False,sort_keys=True,indent=2)+'\n','json',{'kind':'repair-red-green-proof'}).sha256
        return red_ref,green_ref,proof_ref

    def apply(self,worktree:WorktreeRef,plan:RepairPlan,runner:ProcessRunner,store:ArtifactStore,
              *,evidence_bundle_text:str='')->ImplementationResult:
        safe_tests=safe_plan_test_commands(plan)
        if not plan.tests or len(safe_tests) != len(plan.tests):
            return ImplementationResult(success=False,provider='controller',returncode=2)
        protected=['project/','policy/','.state/learning/']
        evidence_dir=worktree.path/'supervisor-evidence'
        if evidence_bundle_text:
            materialize_evidence_bundle(worktree.path,evidence_bundle_text)
        else:
            evidence_dir.mkdir(parents=True,exist_ok=True)
            (evidence_dir/'failure-evidence.json').write_text('{}\n',encoding='utf-8')
        prompt=(
            'Implement only the approved machine repair in this disposable worktree. Do not modify '
            f'protected paths/prefixes {protected}. Do not hardcode current source/article wording. '
            'Do not query Pangram or Brave Search. Do not commit anything yourself. Run only local non-network tests. '
            'Work test-first: (1) add the smallest regression, (2) run the exact targeted test and observe it FAIL '
            'for the expected reason, (3) make the smallest production repair, (4) rerun the same targeted test and '
            'observe it PASS. Record those two real command results in supervisor-evidence/repair-proof.json with '
            'shape {"red":{"command":str,"returncode":int,"stdout":str,"stderr":str},'
            '"green":{"command":str,"returncode":int,"stdout":str,"stderr":str}}. '
            'The controller will independently verify your patch. Failure evidence is available at '
            'supervisor-evidence/failure-evidence.json.\n\nPLAN:\n'+plan.model_dump_json(indent=2)
        )
        safe_env=_repair_child_env(worktree.path,self.base_env)
        attempts=[]
        try:
            for model in self.models:
                proof_path=evidence_dir/'repair-proof.json'
                proof_path.unlink(missing_ok=True)
                argv=['codex','exec','--ephemeral','--sandbox','workspace-write','--skip-git-repo-check','--config','model_reasoning_effort="high"']
                if model: argv += ['--model',model]
                argv += ['-']
                result=runner.run(ProcessSpec(argv=argv,cwd=worktree.path,timeout_seconds=self.timeout_seconds,env=safe_env,input_text=prompt))
                out_ref=store.put_text(result.stdout,'stdout.txt',{'provider':'codex','role':'repair_executor','model':model or 'CLI-default'}).sha256 if result.stdout else ''
                err_ref=store.put_text(result.stderr,'stderr.txt',{'provider':'codex','role':'repair_executor','model':model or 'CLI-default'}).sha256 if result.stderr else ''
                if result.returncode==0:
                    proof_refs=self._proof_refs(proof_path,plan,store) if proof_path.is_file() else None
                    if proof_refs is None:
                        return ImplementationResult(success=False,provider='codex',model=model or 'CLI-default',returncode=0,stdout_ref=out_ref,stderr_ref=err_ref,transcript_ref=out_ref or err_ref)
                    current=subprocess.check_output(['git','rev-parse','HEAD'],cwd=worktree.path,text=True).strip()
                    if current != worktree.base_commit:
                        return ImplementationResult(success=False,provider='codex',model=model or 'CLI-default',returncode=0,stdout_ref=out_ref,stderr_ref=err_ref,transcript_ref=out_ref or err_ref)
                    # Repair evidence is diagnostic only and must never enter the promoted candidate.
                    shutil.rmtree(evidence_dir,ignore_errors=True)
                    subprocess.run(['git','add','-A'],cwd=worktree.path,check=True)
                    if subprocess.run(['git','diff','--cached','--quiet'],cwd=worktree.path).returncode==0:
                        return ImplementationResult(success=False,provider='codex',model=model or 'CLI-default',returncode=0,stdout_ref=out_ref,stderr_ref=err_ref,transcript_ref=out_ref or err_ref)
                    subprocess.run(['git','-c','user.name=Authorial Flow Repair','-c','user.email=repair@example.invalid','commit','-qm','machine repair candidate'],cwd=worktree.path,check=True)
                    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=worktree.path,text=True).strip()
                    red_ref,green_ref,proof_ref=proof_refs
                    return ImplementationResult(success=True,provider='codex',model=model or 'CLI-default',returncode=0,stdout_ref=out_ref,stderr_ref=err_ref,commit_sha=sha,transcript_ref=out_ref or err_ref,red_ref=red_ref,green_ref=green_ref,proof_ref=proof_ref)
                attempts.append(result.returncode)
            return ImplementationResult(success=False,provider='codex',returncode=attempts[-1] if attempts else 1)
        finally:
            shutil.rmtree(evidence_dir,ignore_errors=True)
    def correct(self,worktree:WorktreeRef,plan:RepairPlan,failed_verification,runner:ProcessRunner,store:ArtifactStore,
                *,previous_transcript_refs:list[str]|tuple[str,...]=())->ImplementationResult:
        """Give Codex exactly one bounded correction opportunity in the existing repair worktree."""
        safe_tests=safe_plan_test_commands(plan)
        if not plan.tests or len(safe_tests) != len(plan.tests):
            return ImplementationResult(success=False,provider='controller',returncode=2)
        evidence_dir=worktree.path/'supervisor-evidence'
        evidence_dir.mkdir(parents=True,exist_ok=True)
        diff=subprocess.check_output(['git','diff','--binary',worktree.base_commit,'--'],cwd=worktree.path,text=True)
        evidence={
            'plan':plan.model_dump(mode='json'),
            'candidate_diff':diff[-80000:],
            'review_reason':str(getattr(failed_verification,'review_reason','') or ''),
            'commands':[
                {'argv':list(c.argv),'returncode':c.returncode,'stdout':c.stdout[-6000:],'stderr':c.stderr[-6000:]}
                for c in getattr(failed_verification,'commands',())
            ],
            'previous_transcript_refs':list(previous_transcript_refs),
        }
        (evidence_dir/'correction-evidence.json').write_text(
            json.dumps(evidence,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8'
        )
        protected=['project/','policy/','.state/learning/']
        prompt=(
            'Make exactly one bounded correction to the existing machine-repair candidate. Read '
            'supervisor-evidence/correction-evidence.json. Fix only the verified failure; do not broaden the '
            f'patch, modify protected paths/prefixes {protected}, hardcode current source/article wording, query '
            'Pangram/Brave, or commit. Leave the corrected files in the worktree; the controller will rerun every '
            'verification gate from the beginning.\n\nPLAN:\n'+plan.model_dump_json(indent=2)
        )
        safe_env=_repair_child_env(worktree.path,self.base_env)
        attempts=[]
        try:
            for model in self.models:
                argv=['codex','exec','--ephemeral','--sandbox','workspace-write','--skip-git-repo-check','--config','model_reasoning_effort="high"']
                if model: argv += ['--model',model]
                argv += ['-']
                result=runner.run(ProcessSpec(argv=argv,cwd=worktree.path,timeout_seconds=self.timeout_seconds,env=safe_env,input_text=prompt))
                out_ref=store.put_text(result.stdout,'stdout.txt',{'provider':'codex','role':'repair_correction','model':model or 'CLI-default'}).sha256 if result.stdout else ''
                err_ref=store.put_text(result.stderr,'stderr.txt',{'provider':'codex','role':'repair_correction','model':model or 'CLI-default'}).sha256 if result.stderr else ''
                if result.returncode==0:
                    shutil.rmtree(evidence_dir,ignore_errors=True)
                    subprocess.run(['git','add','-A'],cwd=worktree.path,check=True)
                    if subprocess.run(['git','diff','--cached','--quiet'],cwd=worktree.path).returncode==0:
                        return ImplementationResult(success=False,provider='codex',model=model or 'CLI-default',returncode=0,stdout_ref=out_ref,stderr_ref=err_ref,transcript_ref=out_ref or err_ref)
                    subprocess.run(['git','-c','user.name=Authorial Flow Repair','-c','user.email=repair@example.invalid','commit','-qm','bounded repair correction'],cwd=worktree.path,check=True)
                    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=worktree.path,text=True).strip()
                    return ImplementationResult(success=True,provider='codex',model=model or 'CLI-default',returncode=0,stdout_ref=out_ref,stderr_ref=err_ref,commit_sha=sha,transcript_ref=out_ref or err_ref)
                attempts.append(result.returncode)
            return ImplementationResult(success=False,provider='codex',returncode=attempts[-1] if attempts else 1)
        finally:
            shutil.rmtree(evidence_dir,ignore_errors=True)

