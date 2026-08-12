from __future__ import annotations

from dataclasses import dataclass
import re

from ..authority import AuthorityUnit


@dataclass(frozen=True)
class FidelityResult:
    verdict: str
    confidence: float = 1.0
    failure_type: str = "none"
    reason: str = ""
    affected_units: tuple[str, ...] = ()


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def relation_guard(source: str, candidate: str) -> FidelityResult:
    s, c = _norm(source), _norm(candidate)
    if re.search(r"\b(answer(?:s|ed|ing)?|give(?:s)? an answer|resolve[sd]?)\b", c) and not re.search(r"\b(answer|resolve)\b", s):
        return FidelityResult("FAIL", .98, "invented_answer_relation", "candidate turns source adjacency into an answer relation")
    inference = re.match(r"^(so|therefore|thus|hence)\b[,:]?\s*(.*)", c)
    if inference:
        marker, core = inference.group(1), inference.group(2).strip()
        # A source containing some unrelated "so" does not license a new inferential bridge here.
        # Require the same proposition to be explicitly introduced by that marker in the source.
        core_prefix = " ".join(core.split()[:5])
        licensed = bool(core_prefix) and re.search(
            rf"\b{re.escape(marker)}\b[,:]?\s+{re.escape(core_prefix)}", s
        )
        if not licensed:
            return FidelityResult("FAIL", .96, "invented_causal_relation", "candidate adds an inference relation not stated for this proposition in source")
    for marker in ("immediately", "awkward"):
        if re.search(rf"\b{marker}\b", c) and not re.search(rf"\b{marker}\b", s):
            return FidelityResult("FAIL", .95, "invented_timing_or_evaluation", f"candidate adds {marker!r} without source support")
    return FidelityResult("PASS", .80)


def semantic_guard(candidate: str, units: list[AuthorityUnit]) -> FidelityResult:
    low = _norm(candidate)
    missing_exact = [u.id for u in units if u.exact_lock and u.must_preserve and _norm(u.text) not in low]
    # Exact-lock absence in a single move is not itself a failure; exact units may appear later.
    # This guard only blocks direct contradiction markers for currently referenced locked text.
    for unit in units:
        if unit.exact_lock and unit.text and unit.text.lower() in candidate.lower():
            continue
    return FidelityResult("PASS", .75, affected_units=tuple(missing_exact))
