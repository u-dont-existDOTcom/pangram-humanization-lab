from __future__ import annotations

from dataclasses import replace
from typing import Callable

from ..candidates import CandidateRecord
from .cold_audit import ColdAuditResult


def revise_only_for_defects(
    candidate: CandidateRecord,
    audit: ColdAuditResult,
    reviser: Callable[[CandidateRecord, ColdAuditResult], str],
) -> CandidateRecord:
    if audit.pass_:
        return candidate
    revised=reviser(candidate,audit)
    return replace(
        candidate,
        id=f"{candidate.id}-r",
        text=revised,
        parent_id=candidate.id,
        frozen=False,
        pangram=None,
    )
