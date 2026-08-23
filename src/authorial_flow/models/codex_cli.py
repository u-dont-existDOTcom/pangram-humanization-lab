from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from typing import Any, Mapping

from ..artifacts import ArtifactStore
from ..pause import OperationContext
from ..process_runner import ProcessRunner, ProcessSpec
from ..secrets import child_env
from .common import (
    FailureKind, ModelAttempt, ModelCall, ModelResult, ProviderFailure,
    capability_signature, classify_attempt_failure, stable_request_id,
    stops_provider_fallback, unique_model_profiles, validate_json_schema,
    validate_schema_contract,
)


_NO_OWNER_QUESTION_EXACT = {
    "none",
    "none.",
    "no owner question",
    "no owner question.",
    "no owner questions",
    "no owner questions.",
    "no unresolved owner question",
    "no unresolved owner question.",
    "no unresolved owner questions",
    "no unresolved owner questions.",
}


def _normalize_representation_output(parsed: Any, role: str) -> Any:
    """Normalize only explicit no-question sentinels from representation output.

    This is deliberately conservative. A nonempty owner question remains untouched unless
    the model has explicitly said there is no question. In particular, generic strings
    beginning with "no" are never erased merely because of their prefix.
    """
    if role != "representation" or not isinstance(parsed, dict):
        return parsed
    sanity = parsed.get("semantic_sanity")
    if not isinstance(sanity, dict):
        return parsed
    raw = str(sanity.get("owner_question") or "").strip()
    if not raw:
        return parsed
    folded = " ".join(raw.casefold().split())
    explicit_none = folded in _NO_OWNER_QUESTION_EXACT
    observed_machine_resolvable_none = (
        folded.startswith("none.")
        and "owner context resolves" in folded
        and "machine-resolvable" in folded
    )
    if not (explicit_none or observed_machine_resolvable_none):
        return parsed
    normalized = dict(parsed)
    normalized_sanity = dict(sanity)
    normalized_sanity["owner_question"] = ""
    normalized["semantic_sanity"] = normalized_sanity
    return normalized


def _codex_output_schema(schema: dict[str, Any] | None) -> dict[str, Any]:
    """Translate the local semantic schema into Codex's strict output-schema subset.

    The runtime's Pydantic-derived schemas can contain Python-default metadata and optional
    object properties. Codex/OpenAI structured output requires closed objects with every
    property named in ``required``.  This provider-only projection therefore strips default
    metadata and requires every declared property while leaving the original schema untouched
    for local validation of the returned value.
    """
    projected: dict[str, Any] = json.loads(json.dumps(schema or {"type": "object"}))

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            node.pop("default", None)
            node.pop("title", None)
            if node.get("type") == "object":
                properties = node.get("properties")
                if isinstance(properties, dict):
                    node["additionalProperties"] = False
                    node["required"] = list(properties)
            for key, value in list(node.items()):
                if key in {"required", "enum"}:
                    continue
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(projected)
    return projected


class CodexCLI:
    def __init__(
        self,
        models: list[str | None],
        *,
        base_env: Mapping[str, str] | None = None,
        cli_version: str = "unknown",
        timeout_seconds: float = 1800,
        reasoning_effort: str = "high",
    ) -> None:
        self.models = list(models)
        self.base_env = dict(base_env or os.environ)
        self.cli_version = cli_version
        self.timeout_seconds = timeout_seconds
        self.reasoning_effort = reasoning_effort

    def call(self, call: ModelCall, runner: ProcessRunner, store: ArtifactStore) -> ModelResult:
        request_id = call.request_id or stable_request_id("codex", call.role, call.prompt, call.schema)
        attempts: list[ModelAttempt] = []
        safe_env = child_env(self.base_env, {"PANGRAM_API_KEY", "BRAVE_SEARCH_API_KEY"})
        profiles = unique_model_profiles(self.models)
        try:
            validate_schema_contract(call.schema)
            provider_schema = _codex_output_schema(call.schema)
            validate_schema_contract(provider_schema)
        except ValueError as exc:
            model = profiles[0] if profiles else None
            resolved = model or "CLI-default"
            attempts.append(ModelAttempt(
                resolved, -1, error=f"invalid schema: {type(exc).__name__}",
                failure_kind=FailureKind.INVALID_SCHEMA.value,
                capability_signature=capability_signature("codex", resolved, call.schema),
            ))
            raise ProviderFailure("codex", call.role, request_id, attempts, schema=call.schema) from exc
        tmp_root = store.root / "tmp" / request_id
        if tmp_root.exists():
            shutil.rmtree(tmp_root)
        tmp_root.mkdir(parents=True, exist_ok=True)
        try:
            schema_path = tmp_root / "schema.json"
            schema_path.write_text(json.dumps(provider_schema, sort_keys=True, indent=2), encoding="utf-8")
            for model in profiles:
                resolved = model or "CLI-default"
                signature = capability_signature("codex", resolved, call.schema)
                output_path = tmp_root / f"output-{len(attempts)+1}.json"
                argv = [
                    "codex", "exec", "--ephemeral", "--sandbox", "read-only",
                    "--skip-git-repo-check", "--config", f'model_reasoning_effort="{self.reasoning_effort}"',
                    "--output-schema", str(schema_path), "--output-last-message", str(output_path),
                ]
                if model:
                    argv.extend(["--model", model])
                argv.append("-")
                result = runner.run(ProcessSpec(
                    argv=argv, cwd=Path.cwd(), timeout_seconds=self.timeout_seconds,
                    env=safe_env, input_text=call.prompt,
                    operation=OperationContext(
                        operation="model_call",
                        provider="codex",
                        model=model or "CLI-default",
                        role=call.role,
                        cancelable=True,
                    ),
                ))
                out_ref = store.put_text(result.stdout, "stdout.txt", {
                    "provider": "codex", "role": call.role, "request_id": request_id,
                    "model": model or "CLI-default", "stream": "stdout",
                }).sha256 if result.stdout else ""
                err_ref = store.put_text(result.stderr, "stderr.txt", {
                    "provider": "codex", "role": call.role, "request_id": request_id,
                    "model": model or "CLI-default", "stream": "stderr",
                }).sha256 if result.stderr else ""
                if result.returncode != 0 or not output_path.exists():
                    error = "nonzero exit" if result.returncode != 0 else "missing structured output"
                    kind = classify_attempt_failure(
                        returncode=result.returncode, stdout=result.stdout,
                        stderr=result.stderr, error=error,
                    )
                    attempts.append(ModelAttempt(
                        resolved, result.returncode, out_ref, err_ref, error,
                        kind.value, signature,
                    ))
                    if stops_provider_fallback(kind):
                        break
                    continue
                try:
                    parsed = json.loads(output_path.read_text(encoding="utf-8"))
                    validate_json_schema(parsed, call.schema)
                    parsed = _normalize_representation_output(parsed, call.role)
                except Exception as exc:
                    attempts.append(ModelAttempt(
                        resolved, result.returncode, out_ref, err_ref,
                        f"parse/schema: {type(exc).__name__}",
                        FailureKind.STRUCTURED_CONTRACT.value, signature,
                    ))
                    continue
                raw_ref = store.put_bytes(output_path.read_bytes(), "json", {
                    "provider": "codex", "role": call.role, "request_id": request_id,
                    "model": resolved, "kind": "structured-output",
                }).sha256
                attempts.append(ModelAttempt(
                    resolved, result.returncode, out_ref, err_ref, "", "", signature,
                ))
                return ModelResult(
                    provider="codex", role=call.role, request_id=request_id,
                    model=resolved, cli_version=self.cli_version, parsed=parsed,
                    text=output_path.read_text(encoding="utf-8"), stdout_ref=out_ref or raw_ref,
                    stderr_ref=err_ref, attempts=tuple(attempts),
                )
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)
        raise ProviderFailure("codex", call.role, request_id, attempts, schema=call.schema)
