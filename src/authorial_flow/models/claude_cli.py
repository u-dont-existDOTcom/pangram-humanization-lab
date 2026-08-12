from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping

from ..artifacts import ArtifactStore
from ..pause import OperationContext
from ..process_runner import ProcessRunner, ProcessSpec
from ..secrets import child_env
from .common import (
    FailureKind, ModelAttempt, ModelCall, ModelResult, ProviderFailure,
    capability_signature, classify_attempt_failure, extract_json_object,
    stable_request_id, stops_provider_fallback, unique_model_profiles,
    validate_json_schema, validate_schema_contract,
)


class ClaudeCLI:
    def __init__(
        self,
        models: list[str],
        *,
        base_env: Mapping[str, str] | None = None,
        cli_version: str = "unknown",
        timeout_seconds: float = 1800,
    ) -> None:
        self.models = list(models)
        self.base_env = dict(base_env or os.environ)
        self.cli_version = cli_version
        self.timeout_seconds = timeout_seconds

    def call(self, call: ModelCall, runner: ProcessRunner, store: ArtifactStore) -> ModelResult:
        base_request_id = call.request_id or stable_request_id("claude", call.role, call.prompt, call.schema)
        attempts: list[ModelAttempt] = []
        safe_env = child_env(self.base_env, {"PANGRAM_API_KEY", "BRAVE_SEARCH_API_KEY"})
        request_text = call.prompt
        if call.schema:
            schema_text = json.dumps(call.schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            request_text += (
                "\n\nOUTPUT CONTRACT:\n"
                "Return exactly one JSON object matching this JSON Schema. "
                "Do not add prose, Markdown fences, or a second JSON object.\n"
                "JSON SCHEMA:\n" + schema_text
            )
        profiles = unique_model_profiles(self.models)
        try:
            validate_schema_contract(call.schema)
        except ValueError as exc:
            model = profiles[0] if profiles else ""
            attempts.append(ModelAttempt(
                str(model), -1, error=f"invalid schema: {type(exc).__name__}",
                failure_kind=FailureKind.INVALID_SCHEMA.value,
                capability_signature=capability_signature("claude", str(model), call.schema),
            ))
            raise ProviderFailure("claude", call.role, base_request_id, attempts, schema=call.schema) from exc
        for model in profiles:
            signature = capability_signature("claude", str(model), call.schema)
            argv = [
                "claude", "-p", "--output-format", "json", "--max-turns", "1",
                "--model", model,
                "Read stdin carefully and return only the requested representation.",
            ]
            result = runner.run(ProcessSpec(
                argv=argv, cwd=Path.cwd(), timeout_seconds=self.timeout_seconds,
                env=safe_env, input_text=request_text,
                operation=OperationContext(
                    operation="model_call",
                    provider="claude",
                    model=model,
                    role=call.role,
                    cancelable=True,
                ),
            ))
            out_ref = store.put_text(result.stdout, "stdout.txt", {
                "provider": "claude", "role": call.role, "request_id": base_request_id,
                "model": model, "stream": "stdout",
            }).sha256 if result.stdout else ""
            err_ref = store.put_text(result.stderr, "stderr.txt", {
                "provider": "claude", "role": call.role, "request_id": base_request_id,
                "model": model, "stream": "stderr",
            }).sha256 if result.stderr else ""
            if result.returncode != 0:
                kind = classify_attempt_failure(
                    returncode=result.returncode, stdout=result.stdout,
                    stderr=result.stderr, error="nonzero exit",
                )
                attempts.append(ModelAttempt(
                    model, result.returncode, out_ref, err_ref, "nonzero exit",
                    kind.value, signature,
                ))
                if stops_provider_fallback(kind):
                    break
                continue
            try:
                outer = json.loads(result.stdout)
                payload = outer.get("result", result.stdout) if isinstance(outer, dict) else result.stdout
                if call.schema:
                    parsed = extract_json_object(str(payload)) if isinstance(payload, str) else payload
                    validate_json_schema(parsed, call.schema)
                else:
                    parsed = payload
                resolved_model = outer.get("model") if isinstance(outer, dict) else None
                resolved_model = str(resolved_model or model)
            except Exception as exc:
                attempts.append(ModelAttempt(
                    model, result.returncode, out_ref, err_ref,
                    f"parse/schema: {type(exc).__name__}",
                    FailureKind.STRUCTURED_CONTRACT.value, signature,
                ))
                continue
            attempts.append(ModelAttempt(
                model, result.returncode, out_ref, err_ref, "", "", signature,
            ))
            return ModelResult(
                provider="claude", role=call.role, request_id=base_request_id,
                model=resolved_model, cli_version=self.cli_version, parsed=parsed,
                text=str(payload), stdout_ref=out_ref, stderr_ref=err_ref,
                attempts=tuple(attempts),
            )
        raise ProviderFailure("claude", call.role, base_request_id, attempts, schema=call.schema)
