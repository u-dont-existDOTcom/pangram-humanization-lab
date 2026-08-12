from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from ..modes import TaskMode


P1_ALLOWED={
    'spelling','grammar','punctuation','spacing','literal_agreement','broken_link','obvious_ambiguity'
}
P2_ALLOWED=P1_ALLOWED|{'clarity','rhythm','repetition','local_voice'}
P2S_PROHIBITED_PREFIXES=(
    'claim_','certainty_','actor_','causal_','recommendation_','factual_','allegation_',
    'link_','media_','coined_term_','catchphrase_','personal_history_','research_'
)
P2_PROHIBITED={
    'argument_order_changed','example_deleted','example_added','emotional_temperature_changed',
    'locked_line_changed','paragraph_order_changed','section_order_changed','claim_deleted','claim_added',
    'certainty_changed','causality_changed','actor_changed','link_anchor_changed','media_changed'
}


@dataclass(frozen=True)
class ChangeLedger:
    mode: str
    source_hash: str
    candidate_hash: str | None
    deltas: tuple[dict[str,Any],...]


@dataclass(frozen=True)
class ConservativeResult:
    status: str
    mode: TaskMode
    candidate_ref: str | None
    report_ref: str | None
    change_ledger_ref: str
    hard_violations: tuple[str,...]
    writer_call_count: int=0
    research_call_count: int=0


def _hash(text:str|None)->str|None:
    return sha256(text.encode()).hexdigest() if text is not None else None


def _allowed(mode:TaskMode,key:str)->bool:
    if mode is TaskMode.P0:
        return False
    if mode is TaskMode.P1:
        return key in P1_ALLOWED
    if mode is TaskMode.P2:
        return key in P2_ALLOWED and key not in P2_PROHIBITED
    if mode is TaskMode.P2S:
        if key in {'paragraph_order_changed','section_order_changed','sentence_architecture','transitions','humor','paragraphing'}:
            return True
        return not any(key.startswith(prefix) for prefix in P2S_PROHIBITED_PREFIXES) and key not in {
            'claim_deleted','claim_added','certainty_changed','causality_changed','actor_changed',
            'recommendation_changed','link_anchor_changed','media_changed'
        }
    return True


def build_change_ledger(mode:TaskMode,source:str,candidate:str|None,changes:dict[str,Any])->ChangeLedger:
    deltas=tuple(
        {'kind':key,'value':value,'allowed':_allowed(mode,key)}
        for key,value in changes.items() if bool(value)
    )
    return ChangeLedger(mode.value,_hash(source) or '',_hash(candidate),deltas)


def execute_mode(mode:TaskMode, *, source:str, candidate:str|None, changes:dict[str,Any],
                 report_text:str|None=None)->ConservativeResult:
    if mode is TaskMode.P0:
        ledger=build_change_ledger(mode,source,None,{})
        return ConservativeResult('REPORT_ONLY',mode,None,report_text or '',json.dumps(ledger.__dict__,default=list),(),0,0)
    ledger=build_change_ledger(mode,source,candidate,changes)
    violations=tuple(str(d['kind']) for d in ledger.deltas if not d['allowed'])
    status='MODE_VIOLATION' if violations else 'PASS'
    return ConservativeResult(
        status,mode,_hash(candidate) if candidate is not None else None,None,
        json.dumps(ledger.__dict__,sort_keys=True,default=list),violations,
        writer_call_count=1 if candidate is not None else 0,
        research_call_count=0 if mode in {TaskMode.P1,TaskMode.P2,TaskMode.P2S} else 0,
    )
