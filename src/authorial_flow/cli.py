from __future__ import annotations

import argparse
import getpass
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

from .config import RuntimeConfig
from .artifacts import ArtifactStore
from .events import EventJournal
from .finalize import build_evidence_package
from .graph import open_graph
from .pause import PauseObservation, temporary_sigint_pause
from .runtime import RuntimeServices, build_runtime_dependencies, seed_initial_state
from .policy import PolicySnapshot, file_sha
from .project import ProjectInputs, compute_thread_id
from .version import GRAPH_VERSION
from .supervisor import (
    SupervisorAction,
    SupervisorActionEffect,
    SupervisorSessionStore,
    SupervisorSnapshot,
    ask_owner_supervisor,
    normalize_action,
)

LEARNING_VERSION='1'


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog='authorial-flow',description='Checkpointed authorial thought-flow runtime')
    p.add_argument('--root',type=Path,default=repository_root())
    sub=p.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run',help='start or resume the content-addressed project thread')
    run.add_argument('source',nargs='?',type=Path)
    sub.add_parser('resume',help='resume the current thread after interruption')
    sub.add_parser('status',help='show current checkpoint/event status without model calls')
    ans=sub.add_parser('answer',help='resume an owner interrupt with JSON response')
    ans.add_argument('response')
    pkg=sub.add_parser('package',help='build a secret-free evidence package')
    pkg.add_argument('--reason',choices=['final','bounded-failure','manual'],default='manual')
    return p


def format_heartbeat(*,thread_id:str,node:str,phase:str,model:str,pid:int|str,elapsed:float,retry:int,moves:int,last_event:str)->str:
    total=max(0,int(elapsed)); minutes,seconds=divmod(total,60)
    return (
        f"thread={thread_id[:12]} | node={node or '-'} | phase={phase or '-'} | "
        f"model={model or '-'} | pid={pid or '-'} | elapsed={minutes:02d}:{seconds:02d} | "
        f"retry={retry} | moves={moves} | {last_event}"
    )


def _thread_file(config: RuntimeConfig)->Path:
    return config.state_dir/'current-thread.json'


def _write_thread(config:RuntimeConfig,thread_id:str,source:Path)->None:
    config.state_dir.mkdir(parents=True,exist_ok=True)
    payload={'thread_id':thread_id,'source':str(source.resolve()),'source_sha256':file_sha(source)}
    _thread_file(config).write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')


def _read_thread(config:RuntimeConfig)->dict[str,Any]:
    path=_thread_file(config)
    if not path.exists():
        raise RuntimeError('No current thread. Run authorial-flow run first.')
    return json.loads(path.read_text())


def program_version(root: Path) -> str:
    """Return a program lineage token that changes after promoted code repairs."""
    import subprocess
    try:
        result=subprocess.run(
            ["git","rev-parse","HEAD"],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=True
        )
        value=result.stdout.strip()
        if value:
            return value
    except (OSError, subprocess.CalledProcessError):
        pass
    return GRAPH_VERSION


def resolve_policy_dir(root: Path) -> Path:
    direct=root/"policy"
    if (direct/"MANIFEST.json").is_file():
        return direct
    candidates=sorted(p.parent for p in direct.glob("*/MANIFEST.json") if p.is_file())
    if len(candidates)==1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(direct/"MANIFEST.json")
    raise RuntimeError("multiple policy snapshots found; keep exactly one active policy bundle")


def _resolve_thread(config:RuntimeConfig,source:Path|None)->tuple[str,Path]:
    inputs=ProjectInputs.load(config.root/'project')
    policy=PolicySnapshot.load(resolve_policy_dir(config.root))
    source=(source or config.root/'project'/'INPUT.md').resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    base=compute_thread_id(inputs,policy,GRAPH_VERSION,LEARNING_VERSION)
    base=sha256(f"{base}\0program={program_version(config.root)}".encode()).hexdigest()
    if source != (config.root/'project'/'INPUT.md').resolve():
        base=sha256(f"{base}\0{file_sha(source)}".encode()).hexdigest()
    return base,source


def _graph_config(thread_id:str)->dict[str,Any]:
    return {'configurable':{'thread_id':thread_id}}


def _supervisor_interrupt(result: dict[str, Any]) -> dict[str, Any] | None:
    for interrupt_value in result.get("__interrupt__") or []:
        payload = (
            interrupt_value
            if isinstance(interrupt_value, dict)
            else getattr(interrupt_value, "value", None)
        )
        if isinstance(payload, dict) and str(payload.get("kind") or "").upper() == "SUPERVISOR":
            return payload
    return None


def _render_pause_request(observation: PauseObservation) -> None:
    operation = observation.operation
    if operation is not None and operation.cancelable:
        detail = "/".join(filter(None, (operation.provider, operation.model, operation.role)))
        suffix = f" ({detail})" if detail else ""
        print(f"Pause requested; cancelling the active model call{suffix}.", file=sys.stderr, flush=True)
        return
    if operation is not None:
        label = operation.operation or "atomic operation"
        print(
            f"Pause requested; waiting for the current {label} to reach its checkpoint boundary.",
            file=sys.stderr,
            flush=True,
        )
        return
    print("Pause requested; stopping at the next checkpoint boundary.", file=sys.stderr, flush=True)


def _invoke_with_pause_signal(
    app: Any,
    initial: Any,
    graph_config: dict[str, Any],
    services: RuntimeServices | Any,
) -> dict[str, Any]:
    controller = getattr(services, "pause_controller", None)
    if controller is None:
        return app.invoke(initial, graph_config)
    with temporary_sigint_pause(controller, _render_pause_request):
        return app.invoke(initial, graph_config)


def render_supervisor_reply(reply: Any) -> None:
    print(reply.answer)
    if reply.inferences:
        print("Inferences:")
        for item in reply.inferences:
            print(f"- {item}")
    if reply.uncertainties:
        print("Uncertainties:")
        for item in reply.uncertainties:
            print(f"- {item}")


def render_confirmed_effect(effect: SupervisorActionEffect) -> None:
    print("Proposed checkpoint action:")
    print(json.dumps({
        "action_kind": effect.action_kind,
        "scope": effect.scope,
        "restart_depth": effect.restart_depth,
        "resume_node": effect.resume_node,
        "invalidated_fields": effect.invalidated_fields,
        "removed_moves": effect.removed_moves,
    }, ensure_ascii=False, indent=2))


def _load_interrupt_snapshot(payload: dict[str, Any], services: RuntimeServices | Any) -> SupervisorSnapshot:
    embedded = payload.get("snapshot")
    if isinstance(embedded, dict):
        return SupervisorSnapshot.model_validate(embedded)
    snapshot_ref = str(payload.get("snapshot_ref") or "")
    found = services.artifact_store.find(snapshot_ref) if snapshot_ref else None
    if found is None:
        raise ValueError("supervisor snapshot artifact is unavailable")
    return SupervisorSnapshot.model_validate_json(found.path.read_text(encoding="utf-8"))


def run_supervisor_loop(
    payload: dict[str, Any],
    services: RuntimeServices | Any,
    *,
    interactive: bool | None = None,
) -> SupervisorAction | None:
    if interactive is None:
        interactive = bool(sys.stdin.isatty())
    if not interactive:
        print("Run remains paused. Reopen this thread interactively to continue supervision.")
        return None

    snapshot = _load_interrupt_snapshot(payload, services)
    session_ref = str(payload.get("session_ref") or "")
    sessions = SupervisorSessionStore(services.artifact_store.root.parent / "supervisor")
    # Validate the durable session reference before accepting terminal input.
    sessions.read(session_ref)
    validation_error = str(payload.get("validation_error") or "").strip()
    if validation_error:
        print(f"Previous action was not applied: {validation_error}", file=sys.stderr)

    while True:
        user_text = input("supervisor> ").strip()
        if user_text.lower() in {"leave", "leave paused", "exit"}:
            print("Run remains paused. ./RUN.sh will reopen this supervisor session.")
            return None
        if not user_text:
            continue
        sessions.append(session_ref, "user", user_text)
        try:
            reply = ask_owner_supervisor(snapshot, sessions.read(session_ref), services)
        except KeyboardInterrupt:
            print("Supervisor answer cancelled; the graph is still paused.", file=sys.stderr)
            continue
        sessions.append(session_ref, "assistant", reply.answer)
        render_supervisor_reply(reply)
        if reply.proposed_action.kind == "NONE":
            continue
        try:
            action, effect = normalize_action(reply.proposed_action, snapshot)
        except ValueError as exc:
            print(f"Proposed action is invalid: {exc}", file=sys.stderr)
            continue
        render_confirmed_effect(effect)
        if input("Apply this action? [y/N] ").strip().lower() not in {"y", "yes"}:
            continue
        return action


def _continue_with_supervision(
    app: Any,
    graph_config: dict[str, Any],
    initial: Any,
    services: RuntimeServices | Any,
    *,
    interactive: bool | None = None,
) -> dict[str, Any]:
    pending = initial
    while True:
        result = _invoke_with_pause_signal(app, pending, graph_config, services)
        payload = _supervisor_interrupt(result)
        if payload is None:
            return result
        action = run_supervisor_loop(payload, services, interactive=interactive)
        if action is None:
            return result
        from langgraph.types import Command
        pending = Command(resume=action.model_dump(mode="json"))


def _run_graph(config:RuntimeConfig,thread_id:str,initial:dict[str,Any]|None,*,services:RuntimeServices|Any|None=None)->dict[str,Any]:
    services=services or RuntimeServices.from_config(config)
    deps=build_runtime_dependencies(config,project_root=config.root,services=services)
    with open_graph(config,deps) as app:
        return _continue_with_supervision(app, _graph_config(thread_id), initial, services)


def _repair_restart_pending_file(config: RuntimeConfig) -> Path:
    return config.state_dir / "repair-restart-pending.json"


def restart_argv(config: RuntimeConfig, source: Path | None = None) -> list[str]:
    # Autonomous code repair must preserve the already-checkpointed conceptual thread.
    return [sys.executable, "-m", "authorial_flow.cli", "--root", str(config.root), "resume"]


def _machine_restart_interrupt(result: dict[str, Any]) -> dict[str, Any] | None:
    interrupts=result.get("__interrupt__") or []
    if not interrupts:
        return None
    first=interrupts[0]
    payload=getattr(first,"value",None)
    if isinstance(payload,dict) and str(payload.get("kind") or "").upper()=="MACHINE_RESTART":
        return payload
    return None


def _machine_restart_command():
    from langgraph.types import Command
    return Command(resume={"kind":"MACHINE_RESTART_RESUME"})


_TERMINAL_RECOVERY_NODES={
    "regressions","representation","generation","cold_audit","freeze","detector","owner_learning","repair",
}


def _terminal_failure_replay_config(app, graph_config:dict[str,Any], result:dict[str,Any]):
    """Return the newest checkpoint immediately before the failed machine node."""
    if str(result.get("status") or "") != "bounded_machine_stop":
        return None
    origin=str(result.get("failure_origin_node") or "")
    if origin not in _TERMINAL_RECOVERY_NODES:
        return None
    latest=app.get_state(graph_config)
    if tuple(getattr(latest,"next",()) or ()):
        return None
    for snapshot in app.get_state_history(graph_config):
        if origin in tuple(getattr(snapshot,"next",()) or ()):
            return getattr(snapshot,"config",None)
    return None


def replay_terminal_machine_failure_on_app(app, graph_config:dict[str,Any], result:dict[str,Any])->dict[str,Any]:
    """Replay the failed node from its pre-failure checkpoint on the same thread."""
    replay_config=_terminal_failure_replay_config(app,graph_config,result)
    if replay_config is None:
        return result
    return app.invoke(None,replay_config)


def _bounded_recovery_marker(config:RuntimeConfig,thread_id:str,version:str)->Path:
    key=sha256(f"{thread_id}\0{version}".encode()).hexdigest()
    return config.state_dir/"bounded-recovery"/f"{key}.json"


def _write_bounded_recovery_marker(
    config:RuntimeConfig, *, thread_id:str, version:str, origin:str, failure_class:str="",
    failure_record_ref:str="", checkpoint_id:str="", reason:str,
)->Path:
    marker=_bounded_recovery_marker(config,thread_id,version)
    if marker.is_file():
        return marker
    marker.parent.mkdir(parents=True,exist_ok=True)
    payload={
        "format":"authorial-flow-bounded-recovery-v1",
        "thread_id":thread_id,
        "program_version":version,
        "failure_origin_node":origin,
        "failure_class":failure_class,
        "failure_record_ref":failure_record_ref,
        "checkpoint_id":checkpoint_id,
        "reason":reason,
    }
    tmp=marker.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    os.replace(tmp,marker)
    return marker


def recover_terminal_machine_failure(
    config:RuntimeConfig, thread_id:str, result:dict[str,Any]|None=None, *, services:RuntimeServices|Any|None=None,
)->dict[str,Any]|None:
    """Recover one terminal machine failure per program version without reseeding the thread.

    This is primarily an upgrade bridge for a thread that an older program image
    already finalized as ``bounded_machine_stop``.  A per-program marker prevents
    repeated invocations of the same broken release from replaying providers forever.
    """
    services=services or RuntimeServices.from_config(config)
    deps=build_runtime_dependencies(config,project_root=config.root,services=services)
    graph_config=_graph_config(thread_id)
    with open_graph(config,deps) as app:
        latest=app.get_state(graph_config)
        latest_next=tuple(getattr(latest,"next",()) or ())
        latest_values=dict(getattr(latest,"values",{}) or {})
        if latest_next:
            return None if result is None else result
        terminal=result if result is not None else latest_values
        if str(terminal.get("status") or "") != "bounded_machine_stop":
            return None if result is None else result
        origin=str(terminal.get("failure_origin_node") or "")
        if origin not in _TERMINAL_RECOVERY_NODES:
            return terminal

        version=program_version(config.root)
        marker=_bounded_recovery_marker(config,thread_id,version)
        if marker.is_file():
            return terminal

        replay_config=_terminal_failure_replay_config(app,graph_config,terminal)
        if replay_config is None:
            return terminal

        payload={
            "thread_id":thread_id,
            "program_version":version,
            "failure_origin_node":origin,
            "failure_class":str(terminal.get("failure_class") or ""),
            "failure_record_ref":str(terminal.get("failure_record_ref") or terminal.get("failure_evidence_ref") or ""),
            "checkpoint_id":str((replay_config.get("configurable") or {}).get("checkpoint_id") or ""),
            "reason":"legacy-terminal-replay",
        }
        _write_bounded_recovery_marker(
            config, thread_id=thread_id, version=version, origin=origin,
            failure_class=payload["failure_class"], failure_record_ref=payload["failure_record_ref"],
            checkpoint_id=payload["checkpoint_id"], reason=payload["reason"],
        )
        EventJournal(config.event_path).append("bounded-recovery-replay",payload)
        print(f"recovery: replaying terminal {origin} checkpoint on same thread",flush=True)
        return _continue_with_supervision(app, replay_config, None, services)


def maybe_restart_after_repair(config: RuntimeConfig, result: dict[str, Any]) -> bool:
    if str(result.get("status") or "") != "repair_promoted_restart_required":
        return False
    current=_read_thread(config)
    argv = restart_argv(config)
    pending={
        "thread_id":current.get("thread_id",""),
        "source":current.get("source",""),
        "program_version":result.get("program_version",""),
        "repair_commit":result.get("repair_commit",""),
        "failure_evidence_ref":result.get("failure_evidence_ref") or result.get("failure_record_ref", ""),
        "repair_resume_node":result.get("repair_resume_node","regressions"),
        "plan_ref":result.get("plan_ref",""),
        "test_ref":result.get("test_ref",""),
        "review_ref":result.get("review_ref",""),
    }
    pending_path=_repair_restart_pending_file(config)
    pending_path.parent.mkdir(parents=True,exist_ok=True)
    tmp=pending_path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(pending,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    os.replace(tmp,pending_path)
    lineage=config.state_dir/"repair-lineage.jsonl"
    lineage.parent.mkdir(parents=True,exist_ok=True)
    with lineage.open("a",encoding="utf-8") as fh:
        fh.write(json.dumps({
            "parent_thread_id":current.get("thread_id",""),
            "program_version":result.get("program_version",""),
            "repair_commit":result.get("repair_commit",""),
            "failure_evidence_ref":pending["failure_evidence_ref"],
            "repair_resume_node":pending["repair_resume_node"],
            "reason":"promoted_code_repair",
        },sort_keys=True)+"\n")
    EventJournal(config.event_path).append(
        "repair:restart-same-thread", {
            "thread_id":current.get("thread_id",""),
            "program_version":result.get("program_version",""),
            "repair_commit":result.get("repair_commit",""),
            "repair_resume_node":pending["repair_resume_node"],
        }
    )
    EventJournal(config.event_path).append(
        "repair-restart", {
            "thread_id":current.get("thread_id",""),
            "program_version": result.get("program_version", ""),
            "repair_commit":result.get("repair_commit",""),
            "repair_resume_node":pending["repair_resume_node"],
            "argv": argv[1:],
        }
    )
    os.execv(argv[0], argv)
    return True


def ensure_pangram_key() -> str:
    key=(os.environ.get("PANGRAM_API_KEY") or "").strip()
    if key:
        return key
    if not sys.stdin.isatty():
        raise RuntimeError(
            "PANGRAM_API_KEY is required for detector submission; run interactively to enter it without saving"
        )
    key=getpass.getpass("Pangram API key for this process (not saved): ").strip()
    if not key:
        raise RuntimeError("PANGRAM_API_KEY is required for detector submission")
    os.environ["PANGRAM_API_KEY"]=key
    return key



def finalize_if_accepted(config: RuntimeConfig, result: dict[str, Any]) -> dict[str, Any]:
    if str(result.get("status") or "") != "accepted":
        return result
    candidate_ref=str(result.get("recommended_candidate_ref") or "").strip()
    text=""
    if candidate_ref:
        artifact=ArtifactStore(config.artifact_dir).find(candidate_ref)
        if artifact is None:
            raise RuntimeError("accepted recommended candidate artifact is missing")
        try:
            record=json.loads(artifact.path.read_text(encoding="utf-8"))
            text=str(record.get("text") or "").strip() if isinstance(record,dict) else ""
        except Exception as exc:
            raise RuntimeError("accepted recommended candidate artifact is unreadable") from exc
        if not text:
            raise RuntimeError("accepted recommended candidate artifact contains no text")
    else:
        text=" ".join(str(move).strip() for move in (result.get("accepted_moves") or []) if str(move).strip()).strip()
    if not text:
        raise RuntimeError("accepted result has no text to materialize")
    payload=text+"\n"
    final_dir=config.state_dir/"final"
    final_dir.mkdir(parents=True,exist_ok=True)
    state_path=final_dir/"accepted.md"
    root_path=config.root/"RESULT-AUTHORIAL-FLOW.md"
    state_path.write_text(payload,encoding="utf-8")
    root_path.write_text(payload,encoding="utf-8")
    package=build_evidence_package(config,reason="final")
    return {
        **result,
        "accepted_output_path":str(root_path),
        "evidence_package_path":str(package),
    }

def finalize_bounded_failure(config: RuntimeConfig, result: dict[str, Any]) -> dict[str, Any]:
    if str(result.get("status") or "") != "bounded_machine_stop":
        return result
    # A stop produced by this exact program version is already exhausted.  Stamp it
    # so a later manual resume cannot replay the same provider failure indefinitely.
    try:
        current=_read_thread(config)
        thread_id=str(current.get("thread_id") or "")
        origin=str(result.get("failure_origin_node") or "")
        if thread_id and origin in _TERMINAL_RECOVERY_NODES:
            _write_bounded_recovery_marker(
                config, thread_id=thread_id, version=program_version(config.root), origin=origin,
                failure_class=str(result.get("failure_class") or ""),
                failure_record_ref=str(result.get("failure_record_ref") or result.get("failure_evidence_ref") or ""),
                reason="bounded-stop-observed",
            )
    except Exception:
        # Evidence packaging must still succeed even when optional replay bookkeeping cannot.
        pass
    if result.get("evidence_package_path"):
        return result
    package=build_evidence_package(config,reason="bounded-failure")
    EventJournal(config.event_path).append("repair:bounded-stop",{
        "failure_class":str(result.get("failure_class") or ""),
        "failure_evidence_ref":str(result.get("failure_evidence_ref") or result.get("last_error_ref") or ""),
        "evidence_package_path":str(package),
    })
    return {**result,"evidence_package_path":str(package)}


def ensure_brave_key() -> str:
    key=(os.environ.get("BRAVE_SEARCH_API_KEY") or "").strip()
    if key:
        return key
    if not sys.stdin.isatty():
        raise RuntimeError(
            "BRAVE_SEARCH_API_KEY is required only when material research needs search discovery; "
            "run interactively to enter it without saving"
        )
    key=getpass.getpass("Brave Search API key for this process (not saved): ").strip()
    if not key:
        raise RuntimeError("BRAVE_SEARCH_API_KEY is required for material research discovery")
    os.environ["BRAVE_SEARCH_API_KEY"]=key
    return key


def command_run(config:RuntimeConfig,source:Path|None)->int:
    thread_id,source=_resolve_thread(config,source)
    _write_thread(config,thread_id,source)
    journal=EventJournal(config.event_path)
    journal.append('run-start',{'thread_id':thread_id,'source':str(source)})
    services=RuntimeServices.from_config(config,pangram_key_provider=ensure_pangram_key,research_key_provider=ensure_brave_key)
    initial=seed_initial_state(config,project_root=config.root,source_path=source,services=services)
    initial.update({'thread_id':thread_id,'source_hash':file_sha(source)})
    result=_run_graph(config,thread_id,initial,services=services)
    journal.append('run-return',{'thread_id':thread_id,'status':result.get('status',''),'phase':result.get('phase','')})
    maybe_restart_after_repair(config,result)
    result=finalize_bounded_failure(config,result)
    result=finalize_if_accepted(config,result)
    _print_result(result)
    return 0


def command_resume(config:RuntimeConfig)->int:
    current=_read_thread(config); thread_id=current['thread_id']
    services=RuntimeServices.from_config(config,pangram_key_provider=ensure_pangram_key,research_key_provider=ensure_brave_key)
    pending_path=_repair_restart_pending_file(config)
    initial=None
    if pending_path.is_file():
        pending=json.loads(pending_path.read_text(encoding='utf-8'))
        if str(pending.get('thread_id') or '') != str(thread_id):
            raise RuntimeError('repair restart marker belongs to a different thread')
        # Remove before resuming. If the process later dies, a still-paused machine interrupt is
        # auto-detected on the next resume and continued without requiring this marker.
        pending_path.unlink()
        initial=_machine_restart_command()
        result=_run_graph(config,thread_id,initial,services=services)
    else:
        # An older release may already have finalized this exact thread after exhausting
        # a machine repair budget.  Give a newer program image one replay from the latest
        # pre-failure checkpoint instead of reseeding a different thread.
        recovered=recover_terminal_machine_failure(config,thread_id,None,services=services)
        result=recovered if recovered is not None else _run_graph(config,thread_id,None,services=services)
    machine_interrupt=_machine_restart_interrupt(result)
    if machine_interrupt is not None:
        result=_run_graph(config,thread_id,_machine_restart_command(),services=services)
    EventJournal(config.event_path).append('resume-return',{'thread_id':thread_id,'status':result.get('status','')})
    maybe_restart_after_repair(config,result)
    result=finalize_bounded_failure(config,result)
    result=finalize_if_accepted(config,result)
    _print_result(result); return 0


def command_answer(config:RuntimeConfig,response_text:str)->int:
    from langgraph.types import Command
    response=json.loads(response_text)
    current=_read_thread(config); thread_id=current['thread_id']
    services=RuntimeServices.from_config(config,pangram_key_provider=ensure_pangram_key,research_key_provider=ensure_brave_key)
    result=_run_graph(config,thread_id,Command(resume=response),services=services)
    EventJournal(config.event_path).append('owner-answer',{'thread_id':thread_id,'kind':response.get('kind',''),'status':result.get('status','')})
    maybe_restart_after_repair(config,result)
    result=finalize_bounded_failure(config,result)
    result=finalize_if_accepted(config,result)
    _print_result(result); return 0


def command_status(config:RuntimeConfig)->int:
    current={}
    try: current=_read_thread(config)
    except RuntimeError: pass
    event=EventJournal(config.event_path).latest() or {}
    active=event.get('active_process') or {}
    line=format_heartbeat(
        thread_id=current.get('thread_id','-'),node=str(event.get('node','-')),phase=str(event.get('phase','-')),
        model=str(active.get('model') or event.get('model') or '-'),pid=active.get('pid','-'),
        elapsed=float(active.get('elapsed',0)),retry=int(event.get('retry',0) or 0),
        moves=int(event.get('moves',0) or 0),last_event=str(event.get('kind') or 'no events'),
    )
    print(line); return 0


def _print_result(result:dict[str,Any])->None:
    if _supervisor_interrupt(result) is not None:
        return
    if '__interrupt__' in result:
        payload=result['__interrupt__'][0].value
        print(json.dumps({'status':'OWNER_INPUT_REQUIRED','interrupt':payload},ensure_ascii=False,indent=2))
    else:
        print(json.dumps(result,ensure_ascii=False,indent=2,default=str))


def main(argv:list[str]|None=None)->int:
    args=parser().parse_args(argv)
    config=RuntimeConfig.from_root(args.root)
    os.environ.setdefault('LANGGRAPH_STRICT_MSGPACK','true')
    try:
        if args.command=='run': return command_run(config,args.source)
        if args.command=='resume': return command_resume(config)
        if args.command=='status': return command_status(config)
        if args.command=='answer': return command_answer(config,args.response)
        if args.command=='package':
            print(build_evidence_package(config,reason=args.reason)); return 0
        raise RuntimeError(f'unknown command {args.command}')
    except KeyboardInterrupt:
        EventJournal(config.event_path).append('interrupted',{})
        print('Interrupted safely. Run the same command or `authorial-flow resume` to continue.',file=sys.stderr)
        return 130


if __name__=='__main__':
    raise SystemExit(main())
