from __future__ import annotations

"""Repairable installer preflight.

This module exists because installer/test failures happen before the LangGraph runtime
can enter its normal repair node.  It reuses the same isolated production repair
cycle, so a machine-fixable pytest regression can be repaired without making the
owner collect or relay logs.
"""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Sequence

from .config import RuntimeConfig
from .finalize import build_evidence_package

_MAX_TEXT=12000
_SECRET_NAMES=("PANGRAM_API_KEY","BRAVE_SEARCH_API_KEY","OPENAI_API_KEY","ANTHROPIC_API_KEY")


def _redact(text:str)->str:
    value=str(text or "")
    for name in _SECRET_NAMES:
        secret=str(os.environ.get(name) or "")
        if secret:
            value=value.replace(secret,"[REDACTED]")
    return value[:_MAX_TEXT] + ("[TRUNCATED]" if len(value)>_MAX_TEXT else "")


def _default_command_runner(command:Sequence[str],cwd:Path):
    return subprocess.run(
        list(command),cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
    )


def _emit_result(result:Any)->None:
    stdout=str(getattr(result,"stdout","") or "")
    stderr=str(getattr(result,"stderr","") or "")
    if stdout:
        print(stdout,end="" if stdout.endswith("\n") else "\n",flush=True)
    if stderr:
        print(stderr,end="" if stderr.endswith("\n") else "\n",file=sys.stderr,flush=True)


def _program_version(root:Path)->str:
    proc=subprocess.run(
        ["git","rev-parse","HEAD"],cwd=root,text=True,
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
    )
    return proc.stdout.strip() if proc.returncode==0 and proc.stdout.strip() else "bootstrap"


def _source_snapshot(services:Any,root:Path)->tuple[str,str]:
    source=root/"project"/"INPUT.md"
    if not source.is_file():
        return "",""
    text=source.read_text(encoding="utf-8")
    ref=services.artifact_store.put_text(
        text,"md",{"kind":"bootstrap-source-snapshot","path":str(source)}
    ).sha256
    return ref,sha256(text.encode()).hexdigest()


def _evidence_file_payload(root:Path,evidence_file:Path|None)->dict[str,Any]|None:
    if evidence_file is None:
        return None
    path=evidence_file if evidence_file.is_absolute() else root/evidence_file
    path=path.resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("evidence file must remain inside project root") from exc
    if not path.is_file():
        return {"path":str(path),"missing":True,"sha256":"","content":""}
    data=path.read_bytes()
    try:
        text=data.decode("utf-8")
    except UnicodeDecodeError:
        text="[BINARY EVIDENCE FILE]"
    return {
        "path":str(path.relative_to(root.resolve())),
        "missing":False,
        "sha256":sha256(data).hexdigest(),
        "content":_redact(text),
    }


def _credential_requirement(root:Path,evidence_file:Path|None)->str:
    if evidence_file is None:
        return ""
    path=evidence_file if evidence_file.is_absolute() else root/evidence_file
    try:
        payload=json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    credential=str(payload.get("credential_required") or "").strip()
    return credential if credential in {"PANGRAM_API_KEY"} else ""


def _account_action_requirement(root:Path,evidence_file:Path|None)->str:
    if evidence_file is None:
        return ""
    path=evidence_file if evidence_file.is_absolute() else root/evidence_file
    try:
        payload=json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    action=str(payload.get("account_action_required") or "").strip()
    return action if action in {"PANGRAM_CREDITS"} else ""


def _persist_failure(
    *,services:Any,root:Path,command:Sequence[str],result:Any,attempt:int,source_hash:str,
    phase:str="installer-preflight",failure_class:str="REGRESSION_ARCHITECTURE",
    originating_node:str="regressions",evidence_file:Path|None=None,
)->str:
    is_live_smoke=phase == "installer-live-smoke"
    payload={
        "format":"authorial-flow-bootstrap-repair-evidence-v1",
        "failure_class":failure_class,
        "originating_node":originating_node,
        "phase":phase,
        "failure_code":"installer live smoke failed" if is_live_smoke else "installer pytest preflight failed",
        "exception_type":"LiveSmokeFailure" if is_live_smoke else "PreflightTestFailure",
        "exception_message":f"preflight command returned {int(getattr(result,'returncode',1) or 1)}",
        "program_version":_program_version(root),
        "thread_id":"bootstrap-preflight",
        "source_hash":source_hash,
        "repair_attempt":attempt,
        "command":[str(x) for x in command],
        "returncode":int(getattr(result,"returncode",1) or 1),
        "stdout":_redact(str(getattr(result,"stdout","") or "")),
        "stderr":_redact(str(getattr(result,"stderr","") or "")),
        "suggested_test_command":"python -m pytest -q",
        "evidence_file":_evidence_file_payload(root,evidence_file),
    }
    return services.artifact_store.put_text(
        json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+"\n",
        "json",{"kind":"bootstrap-repair-evidence"},
    ).sha256



def _acceptance_command(root:Path,command:Sequence[str])->list[str]:
    argv=[str(x) for x in command]
    if not argv:
        return []
    if argv[0] == ".venv/bin/python":
        argv[0]=str((root/argv[0]).resolve())
    return argv

def run_preflight(
    config:RuntimeConfig,
    command:Sequence[str],
    *,
    services:Any|None=None,
    repair_cycle_factory:Callable[[RuntimeConfig,Path,Any],Callable[[dict[str,Any]],dict[str,Any]]]|None=None,
    command_runner:Callable[[Sequence[str],Path],Any]|None=None,
    package_builder:Callable[...,Path]=build_evidence_package,
    phase:str="installer-preflight",
    failure_class:str="REGRESSION_ARCHITECTURE",
    originating_node:str="regressions",
    source_provenance:str="INSTALLER_PREFLIGHT",
    evidence_file:Path|None=None,
    verify_before_promotion:bool=False,
)->int:
    """Run installer preflight and repair one machine-fixable failure autonomously.

    The repair cycle itself already contains bounded planner attempts plus one
    implementation correction and full controller verification.  After promotion,
    rerun the *exact* installer command once in the main checkout.  A mismatch at
    that point is treated as an environment-specific bounded failure and packaged.
    """
    if not command:
        raise ValueError("preflight command is required")
    root=config.root.resolve()
    if services is None:
        from .runtime import RuntimeServices
        services=RuntimeServices.from_config(config)
    if repair_cycle_factory is None:
        from .runtime import _production_repair_cycle
        repair_cycle_factory=_production_repair_cycle
    command_runner=command_runner or _default_command_runner

    initial=command_runner(command,root)
    _emit_result(initial)
    if int(getattr(initial,"returncode",1)) == 0:
        return 0

    credential=_credential_requirement(root,evidence_file)
    if credential:
        print(f"bootstrap_credential_required={credential}",file=sys.stderr,flush=True)
        return 3
    account_action=_account_action_requirement(root,evidence_file)
    if account_action:
        print(f"bootstrap_account_action_required={account_action}",file=sys.stderr,flush=True)
        return 4

    source_ref,source_hash=_source_snapshot(services,root)
    evidence_ref=_persist_failure(
        services=services,root=root,command=command,result=initial,attempt=0,source_hash=source_hash,
        phase=phase,failure_class=failure_class,originating_node=originating_node,evidence_file=evidence_file,
    )
    cycle=repair_cycle_factory(config,root,services)
    state={
        "thread_id":"bootstrap-preflight",
        "source_ref":source_ref,
        "source_hash":source_hash,
        "task_mode":"P0",
        "source_provenance":source_provenance,
        "failure_class":failure_class,
        "failure_origin_node":originating_node,
        "failure_record_ref":evidence_ref,
        "last_error_ref":evidence_ref,
        "authorial_information_missing":False,
        "repair_attempt":0,
    }
    if verify_before_promotion:
        state["repair_acceptance_commands"]=[_acceptance_command(root,command)]

    promoted=False
    for attempt in range(config.repair_rounds):
        state["repair_attempt"]=attempt
        try:
            outcome=cycle(state)
        except Exception as exc:
            print(
                f"bootstrap_repair_controller_error={type(exc).__name__}: {exc}",
                file=sys.stderr,flush=True,
            )
            break
        if outcome.get("pass"):
            promoted=True
            break
        error_ref=str(outcome.get("error_ref") or state.get("failure_record_ref") or "")
        if error_ref:
            state["failure_record_ref"]=error_ref
            state["last_error_ref"]=error_ref
        if outcome.get("exhausted") or outcome.get("owner_judgment_required"):
            break

    if promoted:
        rerun=command_runner(command,root)
        _emit_result(rerun)
        if int(getattr(rerun,"returncode",1)) == 0:
            return 0
        evidence_ref=_persist_failure(
            services=services,root=root,command=command,result=rerun,
            attempt=int(state.get("repair_attempt",0))+1,source_hash=source_hash,
            phase=phase,failure_class=failure_class,originating_node=originating_node,evidence_file=evidence_file,
        )
        state["failure_record_ref"]=evidence_ref

    package=package_builder(config,reason="bounded-failure")
    print(f"bootstrap_repair_evidence={package}",flush=True)
    return int(getattr(initial,"returncode",1) or 1)


def _parser()->argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description="Run a repairable installer preflight command")
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--phase",default="installer-preflight")
    parser.add_argument("--failure-class",default="REGRESSION_ARCHITECTURE")
    parser.add_argument("--originating-node",default="regressions")
    parser.add_argument("--source-provenance",default="INSTALLER_PREFLIGHT")
    parser.add_argument("--evidence-file",type=Path)
    parser.add_argument("--verify-before-promotion",action="store_true")
    parser.add_argument("command",nargs=argparse.REMAINDER)
    return parser


def main(argv:list[str]|None=None)->int:
    args=_parser().parse_args(argv)
    command=list(args.command)
    if command and command[0] == "--":
        command=command[1:]
    if not command:
        print("bootstrap repair requires a command after --",file=sys.stderr)
        return 2
    return run_preflight(
        RuntimeConfig.from_root(args.root),command,
        phase=args.phase,failure_class=args.failure_class,
        originating_node=args.originating_node,source_provenance=args.source_provenance,
        evidence_file=args.evidence_file,verify_before_promotion=args.verify_before_promotion,
    )


if __name__ == "__main__":
    raise SystemExit(main())
