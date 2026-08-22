from __future__ import annotations

from typing import Any


SUPERVISOR_STATUSES = {"supervisor_pause_requested", "supervisor_action_invalid"}


def _pause_route(state: dict[str, Any]) -> str:
    return (
        "supervisor_pause"
        if str(state.get("status") or "") in SUPERVISOR_STATUSES
        else ""
    )


def route_generation(state: dict[str,Any]) -> str:
    if pause := _pause_route(state):
        return pause
    status=str(state.get("status") or "")
    if status == "machine_failure":
        return "repair"
    return "generation" if status == "continue_generation" else "cold_audit"


def route_after_regressions(state:dict[str,Any])->str:
    if pause := _pause_route(state):
        return pause
    return "repair" if state.get("status") == "machine_failure" else "representation"


def route_after_representation(state:dict[str,Any])->str:
    if pause := _pause_route(state):
        return pause
    # A semantic-sanity contract error is machine state, not authorial ambiguity.
    # This guard is deliberately checked before the historical status field because
    # older representation code may have labelled the same invalid contract as an
    # owner interrupt. Never surface that synthetic question to the owner.
    if str(state.get("semantic_escalation_error") or "").strip():
        return "repair"
    status=str(state.get("status") or "")
    if status == "machine_failure": return "repair"
    if status == "owner_ambiguity_required": return "owner_ambiguity"
    if status == "research_adoption_required": return "research_adoption"
    return "generation"


def route_after_cold_audit(state:dict[str,Any])->str:
    if pause := _pause_route(state):
        return pause
    return "repair" if state.get("status") == "machine_failure" else "freeze"


def route_after_freeze(state: dict[str, Any]) -> str:
    if pause := _pause_route(state):
        return pause
    return "detector"


def route_after_detector(state:dict[str,Any])->str:
    if pause := _pause_route(state):
        return pause
    status=str(state.get("status") or "")
    if status == "owner_review_ready":
        return "owner_review"
    if status in {"detector_retry","detector_poll_pending"}:
        return "detector"
    if status in {"detector_nonhuman","machine_failure"}:
        return "repair"
    return "finalize"


def route_after_repair(state:dict[str,Any])->str:
    if pause := _pause_route(state):
        return pause
    status=str(state.get('status') or '')
    if status == 'repair_promoted_restart_required':
        return 'repair_restart'
    if status == 'repair_promoted':
        return 'regressions'
    if status == 'repair_retry':
        return 'repair'
    if status == 'owner_ambiguity_required':
        return 'owner_ambiguity'
    return 'finalize'


def route_after_repair_restart(state:dict[str,Any])->str:
    allowed={'regressions','representation','generation','cold_audit','freeze','detector','owner_learning'}
    target=str(state.get('repair_resume_node') or 'regressions')
    return target if target in allowed else 'regressions'


def route_owner_response(state: dict[str,Any]) -> str:
    kind=str((state.get("owner_response") or {}).get("kind") or "")
    if kind == "ACCEPT":
        return "finalize"
    if kind == "DEFER":
        return "finalize"
    return "finalize"


def route_after_semantic_sanity(result) -> str:
    escalation=str(result.recommended_escalation).upper()
    if result.status == "PASS" or escalation == "BASIC":
        return "basic"
    if escalation == "RESEARCH":
        return "research"
    if escalation in {"P3","P4"}:
        return "developmental"
    if escalation == "OWNER":
        return "owner_ambiguity"
    raise ValueError(f"unknown semantic-sanity escalation: {escalation}")


def route_mode_result(result) -> str:
    if result.status == "MODE_VIOLATION":
        return "mode_violation"
    if result.status == "REPORT_ONLY":
        return "finalize"
    return "cold_audit"


def route_after_owner_learning(state: dict[str,Any]) -> str:
    if pause := _pause_route(state):
        return pause
    kind=str((state.get("owner_response") or {}).get("kind") or "")
    if kind in {"BAD_EDGE","STOP_BEFORE","GLOBAL_PRECOMPUTED_SHAPE"}:
        return "regressions"
    if kind in {"MEANING_ISSUE","VOICE_ISSUE","ANSWER","ADOPT_ALTERNATIVE","KEEP_POSITION"}:
        return "representation"
    return "finalize"


def route_after_supervisor(state: dict[str, Any]) -> str:
    if str(state.get("status") or "") == "supervisor_action_invalid":
        return "supervisor_pause"
    allowed = {
        "regressions",
        "representation",
        "generation",
        "cold_audit",
        "freeze",
        "detector",
        "owner_review",
        "owner_ambiguity",
        "research_adoption",
        "owner_learning",
        "repair",
        "repair_restart",
        "finalize",
        "supervisor_pause",
    }
    target = str(state.get("supervisor_resume_node") or "")
    return target if target in allowed else "supervisor_pause"


def route_failure(failure_class) -> str:
    from .failures import FailureClass
    if failure_class is FailureClass.OWNER_JUDGMENT:
        return "owner_interrupt"
    if failure_class in {
        FailureClass.DETERMINISTIC_RUNTIME, FailureClass.PROVIDER_PLUMBING,
        FailureClass.REGRESSION_ARCHITECTURE, FailureClass.GENERATION_DEAD_END,
        FailureClass.SEMANTIC_DEVELOPMENTAL, FailureClass.RESEARCH_PROVIDER,
        FailureClass.FIDELITY, FailureClass.PANGRAM_ONLY,
    }:
        return "repair"
    return "bounded_stop"
