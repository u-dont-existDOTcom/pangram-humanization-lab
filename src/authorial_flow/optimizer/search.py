from __future__ import annotations

import json
from typing import Callable, Any

from ..learning import LearningStore
from .program import ProgramBundle
from .evaluate import EvaluationScore


class OptimizerSearch:
    def __init__(self,*,proposer:Callable[[str,ProgramBundle],ProgramBundle|None],
                 evaluator:Callable[[ProgramBundle,str],EvaluationScore|None],max_rounds:int=6):
        self.proposer=proposer; self.evaluator=evaluator; self.max_rounds=max_rounds

    def build_proposal_input(self,store:LearningStore)->str:
        # hypothesis_view removes locked-test case bodies by construction.
        return json.dumps({'cases':store.hypothesis_view()},ensure_ascii=False,sort_keys=True)

    def partition_manifest(self,store:LearningStore)->str:
        counts={'dev':0,'validation':0,'locked-test':0}
        for rec in store.records(): counts[rec.partition]=counts.get(rec.partition,0)+1
        return json.dumps({'partitions':counts},sort_keys=True)

    def run(self,base_program:ProgramBundle,learning_store:LearningStore,rounds:int|None=None)->ProgramBundle|None:
        rounds=min(self.max_rounds,rounds if rounds is not None else self.max_rounds)
        proposal_input=self.build_proposal_input(learning_store)
        current=base_program
        for _ in range(rounds):
            proposal=self.proposer(proposal_input,current)
            if proposal is None: return None
            dev=self.evaluator(proposal,'dev')
            if dev is None or not dev.promotion_eligible:
                continue
            validation=self.evaluator(proposal,'validation')
            if validation is None or not validation.promotion_eligible:
                continue
            # Locked test is used only after proposal/validation. Its case bodies were never in proposal_input.
            locked=self.evaluator(proposal,'locked-test')
            if locked is None or not locked.promotion_eligible:
                continue
            return proposal
        return None
