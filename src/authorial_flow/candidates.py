from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class CandidateRecord:
    id: str
    text: str
    editorial_score: float
    pangram: dict[str, Any] | None = None
    hard_pass: bool = True
    lineage_id: str = "root"
    parent_id: str | None = None
    meaning_equivalent: bool = True
    frozen: bool = False
    accepted_moves: tuple[str, ...] = ()
    authority_disposition_ref: str = ""
    audit_refs: tuple[str, ...] = ()
    text_artifact_ref: str = ""
    role: str = "CONSERVATIVE"
    material_route: str = "default"
    claims_added: tuple[str, ...] = ()
    claims_removed: tuple[str, ...] = ()
    certainty_changes: tuple[str, ...] = ()
    causal_role_changes: tuple[str, ...] = ()
    source_replacements: tuple[str, ...] = ()
    owner_position_diverges: bool = False

    @property
    def text_sha256(self) -> str:
        return sha256(self.text.encode()).hexdigest()


@dataclass(frozen=True)
class CandidateLineage:
    root_id: str
    first_human_id: str | None = None

    def freeze_first_human(self, candidate_id: str) -> "CandidateLineage":
        if self.first_human_id is not None:
            return self
        return replace(self, first_human_id=candidate_id)


@dataclass(frozen=True)
class CandidatePresentation:
    recommended: CandidateRecord
    alternatives: tuple[CandidateRecord, ...] = ()


def choose_editorial_winner(candidates: list[CandidateRecord] | tuple[CandidateRecord, ...]) -> CandidateRecord:
    if not candidates:
        raise ValueError("at least one candidate is required")
    # Detector status is deliberately absent from ranking.
    return max(candidates, key=lambda c: (c.editorial_score, c.id))


def freeze_editorial_winner(candidates: list[CandidateRecord] | tuple[CandidateRecord, ...]) -> CandidateRecord:
    winner=choose_editorial_winner(candidates)
    return replace(winner, frozen=True)


@dataclass(frozen=True)
class PresentationSet:
    recommended_id: str
    alternatives: list[str]


def select_presentation(candidates: list[CandidateRecord] | tuple[CandidateRecord, ...]) -> PresentationSet:
    if not candidates:
        raise ValueError("at least one candidate is required")
    winner=choose_editorial_winner(candidates)
    alternatives=[]
    seen_routes={winner.material_route}
    for candidate in sorted(candidates,key=lambda c:(-c.editorial_score,c.id)):
        if candidate.id == winner.id:
            continue
        materially_different=(
            candidate.material_route not in seen_routes
            or candidate.owner_position_diverges != winner.owner_position_diverges
            or candidate.role == "BETTER_REASONED_ALTERNATIVE"
        )
        if materially_different:
            alternatives.append(candidate.id)
            seen_routes.add(candidate.material_route)
        if len(alternatives) >= 2:
            break
    return PresentationSet(winner.id,alternatives)
