from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.config import RuntimeConfig


def _root(tmp_path: Path) -> Path:
    root=tmp_path/'repo'; root.mkdir()
    (root/'project').mkdir()
    (root/'project'/'INPUT.md').write_text('source text\n',encoding='utf-8')
    return root


class Result:
    def __init__(self, returncode:int, stdout:str='', stderr:str=''):
        self.returncode=returncode; self.stdout=stdout; self.stderr=stderr


def test_bootstrap_preflight_repairs_failed_suite_then_reruns_exact_command(tmp_path):
    from authorial_flow.bootstrap_repair import run_preflight

    root=_root(tmp_path); cfg=RuntimeConfig.from_root(root)
    store=ArtifactStore(cfg.artifact_dir)
    services=SimpleNamespace(artifact_store=store, journal=None)
    calls=[]
    results=[Result(1,'FAILED test_x','traceback'),Result(0,'206 passed','')]

    def command_runner(command,cwd):
        calls.append((tuple(command),Path(cwd)))
        return results.pop(0)

    cycle_states=[]
    def factory(config,project_root,got_services):
        assert config == cfg and Path(project_root) == root and got_services is services
        def cycle(state):
            cycle_states.append(dict(state))
            evidence=store.find(state['failure_record_ref'])
            assert evidence is not None
            payload=json.loads(evidence.path.read_text(encoding='utf-8'))
            assert payload['command'] == ['.venv/bin/python','-m','pytest','-q']
            assert payload['returncode'] == 1
            assert 'FAILED test_x' in payload['stdout']
            assert 'traceback' in payload['stderr']
            return {'pass':True,'repair_commit':'fixed-sha','program_version':'fixed-sha'}
        return cycle

    packaged=[]
    rc=run_preflight(
        cfg,['.venv/bin/python','-m','pytest','-q'],services=services,
        repair_cycle_factory=factory,command_runner=command_runner,
        package_builder=lambda *args,**kwargs: packaged.append(True) or root/'evidence.zip',
    )
    assert rc == 0
    assert [c[0] for c in calls] == [
        ('.venv/bin/python','-m','pytest','-q'),
        ('.venv/bin/python','-m','pytest','-q'),
    ]
    assert len(cycle_states) == 1
    assert cycle_states[0]['failure_class'] == 'REGRESSION_ARCHITECTURE'
    assert cycle_states[0]['failure_origin_node'] == 'regressions'
    assert cycle_states[0]['source_ref']
    assert packaged == []


def test_bootstrap_preflight_exhaustion_packages_evidence_without_owner_courier(tmp_path,capsys):
    from authorial_flow.bootstrap_repair import run_preflight

    root=_root(tmp_path); cfg=RuntimeConfig.from_root(root)
    store=ArtifactStore(cfg.artifact_dir)
    services=SimpleNamespace(artifact_store=store, journal=None)
    results=[Result(1,'FAILED','machine traceback')]

    def command_runner(command,cwd):
        return results[0]

    def factory(config,project_root,got_services):
        return lambda state: {'pass':False,'exhausted':True,'error_ref':state['failure_record_ref']}

    package=root/'AUTHORIAL-FLOW-EVIDENCE-bounded-failure-test.zip'
    packaged=[]
    rc=run_preflight(
        cfg,['.venv/bin/python','-m','pytest','-q'],services=services,
        repair_cycle_factory=factory,command_runner=command_runner,
        package_builder=lambda config,reason: packaged.append((config,reason)) or package,
    )
    out=capsys.readouterr().out
    assert rc != 0
    assert packaged == [(cfg,'bounded-failure')]
    assert str(package) in out
    assert 'paste' not in out.lower()
    assert 'upload the logs' not in out.lower()


def test_bootstrap_preflight_passes_without_invoking_repair(tmp_path):
    from authorial_flow.bootstrap_repair import run_preflight

    root=_root(tmp_path); cfg=RuntimeConfig.from_root(root)
    store=ArtifactStore(cfg.artifact_dir)
    services=SimpleNamespace(artifact_store=store,journal=None)
    called=[]
    rc=run_preflight(
        cfg,['python','-m','pytest','-q'],services=services,
        repair_cycle_factory=lambda *args: called.append(True),
        command_runner=lambda command,cwd: Result(0,'all green',''),
        package_builder=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('must not package')),
    )
    assert rc == 0
    assert called == []


def test_bootstrap_preflight_captures_live_smoke_report_and_provider_metadata(tmp_path,monkeypatch):
    from authorial_flow.bootstrap_repair import run_preflight

    root=_root(tmp_path); cfg=RuntimeConfig.from_root(root)
    store=ArtifactStore(cfg.artifact_dir)
    services=SimpleNamespace(artifact_store=store, journal=None)
    report=root/'.state'/'live-smoke'/'install-report.json'
    report.parent.mkdir(parents=True)
    monkeypatch.setenv('ANTHROPIC_API_KEY','top-secret-value')
    report.write_text(json.dumps({
        'format':'authorial-flow-live-smoke-v1',
        'results':{'claude':{'status':'fail','detail':'schema mismatch top-secret-value'}},
    }),encoding='utf-8')
    results=[Result(2,'live_smoke_report=.state/live-smoke/install-report.json\n',''),Result(0,'live_smoke_report=.state/live-smoke/install-report.json\n','')]

    def command_runner(command,cwd):
        return results.pop(0)

    seen=[]
    def factory(config,project_root,got_services):
        def cycle(state):
            evidence=store.find(state['failure_record_ref'])
            assert evidence is not None
            payload=json.loads(evidence.path.read_text(encoding='utf-8'))
            seen.append(payload)
            assert payload['phase'] == 'installer-live-smoke'
            assert payload['failure_class'] == 'PROVIDER_PLUMBING'
            assert payload['originating_node'] == 'provider-smoke'
            assert payload['evidence_file']['path'].endswith('install-report.json')
            assert payload['evidence_file']['sha256']
            assert 'schema mismatch' in payload['evidence_file']['content']
            assert 'top-secret-value' not in payload['evidence_file']['content']
            assert '[REDACTED]' in payload['evidence_file']['content']
            assert state['failure_class'] == 'PROVIDER_PLUMBING'
            assert state['failure_origin_node'] == 'provider-smoke'
            assert state['source_provenance'] == 'INSTALLER_LIVE_SMOKE'
            return {'pass':True,'repair_commit':'fixed-sha','program_version':'fixed-sha'}
        return cycle

    rc=run_preflight(
        cfg,['.venv/bin/python','scripts/live_smoke.py','--claude'],services=services,
        repair_cycle_factory=factory,command_runner=command_runner,
        phase='installer-live-smoke',failure_class='PROVIDER_PLUMBING',
        originating_node='provider-smoke',source_provenance='INSTALLER_LIVE_SMOKE',
        evidence_file=report,
        package_builder=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('must not package')),
    )
    assert rc == 0
    assert len(seen) == 1


def test_bootstrap_repair_controller_exception_packages_evidence_instead_of_crashing(tmp_path,capsys):
    from authorial_flow.bootstrap_repair import run_preflight

    root=_root(tmp_path); cfg=RuntimeConfig.from_root(root)
    store=ArtifactStore(cfg.artifact_dir)
    services=SimpleNamespace(artifact_store=store, journal=None)
    report=root/'.state'/'live-smoke'/'install-report.json'
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({'results':{'codex':{'status':'fail','detail':'codex unavailable'}}}),encoding='utf-8')

    def factory(config,project_root,got_services):
        def cycle(state):
            raise RuntimeError('Codex CLI unavailable during repair')
        return cycle

    package=root/'AUTHORIAL-FLOW-EVIDENCE-bounded-failure-test.zip'
    rc=run_preflight(
        cfg,['.venv/bin/python','scripts/live_smoke.py','--codex'],services=services,
        repair_cycle_factory=factory,command_runner=lambda command,cwd: Result(2,'live_smoke_report=x\n',''),
        phase='installer-live-smoke',failure_class='PROVIDER_PLUMBING',
        originating_node='provider-smoke',source_provenance='INSTALLER_LIVE_SMOKE',evidence_file=report,
        package_builder=lambda config,reason: package,
    )
    captured=capsys.readouterr()
    assert rc != 0
    assert 'bootstrap_repair_controller_error=' in captured.err
    assert 'Codex CLI unavailable during repair' in captured.err
    assert f'bootstrap_repair_evidence={package}' in captured.out


def test_live_smoke_bootstrap_requests_exact_command_as_pre_promotion_acceptance_gate(tmp_path):
    from authorial_flow.bootstrap_repair import run_preflight

    root=_root(tmp_path); cfg=RuntimeConfig.from_root(root)
    venv_python=root/'.venv'/'bin'/'python'; venv_python.parent.mkdir(parents=True); venv_python.write_text('')
    store=ArtifactStore(cfg.artifact_dir)
    services=SimpleNamespace(artifact_store=store,journal=None)
    report=root/'.state'/'live-smoke'/'install-report.json'; report.parent.mkdir(parents=True); report.write_text('{}')
    states=[]
    def factory(config,project_root,got_services):
        def cycle(state):
            states.append(dict(state)); return {'pass':False,'exhausted':True,'error_ref':state['failure_record_ref']}
        return cycle
    run_preflight(
        cfg,['.venv/bin/python','scripts/live_smoke.py','--claude','--out','.state/live-smoke/install-report.json'],
        services=services,repair_cycle_factory=factory,
        command_runner=lambda command,cwd: Result(2,'failed',''),
        phase='installer-live-smoke',failure_class='PROVIDER_PLUMBING',originating_node='provider-smoke',
        source_provenance='INSTALLER_LIVE_SMOKE',evidence_file=report,verify_before_promotion=True,
        package_builder=lambda config,reason: root/'evidence.zip',
    )
    assert len(states)==1
    acceptance=states[0]['repair_acceptance_commands']
    assert len(acceptance)==1
    assert acceptance[0][0] == str(venv_python.resolve())
    assert acceptance[0][1:] == ['scripts/live_smoke.py','--claude','--out','.state/live-smoke/install-report.json']


def test_bootstrap_live_smoke_credential_failure_skips_codex_repair(tmp_path,capsys):
    from authorial_flow.bootstrap_repair import run_preflight

    root=_root(tmp_path); cfg=RuntimeConfig.from_root(root)
    store=ArtifactStore(cfg.artifact_dir)
    services=SimpleNamespace(artifact_store=store,journal=None)
    report=root/'.state'/'live-smoke'/'install-report.json'; report.parent.mkdir(parents=True)
    report.write_text(json.dumps({
        'format':'authorial-flow-live-smoke-v1',
        'credential_required':'PANGRAM_API_KEY',
        'credential_status_code':401,
        'error':{'type':'HTTPStatusError','message':'401 Unauthorized'},
    }),encoding='utf-8')
    repair_calls=[]

    rc=run_preflight(
        cfg,['.venv/bin/python','scripts/live_smoke.py','--pangram'],services=services,
        repair_cycle_factory=lambda *args: repair_calls.append(True),
        command_runner=lambda command,cwd: Result(3,'live_smoke_report=x\n','credential required\n'),
        phase='installer-live-smoke',failure_class='PROVIDER_PLUMBING',originating_node='provider-smoke',
        source_provenance='INSTALLER_LIVE_SMOKE',evidence_file=report,
        package_builder=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('credential refresh is not code repair')),
    )
    captured=capsys.readouterr()
    assert rc == 3
    assert repair_calls == []
    assert 'bootstrap_credential_required=PANGRAM_API_KEY' in captured.err


def test_bootstrap_live_smoke_payment_required_skips_codex_repair(tmp_path,capsys):
    from authorial_flow.bootstrap_repair import run_preflight

    root=_root(tmp_path); cfg=RuntimeConfig.from_root(root)
    store=ArtifactStore(cfg.artifact_dir)
    services=SimpleNamespace(artifact_store=store,journal=None)
    report=root/'.state'/'live-smoke'/'install-report.json'; report.parent.mkdir(parents=True)
    report.write_text(json.dumps({
        'format':'authorial-flow-live-smoke-v1',
        'account_action_required':'PANGRAM_CREDITS',
        'account_status_code':402,
        'error':{'type':'HTTPStatusError','message':'402 Payment Required'},
    }),encoding='utf-8')
    repair_calls=[]

    rc=run_preflight(
        cfg,['.venv/bin/python','scripts/live_smoke.py','--pangram'],services=services,
        repair_cycle_factory=lambda *args: repair_calls.append(True),
        command_runner=lambda command,cwd: Result(4,'live_smoke_report=x\n','account action required\n'),
        phase='installer-live-smoke',failure_class='PROVIDER_PLUMBING',originating_node='provider-smoke',
        source_provenance='INSTALLER_LIVE_SMOKE',evidence_file=report,
        package_builder=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('credits are not code repair')),
    )
    captured=capsys.readouterr()
    assert rc == 4
    assert repair_calls == []
    assert 'bootstrap_account_action_required=PANGRAM_CREDITS' in captured.err
