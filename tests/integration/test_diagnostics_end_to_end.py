from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

from authorial_flow.config import RuntimeConfig
from authorial_flow.diagnostics import (
    DIAGNOSTICS_BRANCH,
    build_diagnostic_record,
    load_queued_diagnostics,
    queue_diagnostic,
    safely_publish_diagnostic,
)


def _thread(config: RuntimeConfig, source: Path) -> None:
    import authorial_flow.cli as cli

    source.write_text("source\n", encoding="utf-8")
    cli._write_thread(config, "a" * 64, source)


def _publication() -> SimpleNamespace:
    return SimpleNamespace(
        status="queued", run_id="b" * 64, branch="diagnostics/authorial-flow-graph-v1",
        queued_count=1, commit_sha="", failure_kind="REMOTE_MISSING", attempts=0,
    )


def _git(path: Path, *args: str, git_dir: bool = False) -> str:
    command = ["git"]
    command.extend(["--git-dir", str(path)] if git_dir else ["-C", str(path)])
    command.extend(args)
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def test_run_publishes_finalized_accepted_result_before_printing(monkeypatch, tmp_path):
    import authorial_flow.cli as cli

    cfg=RuntimeConfig.from_root(tmp_path)
    source=tmp_path/'source.md'
    source.write_text('source\n',encoding='utf-8')
    publications=[]; order=[]
    monkeypatch.setattr(cli,'_resolve_thread',lambda config,source_arg:('a'*64,source))
    monkeypatch.setattr(cli.RuntimeServices,'from_config',classmethod(lambda cls,config,**kwargs: object()))
    monkeypatch.setattr(cli,'seed_initial_state',lambda *args,**kwargs:{})
    monkeypatch.setattr(cli,'_run_graph',lambda *args,**kwargs:{'status':'accepted','accepted_moves':['PRIVATE PROSE']})
    monkeypatch.setattr(cli,'finalize_if_accepted',lambda config,result:{**result,'evidence_package_path':'/private/final.zip'})
    monkeypatch.setattr(cli,'finalize_bounded_failure',lambda config,result:result)
    monkeypatch.setattr(cli,'safely_publish_diagnostic',lambda *args,**kwargs: publications.append(kwargs) or order.append('publish') or _publication())
    monkeypatch.setattr(cli,'maybe_restart_after_repair',lambda *args,**kwargs: order.append('restart') or False)
    monkeypatch.setattr(cli,'_print_result',lambda result:order.append('print'))

    assert cli.command_run(cfg,None) == 0
    assert order == ['publish','restart','print']
    assert publications[0]['phase'] == 'runtime-run'
    assert publications[0]['outcome'] == 'accepted'
    assert publications[0]['result']['evidence_package_path'] == '/private/final.zip'


def test_resume_publishes_bounded_stop_and_answer_publishes_supervisor_pause(monkeypatch,tmp_path):
    import authorial_flow.cli as cli

    cfg=RuntimeConfig.from_root(tmp_path)
    source=tmp_path/'source.md'; _thread(cfg,source)
    publications=[]
    monkeypatch.setattr(cli.RuntimeServices,'from_config',classmethod(lambda cls,config,**kwargs: object()))
    monkeypatch.setattr(cli,'recover_terminal_machine_failure',lambda *args,**kwargs:{'status':'bounded_machine_stop','failure_class':'GENERATION_DEAD_END'})
    monkeypatch.setattr(cli,'finalize_bounded_failure',lambda config,result:{**result,'evidence_package_path':'/private/bounded.zip'})
    monkeypatch.setattr(cli,'finalize_if_accepted',lambda config,result:result)
    monkeypatch.setattr(cli,'safely_publish_diagnostic',lambda *args,**kwargs: publications.append(kwargs) or _publication())
    monkeypatch.setattr(cli,'maybe_restart_after_repair',lambda *args,**kwargs:False)
    monkeypatch.setattr(cli,'_print_result',lambda result:None)
    cli.command_resume(cfg)
    assert publications[-1]['phase'] == 'runtime-resume'
    assert publications[-1]['outcome'] == 'bounded_machine_stop'

    supervisor={'__interrupt__':[SimpleNamespace(value={'kind':'SUPERVISOR_PAUSE'})]}
    monkeypatch.setattr(cli,'_run_graph',lambda *args,**kwargs:supervisor)
    monkeypatch.setattr(cli,'_supervisor_interrupt',lambda result:{'kind':'SUPERVISOR_PAUSE'})
    cli.command_answer(cfg,json.dumps({'kind':'RESUME_UNCHANGED'}))
    assert publications[-1]['phase'] == 'runtime-answer'
    assert publications[-1]['outcome'] == 'supervisor_paused'


def test_publish_results_builds_snapshot_flushes_queue_and_prints_content_free_status(monkeypatch,tmp_path,capsys):
    import authorial_flow.cli as cli

    cfg=RuntimeConfig.from_root(tmp_path)
    source=tmp_path/'source.md'; _thread(cfg,source)
    calls=[]
    monkeypatch.setattr(cli,'safely_publish_diagnostic',lambda *args,**kwargs:calls.append(kwargs) or _publication())
    rc=cli.command_publish_results(cfg)
    captured=capsys.readouterr()
    assert rc == 2
    assert calls[0]['phase'] == 'manual-status'
    assert calls[0]['outcome'] == 'snapshot'
    assert 'diagnostics_status=queued' in captured.out
    assert '/private/' not in captured.out
    assert 'source.md' not in captured.out


def test_repair_restart_is_published_before_exec_boundary(monkeypatch,tmp_path):
    import authorial_flow.cli as cli

    cfg=RuntimeConfig.from_root(tmp_path)
    source=tmp_path/'source.md'; _thread(cfg,source)
    order=[]
    monkeypatch.setattr(cli.RuntimeServices,'from_config',classmethod(lambda cls,config,**kwargs: object()))
    monkeypatch.setattr(cli,'recover_terminal_machine_failure',lambda *args,**kwargs:{'status':'repair_promoted_restart_required','repair_commit':'c'*40})
    monkeypatch.setattr(cli,'finalize_bounded_failure',lambda config,result:result)
    monkeypatch.setattr(cli,'finalize_if_accepted',lambda config,result:result)
    monkeypatch.setattr(cli,'safely_publish_diagnostic',lambda *args,**kwargs:order.append('publish') or _publication())
    monkeypatch.setattr(cli,'maybe_restart_after_repair',lambda *args,**kwargs:order.append('exec') or True)
    monkeypatch.setattr(cli,'_print_result',lambda result:order.append('print'))
    cli.command_resume(cfg)
    assert order == ['publish','exec','print']


def test_interruption_queues_without_network_and_reports_total_queue_count(tmp_path,capsys):
    import authorial_flow.cli as cli

    cfg=RuntimeConfig.from_root(tmp_path)
    source=tmp_path/'PRIVATE-SOURCE-NAME.md'; _thread(cfg,source)
    existing=build_diagnostic_record(cfg,phase='manual-status',outcome='snapshot',now=1.0)
    queue_diagnostic(cfg,existing)
    cli._queue_interrupted_diagnostic(cfg)
    output=capsys.readouterr().out
    queued=load_queued_diagnostics(cfg)
    assert len(queued) == 2
    assert 'diagnostics_status=queued' in output
    assert 'queued=2' in output
    assert 'PRIVATE-SOURCE-NAME' not in output


def test_run_wrapper_routes_publish_results_to_installed_cli(tmp_path):
    source_root=Path(__file__).resolve().parents[2]
    shutil.copy2(source_root/'RUN.sh',tmp_path/'RUN.sh')
    executable=tmp_path/'.venv'/'bin'/'authorial-flow'; executable.parent.mkdir(parents=True)
    executable.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$*" > invoked.txt\n',encoding='utf-8')
    executable.chmod(0o755)
    result=subprocess.run([str(tmp_path/'RUN.sh'),'publish-results'],cwd=tmp_path,text=True,capture_output=True)
    assert result.returncode == 0
    assert (tmp_path/'invoked.txt').read_text(encoding='utf-8') == 'publish-results\n'


def test_manual_cli_boundary_creates_real_diagnostics_branch_without_touching_source(
    monkeypatch, tmp_path, capsys,
):
    import authorial_flow.cli as cli

    source = tmp_path / "source"
    remote = tmp_path / "diagnostics.git"
    source.mkdir()
    _git(source, "init", "-b", "install/authorial-flow-graph-v1-1.3.0-dev1")
    _git(source, "config", "user.name", "Test User")
    _git(source, "config", "user.email", "test@example.invalid")
    (source / ".gitignore").write_text(".state/\n", encoding="utf-8")
    (source / "source.txt").write_text("PRIVATE SOURCE SENTINEL\n", encoding="utf-8")
    _git(source, "add", ".gitignore", "source.txt")
    _git(source, "commit", "-m", "source baseline")
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
    cfg = RuntimeConfig.from_root(source)
    before_head = _git(source, "rev-parse", "HEAD")
    before_status = _git(source, "status", "--porcelain=v1", "--untracked-files=all")

    def local_publish(config, **kwargs):
        return safely_publish_diagnostic(
            config, **kwargs, remote_url=str(remote), branch=DIAGNOSTICS_BRANCH,
            timeout_seconds=10,
        )

    monkeypatch.setattr(cli, "safely_publish_diagnostic", local_publish)
    assert cli.command_publish_results(cfg) == 0

    output = capsys.readouterr().out
    assert "diagnostics_status=published" in output
    assert "PRIVATE SOURCE SENTINEL" not in output
    assert _git(source, "rev-parse", "HEAD") == before_head
    assert _git(source, "status", "--porcelain=v1", "--untracked-files=all") == before_status
    latest = json.loads(_git(remote, "show", f"{DIAGNOSTICS_BRANCH}:LATEST.json", git_dir=True))
    assert latest["phase"] == "manual-status"
    assert latest["outcome"] == "snapshot"
    assert "PRIVATE SOURCE SENTINEL" not in json.dumps(latest, sort_keys=True)
