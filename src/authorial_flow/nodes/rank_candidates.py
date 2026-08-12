from __future__ import annotations

from dataclasses import dataclass

from ..candidates import CandidateRecord, choose_editorial_winner


@dataclass(frozen=True)
class EditorialRanking:
    order: tuple[str,...]
    winner_id: str
    material_differences: tuple[str,...]


def rank_candidates_blind(candidates:list[CandidateRecord]|tuple[CandidateRecord,...])->EditorialRanking:
    """Rank without exposing detector fields to the ranking decision."""
    if not candidates:
        raise ValueError('at least one candidate required')
    ranked=sorted(candidates,key=lambda c:(-c.editorial_score,c.id))
    winner=choose_editorial_winner(candidates)
    differences=[]
    base=winner.material_route
    for c in ranked:
        if c.id != winner.id and (c.material_route != base or c.owner_position_diverges != winner.owner_position_diverges):
            differences.append(f'{c.id}:{c.material_route}')
    return EditorialRanking(tuple(c.id for c in ranked),winner.id,tuple(differences))


def editorial_rank_payload(candidate:CandidateRecord)->dict:
    # Intentionally omit Pangram/detector refs.
    return {
        'id':candidate.id,'text':candidate.text,'role':candidate.role,
        'material_route':candidate.material_route,'editorial_score':candidate.editorial_score,
        'hard_pass':candidate.hard_pass,'claims_added':list(candidate.claims_added),
        'claims_removed':list(candidate.claims_removed),'certainty_changes':list(candidate.certainty_changes),
        'causal_role_changes':list(candidate.causal_role_changes),'source_replacements':list(candidate.source_replacements),
        'owner_position_diverges':candidate.owner_position_diverges,
    }
