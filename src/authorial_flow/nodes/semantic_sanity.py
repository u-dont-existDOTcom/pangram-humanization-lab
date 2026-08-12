from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..modes import TaskMode


@dataclass(frozen=True)
class SemanticSanityResult:
    status: str
    defect_types: tuple[str,...]=()
    material_questions: tuple[str,...]=()
    research_trigger: bool=False
    owner_question: str=''
    recommended_escalation: str='BASIC'


SUBSTANTIVE_DEFECTS={
    'wrong_thought','hidden_premise','actor_action_object','chronology','causality',
    'certainty','attribution','heading_function','source_role','should_not_survive'
}


def evaluate_semantic_sanity(signals:dict[str,Any], *, task_mode:TaskMode)->SemanticSanityResult:
    defects=tuple(k for k,v in signals.items() if bool(v) and k in SUBSTANTIVE_DEFECTS)
    if not defects:
        return SemanticSanityResult(status='PASS',recommended_escalation='BASIC')

    if task_mode is TaskMode.P2S:
        question='The source has a substantive thought-level conflict that style-only authority cannot resolve. Which meaning should control?'
        return SemanticSanityResult('FAIL',defects,owner_question=question,recommended_escalation='OWNER')

    if 'source_role' in defects and bool(signals.get('research_material',True)):
        return SemanticSanityResult(
            'FAIL',defects,research_trigger=True,
            material_questions=('Would resolving the source/evidence role materially change the thought?',),
            recommended_escalation='RESEARCH'
        )

    if 'wrong_thought' in defects or 'should_not_survive' in defects:
        return SemanticSanityResult('FAIL',defects,recommended_escalation='P4')
    return SemanticSanityResult('FAIL',defects,recommended_escalation='P3')
