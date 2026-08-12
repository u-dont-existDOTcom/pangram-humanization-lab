from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel, ConfigDict

from ..authority import Authority, AuthorityUnit


class ArchitectureCard(BaseModel):
    model_config=ConfigDict(frozen=True, extra='forbid')
    heading_promise: str=''
    real_pressure: str=''
    reader_stake: str=''
    controlling_claim: str=''
    certainty: str=''
    motive_obligation: str=''
    intellectual_lived_route: tuple[str,...]=()
    actor_action_object: tuple[str,...]=()
    causality_chronology: tuple[str,...]=()
    source_landscape: tuple[str,...]=()
    strongest_complication: str=''
    governing_movement: str=''
    paragraph_jobs: tuple[str,...]=()
    stopping_point: str=''
    exact_language_reasons: tuple[str,...]=()


@dataclass(frozen=True)
class DevelopmentalResult:
    original_units: tuple[AuthorityUnit,...]
    corrected_units: tuple[dict[str,Any],...]
    architecture_card: ArchitectureCard
    architecture_card_ref: str=''
    faithful_position_ref: str=''
    alternative_ref: str=''
    unresolved_authorial: tuple[str,...]=()
    candidate_only: bool=False


def validate_developmental_result(units:list[AuthorityUnit]|tuple[AuthorityUnit,...],
                                  proposed:list[dict[str,Any]]|tuple[dict[str,Any],...])->list[str]:
    by_id={str(row.get('id')):row for row in proposed}
    errors=[]
    for unit in units:
        row=by_id.get(unit.id)
        if unit.must_preserve:
            if row is None or row.get('disposition') in {'omit','drop','remove','bank'}:
                errors.append(f'{unit.id}: owner-authority unit cannot be dropped')
                continue
            if unit.exact_lock and row.get('text') not in {None,unit.text}:
                errors.append(f'{unit.id}: exact-lock text changed')
        if row is not None and row.get('disposition') in {'omit','drop','remove','bank'} and not str(row.get('reason') or '').strip():
            errors.append(f'{unit.id}: omission requires reason')
    # Unknown proposed IDs are provenance errors rather than silently-created source units.
    known={u.id for u in units}
    for row in proposed:
        rid=str(row.get('id') or '')
        if rid and rid not in known and str(row.get('origin') or '') not in {'approved_addition','research_candidate','owner_addition'}:
            errors.append(f'{rid}: new unit requires explicit origin')
    return errors


def build_developmental_result(units:list[AuthorityUnit],proposed:list[dict[str,Any]],*,
                               card:ArchitectureCard,owner_position_changed:bool=False,
                               faithful_position_ref:str='',alternative_ref:str='')->DevelopmentalResult:
    errors=validate_developmental_result(units,proposed)
    if errors:
        if not owner_position_changed:
            raise ValueError('; '.join(errors))
        locked_ids={u.id for u in units if u.authority is Authority.OWNER_LOCKED}
        locked_errors=[e for e in errors if e.split(':',1)[0] in locked_ids]
        if locked_errors:
            raise ValueError('; '.join(locked_errors))
    unresolved=tuple(u.id for u in units if u.authority is Authority.OPEN_AUTHORIAL and not any(p.get('id')==u.id for p in proposed))
    return DevelopmentalResult(
        tuple(units),tuple(dict(p) for p in proposed),card,
        faithful_position_ref=faithful_position_ref,alternative_ref=alternative_ref,
        unresolved_authorial=unresolved,candidate_only=owner_position_changed,
    )
