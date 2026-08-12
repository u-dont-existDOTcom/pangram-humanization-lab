from __future__ import annotations

import json
import os
import platform
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field

from ..artifacts import ArtifactStore
from ..failures import FailureClass, FailureRecord

_MAX_PROVIDER_TEXT = 6000
_SECRET_KEY_RE = re.compile(
    r"(?i)(PANGRAM_API_KEY|BRAVE_SEARCH_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY)\s*[:=]\s*([^\s,;]+)"
)


class ProviderAttemptEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    provider: str = ""
    model: str = ""
    role: str = ""
    request_id: str = ""
    returncode: int = 0
    stdout_ref: str = ""
    stderr_ref: str = ""
    stdout_text: str = ""
    stderr_text: str = ""
    error: str = ""


class RepairEvidenceBundle(BaseModel):
    model_config = ConfigDict(frozen=True)
    format: str = "authorial-flow-repair-evidence-v1"
    failure_class: str
    originating_node: str
    phase: str = ""
    failure_code: str
    exception_type: str = ""
    exception_message: str = ""
    failure_record_ref: str = ""
    program_version: str = ""
    thread_id: str = ""
    checkpoint_id: str = ""
    source_hash: str = ""
    task_mode: str = ""
    source_provenance: str = ""
    local_gate_state: dict[str, Any] = Field(default_factory=dict)
    repair_attempt: int = 0
    authorial_information_missing: bool = False
    provider: str = ""
    role: str = ""
    request_id: str = ""
    expected_schema: dict[str, Any] = Field(default_factory=dict)
    provider_attempts: tuple[ProviderAttemptEvidence, ...] = ()
    runtime_context: dict[str, Any] = Field(default_factory=dict)
    event_context: dict[str, Any] = Field(default_factory=dict)
    state_context: dict[str, Any] = Field(default_factory=dict)
    suggested_test_command: str = ""


def _redact(text: str, secret_values: Iterable[str]) -> str:
    value = str(text or "")
    value = _SECRET_KEY_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", value)
    for secret in secret_values:
        secret = str(secret or "")
        if secret:
            value = value.replace(secret, "[REDACTED]")
    return value


def _bounded_artifact_text(store: ArtifactStore, ref: str, secret_values: Iterable[str]) -> str:
    if not ref:
        return ""
    found = store.find(ref)
    if found is None:
        return "[ARTIFACT MISSING]"
    try:
        text = found.path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"[ARTIFACT READ ERROR: {type(exc).__name__}]"
    text = _redact(text, secret_values)
    if len(text) > _MAX_PROVIDER_TEXT:
        return text[:_MAX_PROVIDER_TEXT] + "[TRUNCATED]"
    return text


def _suggested_test(originating_node: str) -> str:
    mapping = {
        "generation": "python -m pytest tests/unit/test_model_adapters.py tests/integration/test_default_humanize_e2e.py -q",
        "representation": "python -m pytest tests/unit/test_representation_atomicity.py tests/integration/test_runtime_dependencies.py -q",
        "regressions": "python -m pytest tests/regression tests/integration/test_acceptance_matrix.py -q",
        "cold_audit": "python -m pytest tests/integration/test_default_humanize_e2e.py -q",
        "detector": "python -m pytest tests/unit/test_pangram.py tests/integration/test_detector_downstream.py -q",
        "owner_learning": "python -m pytest tests/unit/test_owner_response.py tests/integration/test_owner_learning_resume.py -q",
        "repair": "python -m pytest tests/repair tests/integration/test_repair_resume.py -q",
    }
    return mapping.get(str(originating_node or ""), "python -m pytest -q")


def build_failure_evidence(
    *,
    record: FailureRecord,
    failure_class: FailureClass | str,
    state: dict[str, Any],
    exc: BaseException,
    store: ArtifactStore,
    program_version: str = "",
    event_context: dict[str, Any] | None = None,
    secret_values: Iterable[str] = (),
    failure_record_ref: str = "",
) -> RepairEvidenceBundle:
    secrets = tuple(str(value) for value in secret_values if str(value or ""))
    provider = str(getattr(exc, "provider", "") or "")
    role = str(getattr(exc, "role", "") or "")
    request_id = str(getattr(exc, "request_id", "") or "")
    expected_schema = dict(getattr(exc, "schema", None) or {})
    attempts: list[ProviderAttemptEvidence] = []
    for attempt in getattr(exc, "attempts", ()) or ():
        stdout_ref = str(getattr(attempt, "stdout_ref", "") or "")
        stderr_ref = str(getattr(attempt, "stderr_ref", "") or "")
        attempts.append(ProviderAttemptEvidence(
            provider=provider,
            model=str(getattr(attempt, "model", "") or ""),
            role=role,
            request_id=request_id,
            returncode=int(getattr(attempt, "returncode", 0) or 0),
            stdout_ref=stdout_ref,
            stderr_ref=stderr_ref,
            stdout_text=_bounded_artifact_text(store, stdout_ref, secrets),
            stderr_text=_bounded_artifact_text(store, stderr_ref, secrets),
            error=_redact(str(getattr(attempt, "error", "") or ""), secrets),
        ))

    safe_state = {
        "accepted_move_count": len(state.get("accepted_moves") or []),
        "move_index": int(state.get("move_index", 0) or 0),
        "retry_count": int(state.get("retry_count", 0) or 0),
        "rollback_count": int(state.get("rollback_count", 0) or 0),
        "status": str(state.get("status") or ""),
    }
    runtime_context = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
    }
    return RepairEvidenceBundle(
        failure_class=str(getattr(failure_class, "value", failure_class)),
        originating_node=record.originating_node,
        phase=str(state.get("phase") or record.originating_node),
        failure_code=_redact(record.failure_code, secrets),
        exception_type=record.exception_type or type(exc).__name__,
        exception_message=_redact(record.exception_message or str(exc), secrets),
        failure_record_ref=failure_record_ref,
        program_version=str(program_version or record.program_hash or state.get("program_version") or ""),
        thread_id=str(state.get("thread_id") or ""),
        checkpoint_id=str(state.get("checkpoint_id") or record.checkpoint_id or ""),
        source_hash=record.source_hash or str(state.get("source_hash") or ""),
        task_mode=str(state.get("task_mode") or ""),
        source_provenance=str(state.get("source_provenance") or ""),
        local_gate_state=dict(record.local_gate_state or state.get("final_local_gates") or {}),
        repair_attempt=int(state.get("repair_attempt", 0) or 0),
        authorial_information_missing=record.authorial_information_missing,
        provider=provider,
        role=role,
        request_id=request_id,
        expected_schema=expected_schema,
        provider_attempts=tuple(attempts),
        runtime_context=runtime_context,
        event_context=dict(event_context or {}),
        state_context=safe_state,
        suggested_test_command=_suggested_test(record.originating_node),
    )


def materialize_evidence_bundle(root: Path, bundle_text: str) -> Path:
    root = Path(root)
    evidence_dir = root / "supervisor-evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / "failure-evidence.json"
    # Validate JSON before writing so Codex never sees an accidentally concatenated log blob.
    parsed = json.loads(bundle_text)
    path.write_text(json.dumps(parsed, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path
