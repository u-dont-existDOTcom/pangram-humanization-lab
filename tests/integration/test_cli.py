import json
from pathlib import Path
import zipfile

from authorial_flow.cli import parser, format_heartbeat
from authorial_flow.config import RuntimeConfig
from authorial_flow.finalize import build_evidence_package


def test_cli_has_required_commands():
    p=parser()
    text=p.format_help()
    for name in ["run","resume","status","answer","package","publish-results"]:
        assert name in text


def test_heartbeat_contains_operational_fields():
    line=format_heartbeat(
        thread_id="1234567890abcdef", node="generation", phase="writer",
        model="claude/test", pid=42, elapsed=65, retry=2, moves=3,
        last_event="waiting for model",
    )
    for token in ["thread=1234567890ab","node=generation","phase=writer","model=claude/test","pid=42","elapsed=01:05","retry=2","moves=3","waiting for model"]:
        assert token in line


def test_evidence_package_is_runtime_owned_under_state_evidence(tmp_path):
    root=tmp_path
    (root/"policy").mkdir(); (root/"policy"/"MANIFEST.json").write_text('{}')
    (root/"project").mkdir(); (root/"project"/"MANIFEST.json").write_text('{}')
    out=build_evidence_package(RuntimeConfig.from_root(root), reason="bounded-failure")
    assert out.parent == root/".state"/"evidence"
    assert out.name.startswith("AUTHORIAL-FLOW-EVIDENCE-bounded-failure-")
    assert out.is_file()


def test_evidence_package_excludes_venv_and_secret_values(tmp_path):
    root=tmp_path
    (root/"policy").mkdir(); (root/"policy"/"MANIFEST.json").write_text('{}')
    (root/"project").mkdir(); (root/"project"/"MANIFEST.json").write_text('{}')
    state=root/".state"; state.mkdir()
    (state/"events.jsonl").write_text('{"kind":"ok"}\n')
    (state/"candidate.md").write_text('candidate')
    (root/".venv").mkdir(); (root/".venv"/"secret.txt").write_text('PANGRAM_API_KEY=SUPERSECRET')
    out=build_evidence_package(RuntimeConfig.from_root(root), reason="bounded-failure")
    with zipfile.ZipFile(out) as z:
        names=z.namelist()
        assert not any('.venv' in n for n in names)
        blob=b''.join(z.read(n) for n in names if not n.endswith('/'))
        assert b'SUPERSECRET' not in blob
        assert 'SHA256SUMS.txt' in names


def test_run_graph_builds_real_runtime_dependencies(monkeypatch, tmp_path):
    import contextlib
    import authorial_flow.cli as cli

    sentinel_deps = object()
    seen = {}

    def fake_build(config, *, project_root, services):
        seen['config'] = config
        seen['project_root'] = project_root
        seen['services'] = services
        return sentinel_deps

    @contextlib.contextmanager
    def fake_open(config, deps):
        assert deps is sentinel_deps
        class App:
            def invoke(self, initial, graph_config):
                seen['initial'] = initial
                return {'status': 'ok'}
        yield App()

    monkeypatch.setattr(cli, 'build_runtime_dependencies', fake_build)
    monkeypatch.setattr(cli, 'open_graph', fake_open)
    services = object()
    cfg = RuntimeConfig.from_root(tmp_path)
    result = cli._run_graph(cfg, 'thread-x', {'status': 'start'}, services=services)
    assert result['status'] == 'ok'
    assert seen['project_root'] == cfg.root
    assert seen['services'] is services


def test_promoted_code_repair_requests_process_restart_argv(tmp_path):
    import authorial_flow.cli as cli
    cfg=RuntimeConfig.from_root(tmp_path)
    argv=cli.restart_argv(cfg)
    assert argv[0]
    assert argv[-1] == 'resume'
    assert 'run' not in argv
    assert '--root' in argv


def test_maybe_restart_after_code_repair_execs_resume(monkeypatch, tmp_path):
    import authorial_flow.cli as cli
    cfg=RuntimeConfig.from_root(tmp_path)
    source=tmp_path/'source.md'; source.write_text('source')
    cli._write_thread(cfg,'same-thread-id',source)
    before=cli._thread_file(cfg).read_text()
    seen={}
    monkeypatch.setattr(cli.os, 'execv', lambda exe, argv: seen.update(exe=exe, argv=argv))
    result={
        'status':'repair_promoted_restart_required','program_version':'new-program',
        'repair_commit':'repair-sha','failure_evidence_ref':'failure-ref','repair_resume_node':'generation',
    }
    assert cli.maybe_restart_after_repair(cfg,result) is True
    assert seen['argv'][-1] == 'resume'
    assert cli._thread_file(cfg).read_text() == before
    pending=json.loads((cfg.state_dir/'repair-restart-pending.json').read_text())
    assert pending['thread_id'] == 'same-thread-id'
    assert pending['repair_resume_node'] == 'generation'
    assert cli.maybe_restart_after_repair(cfg, {'status':'accepted'}) is False


def test_program_version_contributes_to_thread_identity(monkeypatch, tmp_path):
    import authorial_flow.cli as cli
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(root)
    monkeypatch.setattr(cli,'program_version',lambda root:'commit-a')
    a,_=cli._resolve_thread(cfg,None)
    monkeypatch.setattr(cli,'program_version',lambda root:'commit-b')
    b,_=cli._resolve_thread(cfg,None)
    assert a != b


def test_runtime_prompts_for_pangram_key_once_per_process(monkeypatch):
    import authorial_flow.cli as cli
    monkeypatch.delenv('PANGRAM_API_KEY',raising=False)
    monkeypatch.setattr(cli.sys.stdin,'isatty',lambda: True)
    calls=[]
    monkeypatch.setattr(cli.getpass,'getpass',lambda prompt: calls.append(prompt) or 'secret-key')
    cli.ensure_pangram_key()
    cli.ensure_pangram_key()
    assert calls and len(calls)==1
    assert cli.os.environ['PANGRAM_API_KEY']=='secret-key'



def test_runtime_prompts_for_brave_key_once_per_process(monkeypatch):
    import authorial_flow.cli as cli
    monkeypatch.delenv('BRAVE_SEARCH_API_KEY',raising=False)
    monkeypatch.setattr(cli.sys.stdin,'isatty',lambda: True)
    calls=[]
    monkeypatch.setattr(cli.getpass,'getpass',lambda prompt: calls.append(prompt) or 'brave-key')
    cli.ensure_brave_key()
    cli.ensure_brave_key()
    assert calls and len(calls)==1
    assert cli.os.environ['BRAVE_SEARCH_API_KEY']=='brave-key'


def test_graph_invoking_commands_do_not_prompt_for_pangram_before_detector(monkeypatch, tmp_path):
    import authorial_flow.cli as cli
    cfg=RuntimeConfig.from_root(tmp_path)
    monkeypatch.setattr(cli, "ensure_pangram_key", lambda: (_ for _ in ()).throw(AssertionError("credential prompt must be lazy")))
    monkeypatch.setattr(cli, "_resolve_thread", lambda config, source: ("thread", tmp_path / "source.md"))
    (tmp_path / "source.md").write_text("source")
    monkeypatch.setattr(cli, "_write_thread", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli.RuntimeServices, "from_config", classmethod(lambda cls, config, **kwargs: object()))
    monkeypatch.setattr(cli, "seed_initial_state", lambda *args, **kwargs: {})
    monkeypatch.setattr(cli, "_run_graph", lambda *args, **kwargs: {"status":"ok"})
    monkeypatch.setattr(cli, "_print_result", lambda result: None)
    monkeypatch.setattr(cli, "maybe_restart_after_repair", lambda *args, **kwargs: False)
    cli.command_run(cfg, None)


def test_accepted_result_materializes_text_and_builds_final_package(monkeypatch, tmp_path):
    import authorial_flow.cli as cli
    cfg=RuntimeConfig.from_root(tmp_path)
    cfg.state_dir.mkdir(parents=True)
    packaged=tmp_path/'AUTHORIAL-FLOW-EVIDENCE-final-test.zip'
    monkeypatch.setattr(cli,'build_evidence_package',lambda config,reason: packaged)
    result={'status':'accepted','accepted_moves':['First thought.','Second thought.']}
    final=cli.finalize_if_accepted(cfg,result)
    assert (tmp_path/'RESULT-AUTHORIAL-FLOW.md').read_text()=='First thought. Second thought.\n'
    assert (cfg.state_dir/'final'/'accepted.md').read_text()=='First thought. Second thought.\n'
    assert final['accepted_output_path']==str(tmp_path/'RESULT-AUTHORIAL-FLOW.md')
    assert final['evidence_package_path']==str(packaged)


def test_nonaccepted_result_does_not_build_final_package(monkeypatch,tmp_path):
    import authorial_flow.cli as cli
    cfg=RuntimeConfig.from_root(tmp_path)
    monkeypatch.setattr(cli,'build_evidence_package',lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('must not package')))
    result={'status':'machine_failure','accepted_moves':['x']}
    assert cli.finalize_if_accepted(cfg,result)==result


def test_evidence_package_includes_learning_and_accepted_result(tmp_path):
    root=tmp_path
    (root/'policy').mkdir(); (root/'policy'/'MANIFEST.json').write_text('{}')
    (root/'project').mkdir(); (root/'project'/'MANIFEST.json').write_text('{}')
    state=root/'.state'; (state/'learning'/'bodies').mkdir(parents=True)
    (state/'learning'/'records.jsonl').write_text('{"event":"OWNER_JUDGMENT"}\n')
    (state/'learning'/'bodies'/'abc.json').write_text('{"verdict":"FAIL"}\n')
    (state/'final').mkdir(); (state/'final'/'accepted.md').write_text('accepted\n')
    out=build_evidence_package(RuntimeConfig.from_root(root),reason='final')
    with zipfile.ZipFile(out) as z:
        names=set(z.namelist())
        assert '.state/learning/records.jsonl' in names
        assert '.state/learning/bodies/abc.json' in names
        assert '.state/final/accepted.md' in names


def test_evidence_package_includes_resolved_dependency_lock(tmp_path):
    root=tmp_path
    (root/'policy').mkdir(); (root/'policy'/'MANIFEST.json').write_text('{}')
    (root/'project').mkdir(); (root/'project'/'MANIFEST.json').write_text('{}')
    dep=root/'.state'/'dependencies'; dep.mkdir(parents=True)
    (dep/'requirements.resolved.lock').write_text('pkg==1.0 --hash=sha256:' + 'd'*64 + '\n')
    (dep/'requirements.resolved.json').write_text('{"package_count":1}\n')
    out=build_evidence_package(RuntimeConfig.from_root(root),reason='manual')
    with zipfile.ZipFile(out) as z:
        names=set(z.namelist())
        assert '.state/dependencies/requirements.resolved.lock' in names
        assert '.state/dependencies/requirements.resolved.json' in names


def test_accepted_result_materializes_exact_recommended_candidate_text(monkeypatch,tmp_path):
    import json
    import authorial_flow.cli as cli
    from authorial_flow.artifacts import ArtifactStore
    cfg=RuntimeConfig.from_root(tmp_path)
    store=ArtifactStore(cfg.artifact_dir)
    candidate_text='First paragraph.\n\nSecond paragraph with deliberate spacing.'
    ref=store.put_text(json.dumps({'text':candidate_text}),'json',{'kind':'candidate-record'}).sha256
    monkeypatch.setattr(cli,'build_evidence_package',lambda config,reason: tmp_path/'evidence.zip')
    result={
        'status':'accepted',
        'recommended_candidate_ref':ref,
        'accepted_moves':['First paragraph.','Second paragraph with deliberate spacing.'],
    }
    cli.finalize_if_accepted(cfg,result)
    assert (tmp_path/'RESULT-AUTHORIAL-FLOW.md').read_text()==candidate_text+'\n'



def test_command_resume_consumes_pending_machine_restart_on_same_thread(monkeypatch,tmp_path):
    import authorial_flow.cli as cli
    cfg=RuntimeConfig.from_root(tmp_path)
    source=tmp_path/'source.md'; source.write_text('source')
    cli._write_thread(cfg,'same-thread-id',source)
    pending=cfg.state_dir/'repair-restart-pending.json'
    pending.parent.mkdir(parents=True,exist_ok=True)
    pending.write_text(json.dumps({
        'thread_id':'same-thread-id','source':str(source),'program_version':'new-program',
        'repair_resume_node':'generation','repair_commit':'repair-sha'
    }))
    sentinel=object(); seen={}
    monkeypatch.setattr(cli,'_machine_restart_command',lambda: sentinel)
    monkeypatch.setattr(cli.RuntimeServices,'from_config',classmethod(lambda cls,config,**kwargs: object()))
    def fake_run(config,thread_id,initial,services=None):
        seen['thread_id']=thread_id; seen['initial']=initial
        return {'status':'ok'}
    monkeypatch.setattr(cli,'_run_graph',fake_run)
    monkeypatch.setattr(cli,'maybe_restart_after_repair',lambda *a,**k: False)
    monkeypatch.setattr(cli,'finalize_if_accepted',lambda config,result: result)
    monkeypatch.setattr(cli,'_print_result',lambda result: None)
    cli.command_resume(cfg)
    assert seen == {'thread_id':'same-thread-id','initial':sentinel}
    assert not pending.exists()
    assert json.loads(cli._thread_file(cfg).read_text())['thread_id'] == 'same-thread-id'



def test_bounded_machine_stop_builds_evidence_package_without_owner_interrupt(monkeypatch,tmp_path):
    import authorial_flow.cli as cli
    cfg=RuntimeConfig.from_root(tmp_path)
    packaged=tmp_path/'AUTHORIAL-FLOW-EVIDENCE-bounded.zip'
    calls=[]
    monkeypatch.setattr(cli,'build_evidence_package',lambda config,reason: calls.append(reason) or packaged)
    result={
        'status':'bounded_machine_stop','failure_class':'PROVIDER_PLUMBING',
        'failure_evidence_ref':'failure-ref','authorial_information_missing':False,
    }
    final=cli.finalize_bounded_failure(cfg,result)
    assert final['status'] == 'bounded_machine_stop'
    assert final['evidence_package_path'] == str(packaged)
    assert final['failure_evidence_ref'] == 'failure-ref'
    assert '__interrupt__' not in final
    assert calls == ['bounded-failure']


def test_terminal_bounded_stop_recovery_replays_failed_checkpoint_once_per_program(monkeypatch,tmp_path):
    import contextlib
    from types import SimpleNamespace
    import authorial_flow.cli as cli

    cfg=RuntimeConfig.from_root(tmp_path)
    graph_cfg={'configurable':{'thread_id':'same-thread'}}
    pre_failure=SimpleNamespace(
        next=('generation',),
        config={'configurable':{'thread_id':'same-thread','checkpoint_id':'before-generation'}},
    )
    terminal=SimpleNamespace(next=(),config=graph_cfg)
    calls=[]

    class FakeApp:
        def get_state(self, config):
            return terminal
        def get_state_history(self, config):
            return iter([terminal,pre_failure])
        def invoke(self, initial, config):
            calls.append((initial,config))
            return {'status':'continue_generation','accepted_moves':['preserved'],'section_job':'preserved-job'}

    @contextlib.contextmanager
    def fake_open(config,deps):
        yield FakeApp()

    monkeypatch.setattr(cli,'program_version',lambda root:'new-release-head')
    monkeypatch.setattr(cli,'build_runtime_dependencies',lambda *a,**k: object())
    monkeypatch.setattr(cli,'open_graph',fake_open)
    services=object()
    bounded={
        'status':'bounded_machine_stop','failure_class':'PROVIDER_PLUMBING',
        'failure_origin_node':'generation','repair_attempt':6,
        'accepted_moves':['preserved'],'section_job':'preserved-job',
    }

    recovered=cli.recover_terminal_machine_failure(cfg,'same-thread',bounded,services=services)
    assert recovered['status']=='continue_generation'
    assert recovered['accepted_moves']==['preserved']
    assert calls==[(None,pre_failure.config)]
    markers=list((cfg.state_dir/'bounded-recovery').glob('*.json'))
    assert len(markers)==1
    marker=json.loads(markers[0].read_text())
    assert marker['thread_id']=='same-thread'
    assert marker['program_version']=='new-release-head'
    assert marker['failure_origin_node']=='generation'

    # The same release must not replay an exhausted provider failure forever.
    second=cli.recover_terminal_machine_failure(cfg,'same-thread',bounded,services=services)
    assert second is bounded
    assert len(calls)==1


def test_terminal_bounded_stop_recovery_infers_missing_legacy_origin_from_current_failure_history(monkeypatch,tmp_path):
    import contextlib
    from types import SimpleNamespace
    import authorial_flow.cli as cli

    cfg=RuntimeConfig.from_root(tmp_path)
    graph_cfg={'configurable':{'thread_id':'legacy-thread'}}
    terminal=SimpleNamespace(
        next=(),values={'status':'bounded_machine_stop','phase':'finalized'},config=graph_cfg,
    )
    before_finalize=SimpleNamespace(
        next=('finalize',),
        values={'status':'bounded_machine_stop','phase':'generation'},
        config={'configurable':{'thread_id':'legacy-thread','checkpoint_id':'before-finalize'}},
    )
    failed_generation=SimpleNamespace(
        next=('repair',),
        values={'status':'machine_failure','phase':'generation','failure_class':'GENERATION_DEAD_END'},
        config={'configurable':{'thread_id':'legacy-thread','checkpoint_id':'failed-generation'}},
    )
    before_generation=SimpleNamespace(
        next=('generation',),
        values={'status':'continue_generation','phase':'generation'},
        config={'configurable':{'thread_id':'legacy-thread','checkpoint_id':'before-generation'}},
    )
    older_terminal=SimpleNamespace(
        next=(),
        values={
            'status':'bounded_machine_stop','phase':'finalized',
            'failure_origin_node':'detector',
        },
        config={'configurable':{'thread_id':'legacy-thread','checkpoint_id':'older-terminal'}},
    )
    calls=[]

    class FakeApp:
        def get_state(self, config):
            return terminal
        def get_state_history(self, config):
            return iter([terminal,before_finalize,failed_generation,before_generation,older_terminal])
        def invoke(self, initial, config):
            calls.append((initial,config))
            return {'status':'continue_generation','accepted_moves':['preserved']}

    @contextlib.contextmanager
    def fake_open(config,deps):
        yield FakeApp()

    monkeypatch.setattr(cli,'program_version',lambda root:'origin-inference-fix')
    monkeypatch.setattr(cli,'build_runtime_dependencies',lambda *a,**k: object())
    monkeypatch.setattr(cli,'open_graph',fake_open)
    bounded={
        'status':'bounded_machine_stop','failure_class':'GENERATION_DEAD_END',
        'failure_origin_node':'','accepted_moves':['preserved'],'repair_attempt':6,
    }

    recovered=cli.recover_terminal_machine_failure(
        cfg,'legacy-thread',bounded,services=object(),
    )

    assert recovered['status']=='continue_generation'
    assert recovered['accepted_moves']==['preserved']
    assert calls==[(None,before_generation.config)]
    markers=list((cfg.state_dir/'bounded-recovery').glob('*.json'))
    assert len(markers)==1
    marker=json.loads(markers[0].read_text())
    assert marker['failure_origin_node']=='generation'
    assert marker['checkpoint_id']=='before-generation'


def test_command_resume_attempts_terminal_machine_recovery_before_packaging(monkeypatch,tmp_path):
    import authorial_flow.cli as cli
    cfg=RuntimeConfig.from_root(tmp_path)
    source=tmp_path/'source.md'; source.write_text('source')
    cli._write_thread(cfg,'same-thread-id',source)
    services=object(); seen={}
    bounded={'status':'bounded_machine_stop','failure_origin_node':'generation','failure_class':'PROVIDER_PLUMBING'}
    recovered={'status':'continue_generation'}
    monkeypatch.setattr(cli.RuntimeServices,'from_config',classmethod(lambda cls,config,**kwargs: services))
    monkeypatch.setattr(cli,'_run_graph',lambda *a,**k: (_ for _ in ()).throw(AssertionError('terminal recovery should precede ordinary resume')))
    def fake_recover(config,thread_id,result,*,services):
        seen.update(thread_id=thread_id,result=result,services=services)
        assert result is None
        return recovered
    monkeypatch.setattr(cli,'recover_terminal_machine_failure',fake_recover)
    monkeypatch.setattr(cli,'maybe_restart_after_repair',lambda *a,**k: False)
    monkeypatch.setattr(cli,'finalize_bounded_failure',lambda config,result: result)
    monkeypatch.setattr(cli,'finalize_if_accepted',lambda config,result: result)
    monkeypatch.setattr(cli,'_print_result',lambda result: seen.update(printed=result))

    cli.command_resume(cfg)
    assert seen['thread_id']=='same-thread-id'
    assert seen['result'] is None
    assert seen['services'] is services
    assert seen['printed'] is recovered


def test_current_program_bounded_stop_is_marked_exhausted_for_future_resume(monkeypatch,tmp_path):
    import authorial_flow.cli as cli
    cfg=RuntimeConfig.from_root(tmp_path)
    source=tmp_path/'source.md'; source.write_text('source')
    cli._write_thread(cfg,'same-thread-id',source)
    monkeypatch.setattr(cli,'program_version',lambda root:'current-program')
    monkeypatch.setattr(cli,'build_evidence_package',lambda config,reason: tmp_path/'evidence.zip')
    result={
        'status':'bounded_machine_stop','failure_class':'PROVIDER_PLUMBING',
        'failure_origin_node':'generation','failure_record_ref':'failure-ref',
    }
    cli.finalize_bounded_failure(cfg,result)
    marker=cli._bounded_recovery_marker(cfg,'same-thread-id','current-program')
    assert marker.is_file()
    payload=json.loads(marker.read_text())
    assert payload['reason']=='bounded-stop-observed'
    assert payload['failure_origin_node']=='generation'
