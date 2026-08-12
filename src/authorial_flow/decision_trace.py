from __future__ import annotations

import re
from typing import Any, Mapping


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Z0-9_.:-]{1,64}$")
_PRESSURE_STATES = {"OPEN", "NATURAL_STOP", "AMBIGUOUS"}
_EDGE_VERDICTS = {"PASS", "FAIL", "STOP_BEFORE_CANDIDATE"}
_PROVIDERS = {"codex", "claude", "controller"}


def _sha(value: Any) -> str:
    token = str(value or "").lower()
    return token if _SHA256_RE.fullmatch(token) else ""


def _token(value: Any) -> str:
    token = str(value or "").upper()
    return token if _TOKEN_RE.fullmatch(token) else ""


def _count(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _confidence(value: Any) -> float:
    try:
        return min(1.0, max(0.0, float(value or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def build_decision_trace(state: Mapping[str, Any]) -> dict[str, Any]:
    """Project controller state into a content-free, versioned decision record."""
    boundary_id = _sha(state.get("generation_boundary_id"))
    decision_boundary_id = _sha(state.get("decision_boundary_id")) or boundary_id
    pressure_raw = state.get("committed_pressure")
    pressure_raw = pressure_raw if isinstance(pressure_raw, Mapping) else {}
    pressure_state = _token(pressure_raw.get("state"))
    committed_pressure = {
        "state": pressure_state if pressure_state in _PRESSURE_STATES else "",
        "confidence": _confidence(pressure_raw.get("confidence")),
        "boundary_id": _sha(pressure_raw.get("boundary_id")),
    }
    votes: list[dict[str, Any]] = []
    for raw in list(state.get("pressure_votes") or [])[:4]:
        if not isinstance(raw, Mapping):
            continue
        vote_state = _token(raw.get("state"))
        provider = str(raw.get("provider") or "").lower()
        votes.append({
            "state": vote_state if vote_state in _PRESSURE_STATES else "",
            "confidence": _confidence(raw.get("confidence")),
            "provider": provider if provider in _PROVIDERS else "",
            "boundary_id": _sha(raw.get("boundary_id")),
        })
    edge: dict[str, Any] = {}
    for key in ("full_edge_result", "entry_edge_result"):
        raw = state.get(key)
        if not isinstance(raw, Mapping):
            continue
        edge_boundary = _sha(raw.get("boundary_id"))
        if decision_boundary_id and edge_boundary != decision_boundary_id:
            continue
        verdict = _token(raw.get("verdict"))
        edge = {
            "verdict": verdict if verdict in _EDGE_VERDICTS else "",
            "confidence": _confidence(raw.get("confidence")),
            "boundary_id": edge_boundary,
        }
        break
    proposal_hash = _sha(state.get("proposal_ref")) or _sha(state.get("candidate_ref"))
    return {
        "schema_version": 1,
        "boundary_id": boundary_id,
        "decision_boundary_id": decision_boundary_id,
        "accepted_move_count": len(state.get("accepted_moves") or []),
        "uncovered_required_count": _count(state.get("uncovered_required_count")),
        "pressure_votes": votes,
        "committed_pressure": committed_pressure,
        "edge": edge,
        "candidate_sha256": proposal_hash,
        "rejection_class": _token(state.get("generation_rejection_class")),
        "budgets": {
            "retry_count": _count(state.get("retry_count")),
            "rollback_count": _count(state.get("rollback_count")),
            "active_budget": _token(state.get("budget")),
            "budget_limit": _count(state.get("budget_limit")),
        },
    }

