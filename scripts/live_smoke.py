#!/usr/bin/env python3
from __future__ import annotations

import argparse
from hashlib import sha256
import httpx
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.models.claude_cli import ClaudeCLI
from authorial_flow.models.codex_cli import CodexCLI
from authorial_flow.models.common import (
    ModelCall, ProviderFailure, unique_model_profiles, validate_schema_contract,
)
from authorial_flow.models.pangram import PangramClient
from authorial_flow.process_runner import ProcessRunner, ProcessSpec
from authorial_flow.research.fetch import HTTPFetcher
from authorial_flow.runtime import runtime_schema_inventory


FIXED_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"status": {"type": "string", "enum": ["ok"]}},
    "required": ["status"],
}


def validate_runtime_schema_inventory() -> dict[str, Any]:
    invalid=[]
    schemas=runtime_schema_inventory()
    for name,schema in schemas.items():
        try:
            validate_schema_contract(schema)
        except ValueError as exc:
            invalid.append({"name":name,"error":f"{type(exc).__name__}: {exc}"})
    return {
        "status":"pass" if not invalid else "fail",
        "schema_count":len(schemas),
        "invalid":invalid,
    }


def redact(value: Any, secret_values: list[str]) -> Any:
    secrets = [s for s in secret_values if s]
    if isinstance(value, dict):
        return {k: redact(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, secrets) for v in value]
    if isinstance(value, tuple):
        return tuple(redact(v, secrets) for v in value)
    if isinstance(value, str):
        out = value
        for secret in secrets:
            out = out.replace(secret, "[REDACTED]")
        return out
    return value


def _version(argv: list[str]) -> str:
    try:
        p = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return (p.stdout or p.stderr).strip().splitlines()[0][:300] if p.returncode == 0 else f"exit-{p.returncode}"
    except Exception as exc:
        return f"unavailable:{type(exc).__name__}"


def run_heartbeat_check(
    *, artifact_root: Path, sleep_seconds: float = 11.0, heartbeat_seconds: float = 5.0
) -> dict[str, Any]:
    artifact_root.mkdir(parents=True, exist_ok=True)
    stamps: list[float] = []
    started = time.monotonic()

    def on_heartbeat(payload: dict) -> None:
        stamps.append(time.monotonic())
        print(
            f"heartbeat pid={payload['pid']} elapsed={payload['elapsed_seconds']:.1f}s alive={payload['alive']}",
            flush=True,
        )

    runner = ProcessRunner(heartbeat_seconds=heartbeat_seconds, on_heartbeat=on_heartbeat)
    result = runner.run(ProcessSpec(
        argv=[sys.executable, "-c", f"import time; time.sleep({float(sleep_seconds)!r})"],
        cwd=ROOT,
        timeout_seconds=max(sleep_seconds + 5, 5),
    ))
    gaps = [b - a for a, b in zip(stamps, stamps[1:])]
    report = {
        "status": "pass" if result.returncode == 0 and stamps else "fail",
        "returncode": result.returncode,
        "duration_seconds": result.duration_seconds,
        "heartbeat_count": len(stamps),
        "heartbeat_gaps_seconds": gaps,
        "first_heartbeat_after_seconds": (stamps[0] - started) if stamps else None,
    }
    ArtifactStore(artifact_root).put_text(json.dumps(report, sort_keys=True, indent=2) + "\n", "json", {
        "kind": "live-smoke-heartbeat",
    })
    return report


def _model_smoke(provider: str, runner: ProcessRunner, store: ArtifactStore, args) -> dict[str, Any]:
    prompt = 'Return exactly this JSON object: {"status":"ok"}'
    call = ModelCall(prompt=prompt, schema=FIXED_SCHEMA, role="live_smoke")
    started = time.monotonic()
    if provider == "claude":
        models = unique_model_profiles([m.strip() for m in args.claude_models.split(",") if m.strip()])
        cli_version = _version(["claude", "--version"])
    else:
        models = unique_model_profiles([m.strip() or None for m in args.codex_models.split(",")])
        cli_version = _version(["codex", "--version"])
    profiles=[]
    for model in models:
        adapter = (
            ClaudeCLI([model], cli_version=cli_version, timeout_seconds=args.timeout)
            if provider == "claude"
            else CodexCLI([model], cli_version=cli_version, timeout_seconds=args.timeout)
        )
        try:
            result = adapter.call(call, runner, store)
        except ProviderFailure as exc:
            profiles.append({
                "configured_model":model or "CLI-default",
                "status":"fail",
                "attempts":[{
                    "model":attempt.model,
                    "failure_kind":attempt.failure_kind,
                    "capability_signature":attempt.capability_signature,
                    "returncode":attempt.returncode,
                } for attempt in exc.attempts],
            })
        else:
            profiles.append({
                "configured_model":model or "CLI-default",
                "resolved_model":result.model,
                "status":"pass",
                "request_id":result.request_id,
                "attempts":[{
                    "model":attempt.model,
                    "failure_kind":attempt.failure_kind,
                    "capability_signature":attempt.capability_signature,
                    "returncode":attempt.returncode,
                } for attempt in result.attempts],
            })
    return {
        "status": "pass" if profiles and all(row["status"]=="pass" for row in profiles) else "fail",
        "provider": provider,
        "cli_version": cli_version,
        "duration_seconds": time.monotonic() - started,
        "schema_preflight":validate_runtime_schema_inventory(),
        "profiles":profiles,
    }


def _pangram_smoke(args) -> dict[str, Any]:
    import httpx

    key = (os.environ.get("PANGRAM_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("PANGRAM_API_KEY is required for --pangram")
    with httpx.Client(base_url=args.pangram_base_url, timeout=args.timeout) as http:
        client = PangramClient(key, http, model=args.pangram_model)
        started = time.monotonic()
        client.ensure_access()
        report: dict[str, Any] = {
            "status": "pass",
            "detector_contract": args.pangram_model,
            "required_version": "4.0",
            "auth_check": "pass",
            "submitted": False,
            "duration_seconds": time.monotonic() - started,
        }
        if args.pangram_submit:
            text = "A small bird landed on the fence, looked around, and flew away."
            digest = sha256(text.encode()).hexdigest()
            task = client.submit(text, digest)
            deadline = time.monotonic() + args.timeout
            while True:
                result = client.poll(task.task_id)
                if result.stage in {"STAGE_SUCCESS", "STAGE_FAILURE", "STAGE_ERROR"}:
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Pangram task did not finish: {task.task_id}")
                time.sleep(args.poll_seconds)
            report.update({
                "submitted": True,
                "task_id": task.task_id,
                "candidate_hash": digest,
                "stage": result.stage,
                "version": result.version,
                "prediction_short": result.prediction_short,
                "fraction_ai": result.fraction_ai,
                "fraction_ai_assisted": result.fraction_ai_assisted,
                "duration_seconds": time.monotonic() - started,
            })
        return report


def _research_smoke(args) -> dict[str, Any]:
    import httpx

    started = time.monotonic()
    with httpx.Client(follow_redirects=True, timeout=args.timeout) as client:
        source = HTTPFetcher(client=client, max_bytes=250_000).fetch(args.research_url)
    return {
        "status": "pass",
        "provider": "direct-url-http",
        "requested_url": args.research_url,
        "canonical_url": source.final_url,
        "access_level": str(source.access_level.value if hasattr(source.access_level, "value") else source.access_level),
        "mime_type": source.mime_type,
        "body_sha256": source.body_sha256,
        "access_limitation": source.access_limitation,
        "duration_seconds": time.monotonic() - started,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Opt-in live provider/detector smoke tests")
    p.add_argument("--claude", action="store_true")
    p.add_argument("--codex", action="store_true")
    p.add_argument("--pangram", action="store_true")
    p.add_argument("--pangram-submit", action="store_true", help="Explicitly spend one harmless Pangram task")
    p.add_argument("--research", action="store_true")
    p.add_argument("--heartbeat", action="store_true")
    p.add_argument("--all", action="store_true")
    p.add_argument("--claude-models", default=os.environ.get("AUTHORIAL_CLAUDE_MODELS", "claude-opus-5,claude-fable-5"))
    p.add_argument("--codex-models", default=os.environ.get("AUTHORIAL_CODEX_MODELS", "gpt-5.6-sol,"))
    p.add_argument("--pangram-model", default="pangram-4")
    p.add_argument("--pangram-base-url", default="https://text.external-api.pangram.com")
    p.add_argument("--research-url", default="https://example.com/")
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--poll-seconds", type=float, default=2.0)
    p.add_argument("--out", type=Path, default=ROOT / ".state" / "live-smoke" / "report.json")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.pangram_submit:
        args.pangram = True
    if args.all:
        args.claude = args.codex = args.pangram = args.research = args.heartbeat = True
    if not any([args.claude, args.codex, args.pangram, args.research, args.heartbeat]):
        raise SystemExit("Choose at least one smoke: --claude --codex --pangram --research --heartbeat or --all")

    state_root = args.out.parent
    artifact_root = state_root / "artifacts"
    store = ArtifactStore(artifact_root)
    heartbeat_events: list[dict] = []

    def provider_heartbeat(payload: dict) -> None:
        heartbeat_events.append(payload)
        print(f"heartbeat pid={payload['pid']} elapsed={payload['elapsed_seconds']:.1f}s", flush=True)

    runner = ProcessRunner(heartbeat_seconds=10, on_heartbeat=provider_heartbeat)
    report: dict[str, Any] = {
        "format": "authorial-flow-live-smoke-v1",
        "started_at": time.time(),
        "schema_preflight":validate_runtime_schema_inventory(),
        "results": {},
    }
    active_check=""
    try:
        if args.claude:
            active_check="claude"
            report["results"]["claude"] = _model_smoke("claude", runner, store, args)
        if args.codex:
            active_check="codex"
            report["results"]["codex"] = _model_smoke("codex", runner, store, args)
        if args.pangram:
            active_check="pangram"
            report["results"]["pangram"] = _pangram_smoke(args)
        if args.research:
            active_check="research"
            report["results"]["research"] = _research_smoke(args)
        if args.heartbeat:
            active_check="heartbeat"
            report["results"]["heartbeat"] = run_heartbeat_check(
                artifact_root=artifact_root / "heartbeat", sleep_seconds=11, heartbeat_seconds=5,
            )
    except httpx.HTTPStatusError as exc:
        response=getattr(exc,"response",None)
        status_code=int(getattr(response,"status_code",0) or 0)
        if status_code in {401,403} and active_check == "pangram":
            report["credential_required"]="PANGRAM_API_KEY"
            report["credential_status_code"]=status_code
            report["error"]={"type":type(exc).__name__,"message":str(exc)}
            status=3
        elif status_code == 402 and active_check == "pangram":
            report["account_action_required"]="PANGRAM_CREDITS"
            report["account_status_code"]=status_code
            report["error"]={"type":type(exc).__name__,"message":str(exc)}
            status=4
        else:
            report["error"] = {"type": type(exc).__name__, "message": str(exc)}
            status = 2
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        status = 2
    else:
        status = 0 if all(v.get("status") == "pass" for v in report["results"].values()) else 2
    report["finished_at"] = time.time()
    report["provider_heartbeats"] = heartbeat_events
    secrets = [os.environ.get("PANGRAM_API_KEY", ""), os.environ.get("BRAVE_SEARCH_API_KEY", "")]
    report = redact(report, secrets)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if status == 3 and report.get("credential_required"):
        print(
            f"live_smoke_credential_required={report['credential_required']} status={report.get('credential_status_code','')}",
            file=sys.stderr,flush=True,
        )
    elif status == 4 and report.get("account_action_required"):
        print(
            f"live_smoke_account_action_required={report['account_action_required']} status={report.get('account_status_code','')}",
            file=sys.stderr,flush=True,
        )
    elif status != 0:
        failed=[]
        details=[]
        for name,value in (report.get("results") or {}).items():
            if not isinstance(value,dict) or value.get("status") == "pass":
                continue
            failed.append(str(name))
            detail=str(value.get("detail") or value.get("error") or value.get("message") or "").strip()
            if detail:
                details.append(f"{name}: {detail}")
        error=report.get("error") or {}
        if isinstance(error,dict) and error:
            failed.append("exception")
            details.append(f"exception: {error.get('type','')}: {error.get('message','')}")
        label=",".join(failed) or "unknown"
        suffix=(" | " + "; ".join(details)) if details else ""
        print(f"live_smoke_failed={label}{suffix}",file=sys.stderr,flush=True)
    print(f"live_smoke_report={args.out}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
