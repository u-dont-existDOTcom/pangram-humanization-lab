from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, ConfigDict


class AccessLevel(StrEnum):
    FULL_TEXT='full_text'
    ABSTRACT='abstract'
    SNIPPET='snippet'
    SECONDHAND='secondhand'


class EvidenceRecord(BaseModel):
    model_config=ConfigDict(frozen=True, extra='forbid')
    source_ref: str
    access_level: AccessLevel
    primary_status: str
    supports: list[str]
    resists: list[str]
    system_inference: list[str]


class ResearchSummary(BaseModel):
    model_config=ConfigDict(frozen=True, extra='forbid')
    question: str
    material_consequence: str
    evidence: tuple[EvidenceRecord,...]
    stable: bool
    access_limits: tuple[str,...]=()
