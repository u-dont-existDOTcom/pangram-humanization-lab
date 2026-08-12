from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Callable


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def suite_identity(suite: dict) -> tuple[str, list[str]]:
    cases = suite.get("cases", [])
    ids = [str(case["id"]) for case in cases]
    if not ids or len(ids) != len(set(ids)):
        if cases:
            raise ValueError("regression case IDs must be unique")
    return sha256(canonical_json(suite).encode()).hexdigest(), ids


def cached_result_matches(record: dict, expected_hash: str, expected_ids: list[str]) -> bool:
    return bool(
        record.get("suite_sha256") == expected_hash
        and record.get("case_ids") == expected_ids
        and record.get("provenance_valid") is True
        and record.get("pass") is True
    )


@dataclass(frozen=True)
class RegressionSummary:
    owner_flow_pass: bool
    semantic_pass: bool
    positive_diagnostic_pass: bool | None = None

    @property
    def hard_pass(self) -> bool:
        return bool(self.owner_flow_pass and self.semantic_pass)


def provenance_record(
    suite: dict,
    *,
    program_version: str,
    provider: str,
    model: str,
    exit_code: int,
    stdout_ref: str = "",
    stderr_ref: str = "",
    result_ref: str = "",
    passed: bool,
    hard: bool,
) -> dict:
    suite_hash, case_ids = suite_identity(suite)
    return {
        "format":"authorial-flow-regression-result-v1",
        "suite_sha256": suite_hash,
        "case_ids": case_ids,
        "program_version": program_version,
        "provider": provider,
        "model": model,
        "exit_code": exit_code,
        "stdout_ref": stdout_ref,
        "stderr_ref": stderr_ref,
        "result_ref": result_ref,
        "provenance_valid": True,
        "hard": hard,
        "pass": bool(passed),
    }


def run_hard_regressions(owner_flow_runner: Callable[[], bool], semantic_runner: Callable[[], bool], positive_runner: Callable[[], bool] | None = None) -> RegressionSummary:
    owner = bool(owner_flow_runner())
    semantic = bool(semantic_runner())
    positive = bool(positive_runner()) if positive_runner else None
    return RegressionSummary(owner, semantic, positive)
