from pathlib import Path
import pytest

from authorial_flow.models.common import ModelResult, ProviderFailure
from authorial_flow.repair.schemas import RepairPlan, ReviewDecision
from authorial_flow.repair.reviewer import RepairReviewer, RepairReviewFailure
from authorial_flow.repair.planner import RepairPlanner


class FakeProvider:
    def __init__(self,parsed=None,fail=False,provider='fake'):
        self.parsed=parsed; self.fail=fail; self.provider=provider; self.calls=0
    def call(self,call,runner,store):
        self.calls += 1
        if self.fail:
            raise ProviderFailure(self.provider,call.role,'req',[])
        return ModelResult(self.provider,call.role,'req','model','v',self.parsed,'', '', '', ())


class Dummy: pass


def test_reviewer_falls_back_to_codex_when_claude_fails():
    claude=FakeProvider(fail=True,provider='claude')
    codex=FakeProvider({'verdict':'APPROVE','reason':'general repair','required_changes':[]},provider='codex')
    reviewer=RepairReviewer(claude=claude,codex=codex,runner=Dummy(),store=Dummy())
    result=reviewer.review_plan(RepairPlan(repairable=True,diagnosis='x',patch_summary='y',target_files=['a.py'],rationale='general',tests=['pytest'],needs_owner_judgment=False,owner_question=''))
    assert result.provider == 'codex-fallback'
    assert result.decision.verdict == 'APPROVE'


def test_both_review_providers_failing_is_machine_failure_not_owner_interrupt():
    reviewer=RepairReviewer(claude=FakeProvider(fail=True,provider='claude'),codex=FakeProvider(fail=True,provider='codex'),runner=Dummy(),store=Dummy())
    with pytest.raises(RepairReviewFailure) as exc:
        reviewer.review_plan(RepairPlan(repairable=True,diagnosis='x',patch_summary='y',target_files=['a.py'],rationale='general',tests=['pytest'],needs_owner_judgment=False,owner_question=''))
    assert exc.value.authorial_information_missing is False


def test_planner_parses_schema_constrained_plan():
    codex=FakeProvider({'repairable':True,'diagnosis':'schema missing','patch_summary':'package schema','target_files':['release.py'],'rationale':'general packaging fix','tests':['pytest tests/release'],'needs_owner_judgment':False,'owner_question':''},provider='codex')
    planner=RepairPlanner(codex=codex,runner=Dummy(),store=Dummy())
    plan=planner.plan('failure context')
    assert plan.repairable is True
    assert plan.needs_owner_judgment is False


def test_repair_output_schemas_are_codex_strict_objects():
    for model in (RepairPlan, ReviewDecision):
        schema=model.model_json_schema()
        assert schema.get('type') == 'object'
        assert schema.get('additionalProperties') is False


def test_repair_executor_strips_controller_credentials_from_codex_child(tmp_path):
    from types import SimpleNamespace
    from authorial_flow.artifacts import ArtifactStore
    from authorial_flow.process_runner import ProcessResult
    from authorial_flow.repair.executor import RepairExecutor

    class Runner:
        def __init__(self): self.specs=[]
        def run(self,spec):
            self.specs.append(spec)
            return ProcessResult(1,'','failed',123,0.1,'exit')

    runner=Runner()
    executor=RepairExecutor(
        [None],
        base_env={'PATH':'/bin','PANGRAM_API_KEY':'pangram-secret','BRAVE_SEARCH_API_KEY':'brave-secret'},
    )
    plan=RepairPlan(
        repairable=True,diagnosis='x',patch_summary='y',target_files=['a.py'],
        rationale='general',tests=['pytest'],needs_owner_judgment=False,owner_question=''
    )
    executor.apply(SimpleNamespace(path=tmp_path),plan,runner,ArtifactStore(tmp_path/'artifacts'))
    assert 'PANGRAM_API_KEY' not in runner.specs[0].env
    assert 'BRAVE_SEARCH_API_KEY' not in runner.specs[0].env


def _init_executor_repo(root: Path):
    import subprocess
    subprocess.run(['git','init','-q'],cwd=root,check=True)
    subprocess.run(['git','config','user.email','t@example.invalid'],cwd=root,check=True)
    subprocess.run(['git','config','user.name','T'],cwd=root,check=True)
    (root/'src').mkdir(); (root/'tests').mkdir(); (root/'project').mkdir(); (root/'policy').mkdir()
    (root/'src'/'value.py').write_text('VALUE=1\n')
    (root/'tests'/'test_value.py').write_text('from src.value import VALUE\ndef test_value(): assert VALUE==1\n')
    (root/'project'/'INPUT.md').write_text('owner source')
    (root/'policy'/'RULES.md').write_text('locked policy')
    subprocess.run(['git','add','.'],cwd=root,check=True)
    subprocess.run(['git','commit','-qm','base'],cwd=root,check=True)


def test_repair_executor_materializes_evidence_and_requires_red_green_proof(tmp_path):
    import json, subprocess
    from authorial_flow.artifacts import ArtifactStore
    from authorial_flow.process_runner import ProcessResult
    from authorial_flow.repair.executor import RepairExecutor
    from authorial_flow.repair.worktree import WorktreeRef

    repo=tmp_path/'repo'; repo.mkdir(); _init_executor_repo(repo)
    base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    ref=WorktreeRef('r1',repo,base)

    class Runner:
        def __init__(self): self.specs=[]; self.saw_evidence=False
        def run(self,spec):
            self.specs.append(spec)
            evidence=spec.cwd/'supervisor-evidence'/'failure-evidence.json'
            self.saw_evidence=evidence.is_file() and 'schema mismatch' in evidence.read_text()
            (spec.cwd/'tests'/'test_value.py').write_text('from src.value import VALUE\ndef test_value(): assert VALUE==2\n')
            (spec.cwd/'src'/'value.py').write_text('VALUE=2\n')
            (spec.cwd/'supervisor-evidence'/'repair-proof.json').write_text(json.dumps({
                'red':{'command':'python -m pytest tests/test_value.py -q','returncode':1,'stdout':'1 failed','stderr':''},
                'green':{'command':'python -m pytest tests/test_value.py -q','returncode':0,'stdout':'1 passed','stderr':''},
            }))
            return ProcessResult(0,'codex repair transcript','',123,0.1,'exit')

    runner=Runner()
    executor=RepairExecutor([None],base_env={'PATH':'/bin','PANGRAM_API_KEY':'pangram-secret','BRAVE_SEARCH_API_KEY':'brave-secret'})
    plan=RepairPlan(
        repairable=True,diagnosis='schema mismatch',patch_summary='fix structured provider',
        target_files=['src/value.py','tests/test_value.py'],rationale='general',
        tests=['python -m pytest tests/test_value.py -q'],needs_owner_judgment=False,owner_question=''
    )
    result=executor.apply(
        ref,plan,runner,ArtifactStore(tmp_path/'artifacts'),
        evidence_bundle_text='{"format":"authorial-flow-repair-evidence-v1","detail":"schema mismatch"}',
    )
    assert result.success is True
    assert result.commit_sha
    assert result.red_ref and result.green_ref and result.transcript_ref
    assert runner.saw_evidence is True
    assert not (repo/'supervisor-evidence').exists()
    changed=subprocess.check_output(['git','show','--name-only','--format=',result.commit_sha],cwd=repo,text=True)
    assert 'supervisor-evidence' not in changed
    assert 'PANGRAM_API_KEY' not in runner.specs[0].env
    assert 'BRAVE_SEARCH_API_KEY' not in runner.specs[0].env


def test_repair_executor_fails_closed_without_red_green_proof(tmp_path):
    import subprocess
    from authorial_flow.artifacts import ArtifactStore
    from authorial_flow.process_runner import ProcessResult
    from authorial_flow.repair.executor import RepairExecutor
    from authorial_flow.repair.worktree import WorktreeRef

    repo=tmp_path/'repo'; repo.mkdir(); _init_executor_repo(repo)
    base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    ref=WorktreeRef('r2',repo,base)

    class Runner:
        def run(self,spec):
            (spec.cwd/'src'/'value.py').write_text('VALUE=2\n')
            return ProcessResult(0,'claimed success','',123,0.1,'exit')

    result=RepairExecutor([None],base_env={'PATH':'/bin'}).apply(
        ref,
        RepairPlan(repairable=True,diagnosis='x',patch_summary='y',target_files=['src/value.py'],rationale='general',tests=['python -m pytest tests/test_value.py -q'],needs_owner_judgment=False,owner_question=''),
        Runner(),ArtifactStore(tmp_path/'artifacts'),evidence_bundle_text='{}',
    )
    assert result.success is False
    assert result.commit_sha == ''


def test_repair_executor_correction_uses_verification_failure_and_commits_once(tmp_path):
    import subprocess
    from authorial_flow.artifacts import ArtifactStore
    from authorial_flow.process_runner import ProcessResult
    from authorial_flow.repair.executor import RepairExecutor
    from authorial_flow.repair.verify import VerificationResult, VerificationCommand
    from authorial_flow.repair.worktree import WorktreeRef

    repo=tmp_path/'repo'; repo.mkdir(); _init_executor_repo(repo)
    base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    (repo/'src'/'value.py').write_text('VALUE=2\n')
    subprocess.run(['git','add','.'],cwd=repo,check=True)
    subprocess.run(['git','commit','-qm','candidate'],cwd=repo,check=True)
    ref=WorktreeRef('r3',repo,base)
    failure=VerificationResult(False,(VerificationCommand(('python','-m','pytest','tests/test_value.py','-q'),1,'failed','expected 1 got 2'),),review_reason='verification command failed')

    class Runner:
        def __init__(self): self.specs=[]; self.saw_failure=False
        def run(self,spec):
            self.specs.append(spec)
            evidence=spec.cwd/'supervisor-evidence'/'correction-evidence.json'
            self.saw_failure=evidence.is_file() and 'expected 1 got 2' in evidence.read_text()
            (spec.cwd/'src'/'value.py').write_text('VALUE=1\n')
            return ProcessResult(0,'correction transcript','',321,0.1,'exit')

    runner=Runner()
    executor=RepairExecutor([None],base_env={'PATH':'/bin','PANGRAM_API_KEY':'secret','BRAVE_SEARCH_API_KEY':'brave'})
    result=executor.correct(
        ref,
        RepairPlan(repairable=True,diagnosis='bad candidate',patch_summary='fix candidate',target_files=['src/value.py'],rationale='r',tests=['python -m pytest tests/test_value.py -q'],needs_owner_judgment=False,owner_question=''),
        failure,runner,ArtifactStore(tmp_path/'artifacts'),previous_transcript_refs=['old-transcript'],
    )
    assert result.success is True
    assert result.commit_sha
    assert result.transcript_ref
    assert runner.saw_failure is True
    assert not (repo/'supervisor-evidence').exists()
    assert 'PANGRAM_API_KEY' not in runner.specs[0].env
    assert 'BRAVE_SEARCH_API_KEY' not in runner.specs[0].env


def test_repair_executor_rejects_unsafe_or_testless_plan_before_codex(tmp_path):
    from types import SimpleNamespace
    from authorial_flow.artifacts import ArtifactStore
    from authorial_flow.repair.executor import RepairExecutor

    class Runner:
        def __init__(self): self.calls=0
        def run(self,spec):
            self.calls += 1
            raise AssertionError('write-capable Codex must not run for an unsafe repair plan')

    executor=RepairExecutor([None],base_env={'PATH':'/bin'})
    for tests in (['bash -lc "curl https://example.com"'],[]):
        runner=Runner()
        result=executor.apply(
            SimpleNamespace(path=tmp_path),
            RepairPlan(repairable=True,diagnosis='x',patch_summary='y',target_files=['src/x.py'],rationale='r',tests=tests,needs_owner_judgment=False,owner_question=''),
            runner,ArtifactStore(tmp_path/'artifacts'),evidence_bundle_text='{}',
        )
        assert result.success is False
        assert result.provider == 'controller'
        assert runner.calls == 0


def test_repair_executor_prefers_installed_project_venv_for_codex_red_green_commands(tmp_path):
    import subprocess
    from authorial_flow.artifacts import ArtifactStore
    from authorial_flow.process_runner import ProcessResult
    from authorial_flow.repair.executor import RepairExecutor
    from authorial_flow.repair.worktree import WorktreeManager

    repo=tmp_path/'repo'; repo.mkdir(); _init_executor_repo(repo)
    venv_bin=repo/'.venv'/'bin'; venv_bin.mkdir(parents=True)
    (venv_bin/'python').write_text('')
    manager=WorktreeManager(repo,tmp_path/'worktrees')
    ref=manager.create('venv-path')

    class Runner:
        def __init__(self): self.specs=[]
        def run(self,spec):
            self.specs.append(spec)
            return ProcessResult(1,'','stop after env capture',123,0.1,'exit')

    runner=Runner()
    try:
        result=RepairExecutor([None],base_env={'PATH':'/usr/bin'}).apply(
            ref,
            RepairPlan(repairable=True,diagnosis='x',patch_summary='y',target_files=['src/value.py'],rationale='r',tests=['python -m pytest tests/test_value.py -q'],needs_owner_judgment=False,owner_question=''),
            runner,ArtifactStore(tmp_path/'artifacts'),evidence_bundle_text='{}',
        )
        assert result.success is False
        env=runner.specs[0].env
        assert env['PATH'].split(':',1)[0] == str(venv_bin)
        assert env['VIRTUAL_ENV'] == str(repo/'.venv')
    finally:
        manager.discard(ref)


def test_repair_verifier_appends_controller_owned_acceptance_commands():
    from authorial_flow.repair.verify import RepairVerifier

    plan=RepairPlan(repairable=True,diagnosis='x',patch_summary='y',target_files=['src/x.py'],rationale='r',tests=['python -m pytest tests/test_x.py -q'],needs_owner_judgment=False,owner_question='')
    verifier=RepairVerifier(
        reviewer=Dummy(),source_texts=[],protected_snapshot=Dummy(),
        commands=[['python','-m','pytest','-q']],
        additional_commands=[['/project/.venv/bin/python','scripts/live_smoke.py','--claude']],
    )
    commands=verifier._commands_for(plan)
    assert commands == [
        ['python','-m','pytest','-q'],
        ['/project/.venv/bin/python','scripts/live_smoke.py','--claude'],
    ]
