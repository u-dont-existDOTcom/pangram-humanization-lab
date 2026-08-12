import subprocess, sys
from pathlib import Path

from authorial_flow.config import RuntimeConfig
from authorial_flow.repair.worktree import WorktreeManager
from authorial_flow.repair.protection import ProtectedSnapshot
from authorial_flow.repair.schemas import RepairPlan, ReviewDecision
from authorial_flow.repair.verify import RepairVerifier, verify_with_one_fix


class Approver:
    def review_diff(self,plan,diff_text,test_summary=''):
        class R:
            decision=ReviewDecision(verdict='APPROVE',reason='ok',required_changes=[])
            provider='fake'
        return R()


def init_repo(root:Path):
    subprocess.run(['git','init','-q'],cwd=root,check=True)
    subprocess.run(['git','config','user.email','t@example.invalid'],cwd=root,check=True)
    subprocess.run(['git','config','user.name','T'],cwd=root,check=True)
    (root/'src').mkdir(); (root/'tests').mkdir(); (root/'project').mkdir()
    (root/'src'/'ok.py').write_text('VALUE=1\n')
    (root/'tests'/'test_ok.py').write_text('from src.ok import VALUE\ndef test_ok(): assert VALUE==1\n')
    (root/'project'/'INPUT.md').write_text('source')
    subprocess.run(['git','add','.'],cwd=root,check=True); subprocess.run(['git','commit','-qm','base'],cwd=root,check=True)


def test_broken_patch_gets_one_bounded_fix_then_promotes(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir(); init_repo(repo)
    mgr=WorktreeManager(repo,repo/'.state'/'worktrees'); ref=mgr.create('r1')
    (ref.path/'src'/'ok.py').write_text('VALUE =\n')
    subprocess.run(['git','add','.'],cwd=ref.path,check=True); subprocess.run(['git','-c','user.name=R','-c','user.email=r@x','commit','-qm','broken'],cwd=ref.path,check=True)
    broken_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ref.path,text=True).strip()
    ref=type(ref)(ref.repair_id,ref.path,ref.base_commit)
    plan=RepairPlan(repairable=True,diagnosis='syntax',patch_summary='fix syntax',target_files=['src/ok.py'],rationale='general',tests=['pytest'],needs_owner_judgment=False,owner_question='')
    snapshot=ProtectedSnapshot.capture(ref.path,['project/INPUT.md'])
    verifier=RepairVerifier(reviewer=Approver(),source_texts=['source'],protected_snapshot=snapshot,
        commands=[[sys.executable,'-m','compileall','-q','src','tests'],[sys.executable,'-m','pytest','tests','-q']])
    assert verifier.verify(ref,plan).pass_ is False
    def fixer(worktree,failed):
        (worktree.path/'src'/'ok.py').write_text('VALUE=1\n')
        subprocess.run(['git','add','.'],cwd=worktree.path,check=True)
        subprocess.run(['git','-c','user.name=R','-c','user.email=r@x','commit','-qm','fix'],cwd=worktree.path,check=True)
        return subprocess.check_output(['git','rev-parse','HEAD'],cwd=worktree.path,text=True).strip()
    result=verify_with_one_fix(verifier,ref,plan,fixer)
    assert result.pass_ is True
    final_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ref.path,text=True).strip()
    promoted=mgr.promote(ref,final_sha)
    assert promoted == final_sha
    mgr.discard(ref)


def test_repair_budgets_are_bounded(tmp_path):
    cfg=RuntimeConfig.from_root(tmp_path)
    assert cfg.repair_rounds == 5
    assert cfg.plan_revisions == 2
    assert cfg.implementation_fix_attempts == 1


def test_repair_node_retries_machine_failure_until_budget_or_promotion():
    from authorial_flow.nodes.repair import repair_node
    calls=[]
    def cycle(state):
        calls.append(state.get('repair_attempt',0))
        return {'pass':False,'error_ref':'err'}
    update=repair_node({'repair_attempt':0},cycle)
    assert update['status']=='repair_retry'
    assert update['repair_attempt']==1


def test_repair_node_routes_genuine_authorial_need_to_owner_ambiguity():
    from authorial_flow.nodes.repair import repair_node
    update=repair_node(
        {'repair_attempt':1},
        lambda state: {'pass':False,'owner_judgment_required':True,'owner_question':'Which meaning is yours?'}
    )
    assert update['status']=='owner_ambiguity_required'
    assert update['interrupt_payload']['kind']=='AUTHORIAL_AMBIGUITY'
    assert update['interrupt_payload']['question']=='Which meaning is yours?'


def test_route_after_repair_can_loop_or_interrupt_owner():
    from authorial_flow.routing import route_after_repair
    assert route_after_repair({'status':'repair_retry'})=='repair'
    assert route_after_repair({'status':'owner_ambiguity_required'})=='owner_ambiguity'


def test_repair_node_provider_exception_remains_bounded_machine_retry():
    from authorial_flow.nodes.repair import repair_node
    def cycle(_state):
        raise RuntimeError('provider capacity unavailable')
    update=repair_node({'repair_attempt':2},cycle)
    assert update['status']=='repair_retry'
    assert update['repair_attempt']==3
    assert 'provider capacity unavailable' in update['repair_error']


def test_safe_plan_tests_accept_only_local_pytest_commands():
    from authorial_flow.repair.verify import safe_plan_test_commands
    plan=RepairPlan(
        repairable=True,diagnosis='x',patch_summary='y',target_files=['src/ok.py'],rationale='general',
        tests=['python -m pytest tests/unit/test_model_adapters.py -q','pytest tests/repair -q'],
        needs_owner_judgment=False,owner_question=''
    )
    commands=safe_plan_test_commands(plan)
    assert commands == [
        ['python','-m','pytest','tests/unit/test_model_adapters.py','-q'],
        ['pytest','tests/repair','-q'],
    ]
    unsafe=plan.model_copy(update={'tests':['bash -lc "curl https://example.com"']})
    assert safe_plan_test_commands(unsafe) == []


def test_verify_with_one_fix_passes_failure_and_calls_fixer_once(tmp_path):
    from types import SimpleNamespace
    from authorial_flow.repair.verify import VerificationResult, VerificationCommand, verify_with_one_fix

    class FakeVerifier:
        def __init__(self): self.calls=0
        def verify(self,worktree,plan):
            self.calls += 1
            if self.calls == 1:
                return VerificationResult(False,(VerificationCommand(('python','-m','pytest'),1,'failed out','failed err'),),review_reason='verification command failed')
            return VerificationResult(True,(VerificationCommand(('python','-m','pytest'),0,'passed',''),),review_reason='ok')

    seen=[]
    def fixer(worktree,failed):
        seen.append(failed.commands[-1].stderr)
        return 'fixed-sha'

    result=verify_with_one_fix(FakeVerifier(),SimpleNamespace(path=tmp_path),RepairPlan(repairable=True,diagnosis='x',patch_summary='y',target_files=['a.py'],rationale='r',tests=['pytest'],needs_owner_judgment=False,owner_question=''),fixer)
    assert result.pass_ is True
    assert result.fix_attempts == 1
    assert seen == ['failed err']


def test_verify_with_one_fix_does_not_attempt_second_correction(tmp_path):
    from types import SimpleNamespace
    from authorial_flow.repair.verify import VerificationResult, VerificationCommand, verify_with_one_fix

    class AlwaysFail:
        def __init__(self): self.calls=0
        def verify(self,worktree,plan):
            self.calls += 1
            return VerificationResult(False,(VerificationCommand(('pytest',),1,'no','still bad'),),review_reason='fail')

    fixes=[]
    verifier=AlwaysFail()
    result=verify_with_one_fix(
        verifier,SimpleNamespace(path=tmp_path),
        RepairPlan(repairable=True,diagnosis='x',patch_summary='y',target_files=['a.py'],rationale='r',tests=['pytest'],needs_owner_judgment=False,owner_question=''),
        lambda worktree,failed: fixes.append(failed.review_reason) or 'sha',
    )
    assert result.pass_ is False
    assert result.fix_attempts == 1
    assert verifier.calls == 2
    assert fixes == ['fail']


def test_production_repair_cycle_uses_full_evidence_one_fix_and_promotes_corrected_commit(tmp_path,monkeypatch):
    import subprocess
    from types import SimpleNamespace
    from authorial_flow.artifacts import ArtifactStore
    from authorial_flow.runtime import RuntimeServices, _production_repair_cycle
    from authorial_flow.repair.schemas import ImplementationResult, ReviewDecision
    from authorial_flow.repair.verify import VerificationResult, VerificationCommand

    subprocess.run(['git','init','-q'],cwd=tmp_path,check=True)
    subprocess.run(['git','config','user.email','t@example.invalid'],cwd=tmp_path,check=True)
    subprocess.run(['git','config','user.name','T'],cwd=tmp_path,check=True)
    (tmp_path/'project').mkdir(); (tmp_path/'policy').mkdir(); (tmp_path/'src').mkdir(); (tmp_path/'tests').mkdir()
    (tmp_path/'project'/'INPUT.md').write_text('source')
    (tmp_path/'policy'/'RULES.md').write_text('rules')
    (tmp_path/'src'/'x.py').write_text('X=1\n')
    (tmp_path/'tests'/'test_x.py').write_text('def test_x(): assert True\n')
    subprocess.run(['git','add','.'],cwd=tmp_path,check=True); subprocess.run(['git','commit','-qm','base'],cwd=tmp_path,check=True)

    cfg=RuntimeConfig.from_root(tmp_path)
    store=ArtifactStore(cfg.artifact_dir)
    evidence_text='{"format":"authorial-flow-repair-evidence-v1","provider_attempts":[{"stderr_text":"schema mismatch details"}]}'
    evidence_ref=store.put_text(evidence_text,'json',{}).sha256
    services=RuntimeServices.for_tests(claude=object(),codex=object(),pangram=None,artifact_store=store)
    services.runner=object()

    seen={'planner':'','correct':0,'promoted':''}
    plan=RepairPlan(repairable=True,diagnosis='schema',patch_summary='repair',target_files=['src/x.py'],rationale='r',tests=['python -m pytest tests/test_x.py -q'],needs_owner_judgment=False,owner_question='')

    class FakePlanner:
        def __init__(self,**kwargs): pass
        def plan(self,context): seen['planner']=context; return plan
    class FakeReviewer:
        def __init__(self,**kwargs): pass
        def review_plan(self,plan): return SimpleNamespace(decision=ReviewDecision(verdict='APPROVE',reason='ok',required_changes=[]),provider='fake')
        def review_diff(self,*args,**kwargs): return SimpleNamespace(decision=ReviewDecision(verdict='APPROVE',reason='ok',required_changes=[]),provider='fake')
    class FakeExecutor:
        def __init__(self,*args,**kwargs): pass
        def apply(self,ref,plan,runner,store,**kwargs):
            assert 'schema mismatch details' in kwargs['evidence_bundle_text']
            return ImplementationResult(success=True,provider='codex',commit_sha='candidate-sha',transcript_ref='initial-transcript')
        def correct(self,ref,plan,failed,runner,store,**kwargs):
            seen['correct'] += 1
            assert failed.commands[-1].stderr == 'first failure'
            assert kwargs['previous_transcript_refs'] == ['initial-transcript']
            return ImplementationResult(success=True,provider='codex',commit_sha='corrected-sha',transcript_ref='correction-transcript')
    class FakeVerifier:
        def __init__(self,**kwargs): self.calls=0
        def verify(self,ref,plan):
            self.calls += 1
            if self.calls == 1:
                return VerificationResult(False,(VerificationCommand(('pytest',),1,'','first failure'),),review_reason='verification command failed')
            return VerificationResult(True,(VerificationCommand(('pytest',),0,'ok',''),),review_provider='fake',review_reason='ok')
    class FakeManager:
        def __init__(self,*args,**kwargs): pass
        def create(self,repair_id): return SimpleNamespace(repair_id=repair_id,path=tmp_path,base_commit='base-sha')
        def promote(self,ref,sha): seen['promoted']=sha; return sha
        def discard(self,ref): pass

    monkeypatch.setattr('authorial_flow.repair.planner.RepairPlanner',FakePlanner)
    monkeypatch.setattr('authorial_flow.repair.reviewer.RepairReviewer',FakeReviewer)
    monkeypatch.setattr('authorial_flow.repair.executor.RepairExecutor',FakeExecutor)
    monkeypatch.setattr('authorial_flow.repair.verify.RepairVerifier',FakeVerifier)
    monkeypatch.setattr('authorial_flow.repair.worktree.WorktreeManager',FakeManager)
    monkeypatch.setattr('authorial_flow.repair.protection.ProtectedSnapshot.capture',classmethod(lambda cls,root,paths: SimpleNamespace()))

    result=_production_repair_cycle(cfg,tmp_path,services)({
        'repair_attempt':0,'failure_class':'PROVIDER_PLUMBING','failure_origin_node':'generation',
        'failure_record_ref':evidence_ref,'last_error_ref':evidence_ref,'task_mode':'P3','source_provenance':'AI_FROM_OWNER_INPUTS',
        'source_hash':'source','thread_id':'thread-1','authorial_information_missing':False,
    })
    assert 'schema mismatch details' in seen['planner']
    assert seen['correct'] == 1
    assert seen['promoted'] == 'corrected-sha'
    assert result['pass'] is True
    assert result['repair_commit'] == 'corrected-sha'


def test_repair_node_records_original_stage_for_same_thread_restart():
    from authorial_flow.nodes.repair import repair_node
    update=repair_node(
        {'repair_attempt':2,'failure_origin_node':'generation','failure_record_ref':'failure-ref'},
        lambda state:{
            'pass':True,'restart_required':True,'program_version':'new-program','repair_commit':'repair-sha',
            'plan_ref':'plan','test_ref':'tests','review_ref':'review','failure_evidence_ref':'failure-ref',
        },
    )
    assert update['status'] == 'repair_promoted_restart_required'
    assert update['repair_resume_node'] == 'generation'
    assert update['repair_commit'] == 'repair-sha'
    assert update['failure_record_ref'] == 'failure-ref'


def test_route_after_repair_restart_returns_original_machine_stage():
    from authorial_flow.routing import route_after_repair, route_after_repair_restart
    assert route_after_repair({'status':'repair_promoted_restart_required'}) == 'repair_restart'
    assert route_after_repair_restart({'status':'repair_resumed','repair_resume_node':'generation'}) == 'generation'
    assert route_after_repair_restart({'status':'repair_resumed','repair_resume_node':'unknown'}) == 'regressions'



def test_repair_node_exhaustion_preserves_dereferenceable_failure_evidence():
    from authorial_flow.nodes.repair import repair_node
    update=repair_node(
        {'repair_attempt':4,'failure_record_ref':'failure-evidence','failure_class':'PROVIDER_PLUMBING'},
        lambda state:{'pass':False,'exhausted':True,'error_ref':'verification-evidence'},
    )
    assert update['status'] == 'bounded_machine_stop'
    assert update['failure_evidence_ref'] == 'verification-evidence'
    assert update['failure_class'] == 'PROVIDER_PLUMBING'
    assert update['authorial_information_missing'] is False


def test_production_repair_cycle_journals_high_level_repair_phases(tmp_path,monkeypatch):
    import subprocess
    from types import SimpleNamespace
    from authorial_flow.artifacts import ArtifactStore
    from authorial_flow.runtime import RuntimeServices, _production_repair_cycle
    from authorial_flow.repair.schemas import ImplementationResult, ReviewDecision
    from authorial_flow.repair.verify import VerificationResult, VerificationCommand

    subprocess.run(['git','init','-q'],cwd=tmp_path,check=True)
    subprocess.run(['git','config','user.email','t@example.invalid'],cwd=tmp_path,check=True)
    subprocess.run(['git','config','user.name','T'],cwd=tmp_path,check=True)
    for d in ('project','policy','src','tests'): (tmp_path/d).mkdir()
    (tmp_path/'project'/'INPUT.md').write_text('source')
    (tmp_path/'policy'/'RULES.md').write_text('rules')
    (tmp_path/'src'/'x.py').write_text('X=1\n')
    (tmp_path/'tests'/'test_x.py').write_text('def test_x(): assert True\n')
    subprocess.run(['git','add','.'],cwd=tmp_path,check=True); subprocess.run(['git','commit','-qm','base'],cwd=tmp_path,check=True)

    cfg=RuntimeConfig.from_root(tmp_path)
    store=ArtifactStore(cfg.artifact_dir)
    evidence_ref=store.put_text('{"format":"authorial-flow-repair-evidence-v1"}','json',{}).sha256
    events=[]
    class FakeJournal:
        def append(self,kind,payload): events.append((kind,payload)); return len(events)
    services=RuntimeServices.for_tests(claude=object(),codex=object(),pangram=None,artifact_store=store)
    services.runner=object(); services.journal=FakeJournal()
    plan=RepairPlan(repairable=True,diagnosis='schema',patch_summary='repair',target_files=['src/x.py'],rationale='r',tests=['python -m pytest tests/test_x.py -q'],needs_owner_judgment=False,owner_question='')
    class FakePlanner:
        def __init__(self,**kwargs): pass
        def plan(self,context): return plan
    class FakeReviewer:
        def __init__(self,**kwargs): pass
        def review_plan(self,plan): return SimpleNamespace(decision=ReviewDecision(verdict='APPROVE',reason='ok',required_changes=[]),provider='fake')
        def review_diff(self,*a,**k): return SimpleNamespace(decision=ReviewDecision(verdict='APPROVE',reason='ok',required_changes=[]),provider='fake')
    class FakeExecutor:
        def __init__(self,*a,**k): pass
        def apply(self,*a,**k): return ImplementationResult(success=True,provider='codex',commit_sha='candidate',transcript_ref='tr',red_ref='red',green_ref='green')
    class FakeVerifier:
        def __init__(self,**kwargs): pass
        def verify(self,*a,**k): return VerificationResult(True,(VerificationCommand(('pytest',),0,'ok',''),),review_provider='fake',review_reason='ok')
    class FakeManager:
        def __init__(self,*a,**k): pass
        def create(self,repair_id): return SimpleNamespace(repair_id=repair_id,path=tmp_path,base_commit='base')
        def promote(self,ref,sha): return 'promoted'
        def discard(self,ref): pass
    monkeypatch.setattr('authorial_flow.repair.planner.RepairPlanner',FakePlanner)
    monkeypatch.setattr('authorial_flow.repair.reviewer.RepairReviewer',FakeReviewer)
    monkeypatch.setattr('authorial_flow.repair.executor.RepairExecutor',FakeExecutor)
    monkeypatch.setattr('authorial_flow.repair.verify.RepairVerifier',FakeVerifier)
    monkeypatch.setattr('authorial_flow.repair.worktree.WorktreeManager',FakeManager)
    monkeypatch.setattr('authorial_flow.repair.protection.ProtectedSnapshot.capture',classmethod(lambda cls,root,paths: SimpleNamespace()))
    result=_production_repair_cycle(cfg,tmp_path,services)({
        'repair_attempt':0,'failure_class':'PROVIDER_PLUMBING','failure_origin_node':'generation',
        'failure_record_ref':evidence_ref,'source_hash':'source','thread_id':'thread-1','source_provenance':'AI_FROM_OWNER_INPUTS',
    })
    assert result['pass'] is True
    assert {kind for kind,_ in events} == {'repair.state'}
    phases=[payload['phase'] for _,payload in events]
    for required in ['diagnose','plan-review','codex-red','patch','verify-targeted','verify-full','promote']:
        assert required in phases
    assert phases.index('diagnose') < phases.index('plan-review') < phases.index('promote')


def test_dirty_main_worktree_blocks_repair_promotion(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir(); init_repo(repo)
    mgr=WorktreeManager(repo,repo/'.state'/'worktrees'); ref=mgr.create('dirty-main')
    (ref.path/'src'/'ok.py').write_text('VALUE=2\n')
    subprocess.run(['git','add','src/ok.py'],cwd=ref.path,check=True)
    subprocess.run(['git','-c','user.name=R','-c','user.email=r@x','commit','-qm','candidate'],cwd=ref.path,check=True)
    candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ref.path,text=True).strip()
    (repo/'src'/'ok.py').write_text('VALUE=99\n')
    import pytest
    with pytest.raises(RuntimeError,match='dirty'):
        mgr.promote(ref,candidate)
    mgr.discard(ref)


def test_rejected_independent_diff_review_blocks_verification(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir(); init_repo(repo)
    mgr=WorktreeManager(repo,repo/'.state'/'worktrees'); ref=mgr.create('review-reject')
    (ref.path/'src'/'ok.py').write_text('VALUE=1\n# harmless candidate\n')
    subprocess.run(['git','add','src/ok.py'],cwd=ref.path,check=True)
    subprocess.run(['git','-c','user.name=R','-c','user.email=r@x','commit','-qm','candidate'],cwd=ref.path,check=True)
    class Rejector:
        def review_diff(self,plan,diff_text,test_summary=''):
            class R:
                decision=ReviewDecision(verdict='REJECT',reason='unrelated broad refactor',required_changes=['narrow patch'])
                provider='fake'
            return R()
    plan=RepairPlan(repairable=True,diagnosis='x',patch_summary='y',target_files=['src/ok.py'],rationale='r',tests=['pytest tests/test_ok.py -q'],needs_owner_judgment=False,owner_question='')
    verifier=RepairVerifier(
        reviewer=Rejector(),source_texts=['source'],protected_snapshot=ProtectedSnapshot.capture(ref.path,['project/']),
        commands=[[sys.executable,'-m','pytest','tests/test_ok.py','-q']],
    )
    result=verifier.verify(ref,plan)
    assert result.pass_ is False
    assert result.review_reason == 'unrelated broad refactor'
    mgr.discard(ref)
