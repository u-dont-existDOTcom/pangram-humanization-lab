from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from ..candidates import CandidateLineage, CandidatePresentation, CandidateRecord


@dataclass(frozen=True)
class DetectorOutcome:
    status: str
    candidate: CandidateRecord
    lineage: CandidateLineage
    result: Any = None


def detector_node(
    candidate: CandidateRecord,
    client: Any,
    *,
    parent: CandidateRecord | None = None,
    lineage: CandidateLineage | None = None,
    pending: dict[str,str] | None = None,
) -> DetectorOutcome:
    lineage=lineage or CandidateLineage(root_id=candidate.lineage_id)
    if not candidate.hard_pass:
        return DetectorOutcome("SKIPPED_LOCAL_FAILURE",candidate,lineage)
    if parent is not None and (not candidate.meaning_equivalent or candidate.lineage_id != parent.lineage_id):
        return DetectorOutcome("REJECTED_SEMANTIC_DELTA",candidate,lineage)
    result=client.evaluate(candidate.text,candidate.text_sha256,pending=pending)
    pangram={
        "stage":result.stage,
        "version":result.version,
        "prediction_short":result.prediction_short,
        "fraction_ai":result.fraction_ai,
        "fraction_ai_assisted":result.fraction_ai_assisted,
        "is_human":result.is_human,
    }
    measured=replace(candidate,pangram=pangram)
    if result.is_human:
        lineage=lineage.freeze_first_human(candidate.id)
        return DetectorOutcome("HUMAN",measured,lineage,result)
    return DetectorOutcome("NON_HUMAN",measured,lineage,result)


def choose_presentation(editorial_winner: CandidateRecord, variants: list[CandidateRecord]) -> CandidatePresentation:
    # The editorial winner remains recommended regardless of detector status.
    useful=tuple(
        sorted(
            (v for v in variants if (v.pangram or {}).get("prediction_short","" ).lower()=="human"),
            key=lambda v:(-v.editorial_score,v.id),
        )
    )
    return CandidatePresentation(editorial_winner,useful[:2])
