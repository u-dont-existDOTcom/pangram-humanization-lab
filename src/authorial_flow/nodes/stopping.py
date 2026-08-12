from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re

from ..authority import Authority, AuthorityUnit
from .pressure import CommittedPressure


@dataclass(frozen=True)
class StopDecision:
    action: str
    reason: str
    unresolved_required: tuple[str, ...] = ()
    provisional_dispositions: tuple[str, ...] = ()


def decide_stop(pressure: CommittedPressure, units: list[AuthorityUnit]) -> StopDecision:
    if pressure.state != "NATURAL_STOP":
        return StopDecision("CONTINUE", "thought remains open")
    required = tuple(u.id for u in units if u.must_preserve and u.disposition == "unresolved")
    if required:
        return StopDecision("ROLLBACK", "natural endpoint arrived before protected meaning was placed", required)
    provisional = tuple(
        u.id for u in units
        if u.disposition == "unresolved" and u.authority in {Authority.AI_PROVISIONAL, Authority.RESEARCH_PROVISIONAL}
    )
    return StopDecision("STOP", "thought arrived; unresolved provisional material is not mandatory", (), provisional)


def branch_hash(pressure: CommittedPressure, candidate: str, failure_class: str) -> str:
    normalized = re.sub(r"\s+", " ", candidate).strip().lower()
    payload = json.dumps({
        "state": pressure.state,
        "live_pressure": pressure.live_pressure,
        "candidate": normalized,
        "failure_class": failure_class,
    }, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode()).hexdigest()
