from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any


def _hash_text(value:str)->str:
    return sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class ProgramBundle:
    id: str
    prompt_hashes: dict[str,str]
    evaluator_config: dict[str,Any]
    graph_compatibility: str
    parent_id: str=''

    @classmethod
    def build(cls,prompts:dict[str,str],evaluator_config:dict[str,Any],*,graph_compatibility:str,parent_id:str='')->'ProgramBundle':
        hashes={name:_hash_text(text) for name,text in sorted(prompts.items())}
        payload={'prompt_hashes':hashes,'evaluator_config':evaluator_config,'graph_compatibility':graph_compatibility,'parent_id':parent_id}
        pid=sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return cls(pid,hashes,dict(evaluator_config),graph_compatibility,parent_id)
