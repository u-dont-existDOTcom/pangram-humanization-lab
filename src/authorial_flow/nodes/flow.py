from __future__ import annotations

from dataclasses import dataclass
import re

from .generate import candidate_semantic_spans
from .pressure import CommittedPressure


@dataclass(frozen=True)
class EdgeResult:
    verdict: str
    confidence: float
    failure_type: str = "none"
    reason: str = ""
    challenge: str = ""


def is_natural_arrival(text: str) -> bool:
    low = text.lower()
    markers = (
        "where i get lost", "where i'm lost", "where i get stuck", "where i'm stuck",
        "what i can't get past", "what i cannot get past", "i don't know how",
        "i do not know how", "that's where i lose", "that is where i lose",
    )
    return any(m in low for m in markers)


def judge_entry(precommitted: CommittedPressure, previous: str, entry: str) -> EdgeResult:
    if precommitted.state == "NATURAL_STOP":
        return EdgeResult("STOP_BEFORE_CANDIDATE", .95, "reopens_after_arrival", "precommitted thought-level arrival")
    low = entry.strip().lower()
    if previous.rstrip().endswith("?"):
        side_openers = ("not that ", "anyway", "meanwhile", "in any case", "choices happen", "choices matter")
        if low.startswith(side_openers):
            return EdgeResult("FAIL", .95, "sidesteps_live_pressure", "candidate entry changes to a neighboring issue instead of pursuing the question")
    return EdgeResult("PASS", .75)


def judge_full_edge(accepted_moves: list[str], candidate: str, precommitted: CommittedPressure | None = None) -> EdgeResult:
    if not accepted_moves:
        return EdgeResult("PASS", 1.0)
    previous = accepted_moves[-1]
    if precommitted and precommitted.state == "NATURAL_STOP":
        return EdgeResult("STOP_BEFORE_CANDIDATE", .98, "reopens_after_arrival", "candidate appears after a precommitted natural stop")
    if is_natural_arrival(previous):
        return EdgeResult("STOP_BEFORE_CANDIDATE", .96, "reopens_after_arrival", "previous move states the live unresolved boundary")
    entry = candidate_semantic_spans(candidate)[0] if candidate_semantic_spans(candidate) else candidate
    if precommitted:
        result = judge_entry(precommitted, previous, entry)
        if result.verdict != "PASS":
            return result
    if previous.rstrip().endswith("?") and entry.strip().lower().startswith("not that "):
        return EdgeResult("FAIL", .97, "sidesteps_live_pressure", "concession opens a neighboring issue")
    return EdgeResult("PASS", .78)


def judge_edge_locally(accepted_moves: list[str], candidate: str) -> EdgeResult:
    """Deterministic regression fallback; live runtime can replace this with isolated model judges."""
    if not accepted_moves:
        return EdgeResult("PASS", 1.0)
    previous = accepted_moves[-1]
    if is_natural_arrival(previous):
        return EdgeResult("STOP_BEFORE_CANDIDATE", .97, "reopens_settled_material_after_arrival", "previous move is a stated epistemic arrival")
    entry = candidate_semantic_spans(candidate)[0] if candidate_semantic_spans(candidate) else candidate
    if previous.rstrip().endswith("?") and entry.strip().lower().startswith("not that "):
        return EdgeResult("FAIL", .97, "sidesteps_live_pressure", "candidate sidesteps the direct question")
    return EdgeResult("PASS", .70)
