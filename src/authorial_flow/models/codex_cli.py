from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from typing import Mapping

from ..artifacts import ArtifactStore
from ..pause import OperationContext
from ..process_runner import ProcessRunner, ProcessSpec
from ..secrets import child_env
from .common import (
    ModelAttempt, ModelCall, ModelResult, ProviderFailure, stable_request_id,
    validate_json_schema,
)


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
        tmp_root = store.root / "tmp" / request_id
        if tmp_root.exists():
            shutil.rmtree(tmp_root)
        tmp_root.mkdir(parents=True, exist_ok=True)
        try:
            schema_path = tmp_root / "schema.json"
            schema_path.write_text(json.dumps(call.schema or {"type": "object"}, sort_keys=True, indent=2), encoding="utf-8")
            for model in self.models:
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
                resolved = model or "CLI-default"
                if result.returncode != 0 or not output_path.exists():
                    attempts.append(ModelAttempt(resolved, result.returncode, out_ref, err_ref, "nonzero exit or missing output"))
                    continue
                try:
                    parsed = json.loads(output_path.read_text(encoding="utf-8"))
                    validate_json_schema(parsed, call.schema)
                except Exception as exc:
                    attempts.append(ModelAttempt(resolved, result.returncode, out_ref, err_ref, f"parse/schema: {type(exc).__name__}"))
                    continue
                raw_ref = store.put_bytes(output_path.read_bytes(), "json", {
                    "provider": "codex", "role": call.role, "request_id": request_id,
                    "model": resolved, "kind": "structured-output",
                }).sha256
                attempts.append(ModelAttempt(resolved, result.returncode, out_ref, err_ref, ""))
                return ModelResult(
                    provider="codex", role=call.role, request_id=request_id,
                    model=resolved, cli_version=self.cli_version, parsed=parsed,
                    text=output_path.read_text(encoding="utf-8"), stdout_ref=out_ref or raw_ref,
                    stderr_ref=err_ref, attempts=tuple(attempts),
                )
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)
        raise ProviderFailure("codex", call.role, request_id, attempts, schema=call.schema)
