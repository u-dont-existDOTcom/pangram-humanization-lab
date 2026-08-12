from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RepairPlan(BaseModel):
    model_config=ConfigDict(frozen=True, extra='forbid')
    repairable: bool
    diagnosis: str
    patch_summary: str
    target_files: list[str]
    rationale: str
    tests: list[str]
    needs_owner_judgment: bool
    owner_question: str


class ReviewDecision(BaseModel):
    model_config=ConfigDict(frozen=True, extra='forbid')
    verdict: str
    reason: str
    required_changes: list[str]


class ImplementationResult(BaseModel):
    model_config=ConfigDict(frozen=True, extra='forbid')
    success: bool
    provider: str
    model: str=''
    returncode: int=0
    stdout_ref: str=''
    stderr_ref: str=''
    commit_sha: str=''
    transcript_ref: str=''
    red_ref: str=''
    green_ref: str=''
    proof_ref: str=''
