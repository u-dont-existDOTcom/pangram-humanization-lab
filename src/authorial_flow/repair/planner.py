from __future__ import annotations

from typing import Any

from ..models.common import ModelCall
from .schemas import RepairPlan


class RepairPlanner:
    def __init__(self,*,codex:Any,runner:Any,store:Any):
        self.codex=codex; self.runner=runner; self.store=store

    def plan(self,failure_context:str)->RepairPlan:
        prompt=(
            'Design one small causal machine repair. Do not ask the owner to perform debugging, '
            'do not hardcode current article/source text, do not weaken owner authority, and do not '
            'optimize detector score at the expense of fidelity.\n\nFAILURE CONTEXT:\n'+failure_context
        )
        result=self.codex.call(ModelCall(
            prompt=prompt,schema=RepairPlan.model_json_schema(),role='repair_plan'
        ),self.runner,self.store)
        return RepairPlan.model_validate(result.parsed)
