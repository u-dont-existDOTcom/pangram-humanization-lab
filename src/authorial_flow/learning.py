from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Any


class LearningKind(StrEnum):
    LOCAL_EDGE='LOCAL_EDGE'
    STOP_BEFORE='STOP_BEFORE'
    GLOBAL_PRECOMPUTED_SHAPE='GLOBAL_PRECOMPUTED_SHAPE'
    MEANING_CORRECTION='MEANING_CORRECTION'
    VOICE_CORRECTION='VOICE_CORRECTION'
    SOURCE_ROLE_CORRECTION='SOURCE_ROLE_CORRECTION'
    RESEARCH_DIRECTION='RESEARCH_DIRECTION'
    OWNER_DIRECTION='OWNER_DIRECTION'


class LearningScope(StrEnum):
    PROJECT_AUTHORITY='PROJECT_AUTHORITY'
    REUSABLE_HYPOTHESIS='REUSABLE_HYPOTHESIS'
    GENERAL_RULE='GENERAL_RULE'
    RETIRED='RETIRED'


PARTITIONS={'dev','validation','locked-test'}


@dataclass(frozen=True)
class LearningRecord:
    id: str
    kind: LearningKind
    project_id: str
    scope: LearningScope
    body_sha256: str
    partition: str
    created_at: float
    payload: dict[str,Any]


@dataclass(frozen=True)
class PromotionResult:
    promoted: bool
    scope: LearningScope
    reason: str


def _canonical(obj:Any)->str:
    return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':'))


class LearningStore:
    def __init__(self,root:Path):
        self.root=Path(root)/'learning'
        self.body_dir=self.root/'bodies'
        self.events_path=self.root/'records.jsonl'

    def _append_event(self,event:dict[str,Any])->None:
        self.root.mkdir(parents=True,exist_ok=True)
        with self.events_path.open('a',encoding='utf-8') as f:
            f.write(json.dumps(event,sort_keys=True,ensure_ascii=False)+'\n')

    def _write_body(self,payload:dict[str,Any])->str:
        raw=_canonical(payload).encode()
        digest=sha256(raw).hexdigest()
        self.body_dir.mkdir(parents=True,exist_ok=True)
        p=self.body_dir/f'{digest}.json'
        if not p.exists():
            p.write_bytes(raw+b'\n')
        return digest

    def append_owner_judgment(self,*,kind:str|LearningKind,project_id:str,payload:dict[str,Any],partition:str='dev')->LearningRecord:
        kind=LearningKind(str(kind))
        if partition not in PARTITIONS:
            raise ValueError(f'unsupported partition: {partition}')
        digest=self._write_body(payload)
        now=time.time()
        rid=f'lr-{digest[:12]}-{time.time_ns()}'
        rec=LearningRecord(rid,kind,project_id,LearningScope.PROJECT_AUTHORITY,digest,partition,now,dict(payload))
        self._append_event({
            'event':'OWNER_JUDGMENT','record_id':rid,'kind':kind.value,'project_id':project_id,
            'scope':rec.scope.value,'body_sha256':digest,'partition':partition,'time':now,
        })
        return rec

    def append_hypothesis(self,*,kind:str|LearningKind,project_id:str,payload:dict[str,Any],partition:str='dev')->LearningRecord:
        kind=LearningKind(str(kind))
        if partition not in PARTITIONS:
            raise ValueError(f'unsupported partition: {partition}')
        digest=self._write_body(payload)
        now=time.time()
        rid=f'lr-{digest[:12]}-{time.time_ns()}'
        rec=LearningRecord(rid,kind,project_id,LearningScope.REUSABLE_HYPOTHESIS,digest,partition,now,dict(payload))
        self._append_event({
            'event':'HYPOTHESIS','record_id':rid,'kind':kind.value,'project_id':project_id,
            'scope':rec.scope.value,'body_sha256':digest,'partition':partition,'time':now,
        })
        return rec

    def _events(self)->list[dict[str,Any]]:
        if not self.events_path.exists(): return []
        return [json.loads(line) for line in self.events_path.read_text().splitlines() if line.strip()]

    def _body(self,digest:str)->dict[str,Any]:
        return json.loads((self.body_dir/f'{digest}.json').read_text())

    def records(self)->list[LearningRecord]:
        base={}
        scopes={}
        for event in self._events():
            if event.get('event') in {'OWNER_JUDGMENT','HYPOTHESIS'}:
                base[event['record_id']]=event
                scopes[event['record_id']]=LearningScope(event['scope'])
            elif event.get('event') in {'PROMOTION','RETIRE'}:
                scopes[event['record_id']]=LearningScope(event['scope'])
        out=[]
        for rid,event in base.items():
            out.append(LearningRecord(
                rid,LearningKind(event['kind']),event['project_id'],scopes[rid],event['body_sha256'],
                event['partition'],float(event['time']),self._body(event['body_sha256'])
            ))
        return out

    def get(self,record_id:str)->LearningRecord:
        for rec in self.records():
            if rec.id==record_id: return rec
        raise KeyError(record_id)

    def promote(self,record_id:str,evidence_refs:list[str],explicit_owner_confirmation:bool=False)->PromotionResult:
        rec=self.get(record_id)
        if rec.payload.get('personal_fact') is True:
            return PromotionResult(False,rec.scope,'personal facts/positions never become style rules')
        if rec.kind in {LearningKind.MEANING_CORRECTION,LearningKind.SOURCE_ROLE_CORRECTION,LearningKind.RESEARCH_DIRECTION} and rec.payload.get('article_specific',False):
            return PromotionResult(False,rec.scope,'article-specific substantive judgment remains project authority')
        usable=[r for r in evidence_refs if not str(r).startswith(('synthetic:','model-positive:'))]
        has_validation=any(str(r).startswith(('validation:','holdout:')) for r in usable)
        enough=explicit_owner_confirmation or (len(usable)>=2 and has_validation)
        if not enough:
            return PromotionResult(False,rec.scope,'needs repeated owner-supported evidence plus held-out validation, or explicit owner confirmation')
        scope=LearningScope.GENERAL_RULE
        self._append_event({
            'event':'PROMOTION','record_id':record_id,'scope':scope.value,
            'evidence_refs':usable,'explicit_owner_confirmation':explicit_owner_confirmation,'time':time.time(),
        })
        return PromotionResult(True,scope,'promotion requirements satisfied')

    def promoted_rules(self)->list[dict[str,str]]:
        rules=[]
        for rec in self.records():
            if rec.scope is not LearningScope.GENERAL_RULE:
                continue
            rule=str(rec.payload.get('abstract_rule') or '').strip()
            if rule:
                rules.append({'id':rec.id,'rule':rule})
        return rules

    def hypothesis_view(self)->list[dict[str,Any]]:
        # Locked-test bodies are never exposed to hypothesis-generating components.
        return [
            {'id':r.id,'kind':r.kind.value,'scope':r.scope.value,'partition':r.partition,'payload':r.payload}
            for r in self.records() if r.partition != 'locked-test'
        ]
