from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RepairOutcome(StrEnum):
    APPLIED_VERIFIED = "APPLIED_VERIFIED"
    STAGED_FOR_OWNER = "STAGED_FOR_OWNER"
    REJECTED_WITH_REASON = "REJECTED_WITH_REASON"
    NON_APPLICABLE_STOP = "NON_APPLICABLE_STOP"


class RepairPlan(BaseModel):
    model_config=ConfigDict(frozen=True, extra='forbid')
    repairable: bool
    diagnosis: str
    patch_summary: str
    target_files: list[str]
    rationale: str
    tests: list[str] = Field(description="Exact local pytest commands; prose test descriptions are invalid")
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
