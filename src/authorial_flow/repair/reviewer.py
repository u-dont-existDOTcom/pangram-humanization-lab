from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..models.common import ModelCall, ProviderFailure
from .schemas import RepairPlan, ReviewDecision


class RepairReviewFailure(RuntimeError):
    def __init__(self,message:str):
        self.authorial_information_missing=False
        super().__init__(message)


@dataclass(frozen=True)
class ReviewedDecision:
    decision: ReviewDecision
    provider: str
    model: str=''


class RepairReviewer:
    def __init__(self,*,claude:Any,codex:Any,runner:Any,store:Any):
        self.claude=claude; self.codex=codex; self.runner=runner; self.store=store

    def _call(self,prompt:str,role:str)->ReviewedDecision:
        call=ModelCall(prompt=prompt,schema=ReviewDecision.model_json_schema(),role=role)
        try:
            result=self.claude.call(call,self.runner,self.store)
            return ReviewedDecision(ReviewDecision.model_validate(result.parsed),'claude',result.model)
        except (ProviderFailure,RuntimeError):
            try:
                result=self.codex.call(call,self.runner,self.store)
                return ReviewedDecision(ReviewDecision.model_validate(result.parsed),'codex-fallback',result.model)
            except (ProviderFailure,RuntimeError) as exc:
                raise RepairReviewFailure('all machine review providers failed') from exc

    def review_plan(self,plan:RepairPlan)->ReviewedDecision:
        prompt=(
            'Review this machine repair plan. Reject owner courier/debug work, source hardcoding, '
            'authority weakening, broad unrelated refactors, or detector-only degradation. '
            'Approve only a bounded general repair.\n\nPLAN:\n'+plan.model_dump_json(indent=2)
        )
        return self._call(prompt,'repair_plan_review')

    def review_diff(self,plan:RepairPlan,diff_text:str,test_summary:str='')->ReviewedDecision:
        prompt=(
            'Review the actual repair diff against the approved plan. Reject protected-data mutation, '
            'source-specific hardcoding, unrelated refactors, checkpoint/credential regression, '
            'authority weakening, or detector-only degradation.\n\nPLAN:\n'
            +plan.model_dump_json(indent=2)+'\n\nTESTS:\n'+test_summary+'\n\nDIFF:\n'+diff_text[:80000]
        )
        return self._call(prompt,'repair_diff_review')
