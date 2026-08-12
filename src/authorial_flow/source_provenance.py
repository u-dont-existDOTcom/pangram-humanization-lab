from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, ConfigDict
from typing import Any


class SourceProvenance(StrEnum):
    OWNER_FINAL='OWNER_FINAL'
    OWNER_DRAFT='OWNER_DRAFT'
    AI_FROM_OWNER_INPUTS='AI_FROM_OWNER_INPUTS'
    MIXED='MIXED'
    SOURCE_POOL='SOURCE_POOL'
    RESEARCH_PROVISIONAL='RESEARCH_PROVISIONAL'


class ProvenanceResult(BaseModel):
    model_config=ConfigDict(frozen=True)
    provenance: SourceProvenance
    evidence_spans: tuple[str,...]=()
    reason: str=''


def classify_provenance(text:str, *, metadata:dict[str,Any]|None=None)->ProvenanceResult:
    metadata=metadata or {}
    override=metadata.get('provenance_override')
    if override:
        return ProvenanceResult(provenance=SourceProvenance(str(override)),reason='deterministic project override')
    kind=str(metadata.get('source_kind') or '').lower()
    if kind in {'owner-final','owner_final','locked'}:
        return ProvenanceResult(provenance=SourceProvenance.OWNER_FINAL,reason='metadata marks owner-final source')
    if kind in {'notes','interview','source-pool','source_pool'}:
        return ProvenanceResult(provenance=SourceProvenance.SOURCE_POOL,reason='metadata marks notes/source pool')
    if kind in {'ai-from-owner-inputs','ai_from_owner_inputs'}:
        return ProvenanceResult(provenance=SourceProvenance.AI_FROM_OWNER_INPUTS,reason='metadata marks AI realization of owner inputs')
    if kind == 'mixed':
        return ProvenanceResult(provenance=SourceProvenance.MIXED,reason='metadata marks mixed provenance')
    return ProvenanceResult(provenance=SourceProvenance.OWNER_DRAFT,reason='conservative default when provenance is not pinned')
