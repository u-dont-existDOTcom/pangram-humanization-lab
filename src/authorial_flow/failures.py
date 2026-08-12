from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, ConfigDict


class FailureClass(StrEnum):
    DETERMINISTIC_RUNTIME='DETERMINISTIC_RUNTIME'
    PROVIDER_PLUMBING='PROVIDER_PLUMBING'
    REGRESSION_ARCHITECTURE='REGRESSION_ARCHITECTURE'
    GENERATION_DEAD_END='GENERATION_DEAD_END'
    SEMANTIC_DEVELOPMENTAL='SEMANTIC_DEVELOPMENTAL'
    RESEARCH_PROVIDER='RESEARCH_PROVIDER'
    FIDELITY='FIDELITY'
    PANGRAM_ONLY='PANGRAM_ONLY'
    OWNER_JUDGMENT='OWNER_JUDGMENT'


class FailureRecord(BaseModel):
    model_config=ConfigDict(frozen=True)
    originating_node: str
    failure_code: str
    exception_type: str=''
    exception_message: str=''
    provider_attempt_refs: tuple[str,...]=()
    checkpoint_id: str=''
    source_hash: str=''
    program_hash: str=''
    local_gate_state: dict={}
    authorial_information_missing: bool=False


def classify_failure(record:FailureRecord)->FailureClass:
    code=record.failure_code.lower()
    node=record.originating_node.lower()
    if record.authorial_information_missing:
        return FailureClass.OWNER_JUDGMENT
    if any(x in code for x in ('timeout','provider','capacity','cli','subprocess','model unavailable','connection')):
        return FailureClass.PROVIDER_PLUMBING
    if any(x in code for x in ('missing schema','missing asset','syntaxerror','permission','checkpoint','sqlite')):
        return FailureClass.DETERMINISTIC_RUNTIME
    if 'regression' in code or node=='regressions':
        return FailureClass.REGRESSION_ARCHITECTURE
    if 'research provider' in code or node=='research':
        return FailureClass.RESEARCH_PROVIDER
    if 'pangram' in code or node=='detector':
        return FailureClass.PANGRAM_ONLY
    if 'fidelity' in code or node in {'fidelity','semantic_guard','relation_guard'}:
        return FailureClass.FIDELITY
    if 'dead end' in code or node=='generation':
        return FailureClass.GENERATION_DEAD_END
    if node in {'semantic_sanity','developmental'}:
        return FailureClass.SEMANTIC_DEVELOPMENTAL
    return FailureClass.DETERMINISTIC_RUNTIME
