from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Literal

PressureState = Literal["OPEN", "NATURAL_STOP", "AMBIGUOUS"]


@dataclass(frozen=True)
class PressureVote:
    state: PressureState
    confidence: float
    live_pressure: str
    previous_move_function: str = ""
    already_settled: tuple[str, ...] = ()
    backward_reopen_risks: tuple[str, ...] = ()
    why_stop_might_be_natural: str = ""
    provider: str = ""


@dataclass(frozen=True)
class CommittedPressure:
    state: PressureState
    confidence: float
    live_pressure: str
    votes: tuple[PressureVote, ...]
    rationale: str


def commit_pressure(votes: list[PressureVote] | tuple[PressureVote, ...]) -> CommittedPressure:
    if not votes:
        raise ValueError("at least one pressure vote required")
    votes = tuple(votes)
    credible_open = [v for v in votes if v.state == "OPEN" and v.confidence >= 0.60]
    if credible_open:
        chosen = max(credible_open, key=lambda v: v.confidence)
        return CommittedPressure("OPEN", chosen.confidence, chosen.live_pressure, votes, "credible OPEN vote vetoes stopping")

    natural = [v for v in votes if v.state == "NATURAL_STOP"]
    if len(natural) == len(votes) and min(v.confidence for v in natural) >= 0.78:
        chosen = max(natural, key=lambda v: v.confidence)
        return CommittedPressure("NATURAL_STOP", min(v.confidence for v in natural), chosen.live_pressure, votes, "cross-reader natural-stop agreement")

    if natural:
        strongest = max(natural, key=lambda v: v.confidence)
        competitors = [v for v in votes if v is not strongest]
        if strongest.confidence >= 0.93 and all(v.state != "OPEN" for v in competitors):
            return CommittedPressure("NATURAL_STOP", strongest.confidence, strongest.live_pressure, votes, "very strong stop without competing OPEN")

    chosen = max(votes, key=lambda v: v.confidence)
    return CommittedPressure("AMBIGUOUS", chosen.confidence, chosen.live_pressure, votes, "readers did not justify irreversible stop")


def read_pressure_pair(
    accepted_prose: str,
    reader_a: Callable[[str], PressureVote],
    reader_b: Callable[[str], PressureVote],
) -> CommittedPressure:
    """Run independent readers concurrently; aggregate only after both return."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        fa = pool.submit(reader_a, accepted_prose)
        fb = pool.submit(reader_b, accepted_prose)
        votes = [fa.result(), fb.result()]
    return commit_pressure(votes)
