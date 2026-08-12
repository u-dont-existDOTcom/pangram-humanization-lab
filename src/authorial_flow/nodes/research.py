from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Callable

from ..research.base import ResearchQuestion, ResearchProvider, Fetcher, RetrievedSource
from ..research.evidence import EvidenceRecord


@dataclass(frozen=True)
class ResearchNodeResult:
    faithful_position_ref: str
    better_reasoned_alternative_ref: str
    evidence: tuple[EvidenceRecord,...]
    sources: tuple[RetrievedSource,...]
    owner_position_changed: bool=False
    status: str='RESOLVED'


def run_bounded_research(
    question:ResearchQuestion, *, provider:ResearchProvider|None, fetcher:Fetcher,
    assessor:Callable[[ResearchQuestion,list[RetrievedSource]],list[EvidenceRecord]],
    faithful_position_ref:str,max_queries:int=2,max_sources:int=5,
)->ResearchNodeResult:
    if provider is None:
        return ResearchNodeResult(faithful_position_ref,'',(),(),False,'PROVIDER_UNAVAILABLE')
    query=(question.query or question.uncertainty).strip()
    hits=provider.search(query,limit=max_sources) if max_queries > 0 else []
    # Prefer direct/primary hints without creating a broad source inventory.
    hits=sorted(hits,key=lambda h:(not h.primary_hint,h.url))[:max_sources]
    sources=[]
    for hit in hits:
        sources.append(fetcher.fetch(hit.url))
    evidence=tuple(assessor(question,sources))
    alt_payload={
        'question':question.uncertainty,
        'evidence':[e.model_dump(mode='json') for e in evidence],
    }
    alt='research-alt:'+sha256(json.dumps(alt_payload,sort_keys=True).encode()).hexdigest() if evidence else ''
    return ResearchNodeResult(faithful_position_ref,alt,evidence,tuple(sources),False,'RESOLVED' if evidence else 'UNRESOLVED')
