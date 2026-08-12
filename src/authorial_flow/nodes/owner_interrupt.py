from __future__ import annotations

from typing import Any, Callable

from ..artifacts import ArtifactStore
from ..events import EventJournal
from ..learning import LearningKind, LearningStore
from ..supervisor import (
    CoverageReconciliationBlocked,
    StaleSupervisorAction,
    SupervisorAction,
    SupervisorSnapshot,
    apply_supervisor_action,
)
from ..work_feed import WorkFeed

FINAL_REVIEW_KINDS={
    'ACCEPT','BAD_EDGE','STOP_BEFORE','GLOBAL_PRECOMPUTED_SHAPE','MEANING_ISSUE','VOICE_ISSUE','DEFER'
}
AUTHORIAL_AMBIGUITY_KINDS={'ANSWER','DEFER'}
RESEARCH_ADOPTION_KINDS={'ADOPT_ALTERNATIVE','KEEP_POSITION','DEFER'}
OWNER_RESPONSE_KINDS=FINAL_REVIEW_KINDS|AUTHORIAL_AMBIGUITY_KINDS|RESEARCH_ADOPTION_KINDS


def validate_owner_response(response:dict[str,Any], *, move_count:int, interrupt_kind:str='FINAL_REVIEW')->dict[str,Any]:
    if not isinstance(response,dict):
        raise ValueError('owner response must be an object')
    kind=str(response.get('kind') or '').upper()
    allowed={
        'FINAL_REVIEW':FINAL_REVIEW_KINDS,
        'AUTHORIAL_AMBIGUITY':AUTHORIAL_AMBIGUITY_KINDS,
        'RESEARCH_ADOPTION':RESEARCH_ADOPTION_KINDS,
    }.get(interrupt_kind)
    if allowed is None:
        raise ValueError(f'unsupported interrupt kind: {interrupt_kind}')
    if kind not in allowed:
        raise ValueError(f'unsupported owner response kind {kind or "<missing>"} for {interrupt_kind}')
    normalized={**response,'kind':kind}
    if kind in {'BAD_EDGE','STOP_BEFORE'}:
        index=response.get('move_index')
        if not isinstance(index,int):
            raise ValueError(f'{kind} requires integer move_index')
        if index < 2 or index > move_count:
            raise ValueError(f'move_index must be between 2 and {move_count}')
    if kind == 'ANSWER' and not str(response.get('answer') or '').strip():
        raise ValueError('ANSWER requires non-empty answer')
    return normalized


def final_review_payload(state:dict[str,Any])->dict[str,Any]:
    payload=dict(state.get('interrupt_payload') or {})
    payload.setdefault('kind','FINAL_REVIEW')
    payload.setdefault('candidate_ref',state.get('candidate_ref',''))
    payload.setdefault('accepted_moves',list(state.get('accepted_moves') or []))
    payload.setdefault('question','Does this preserve the actual thought and flow naturally from inside it?')
    if state.get('recommended_candidate_ref'):
        payload.setdefault('recommended_candidate_ref',state.get('recommended_candidate_ref'))
    if state.get('pangram_human_variant_ref'):
        payload.setdefault('pangram_human_variant_ref',state.get('pangram_human_variant_ref'))
        payload.setdefault('detector_note','The editorial winner remains recommended; this separate meaning-preserving variant passed Pangram.')
    if state.get('better_reasoned_alternative_ref'):
        payload.setdefault('better_reasoned_alternative_ref',state.get('better_reasoned_alternative_ref'))
    return payload


def minimal_authorial_question(unit_id:str,interpretations:list[str],material_consequence:str)->dict[str,Any]:
    if len(interpretations)<2:
        raise ValueError('authorial ambiguity requires at least two materially different interpretations')
    return {
        'kind':'AUTHORIAL_AMBIGUITY','unit_id':unit_id,
        'question':'Which of these meanings is actually yours?',
        'interpretations':list(interpretations),
        'material_consequence':material_consequence,
    }


def research_adoption_payload(state:dict[str,Any])->dict[str,Any]:
    return {
        'kind':'RESEARCH_ADOPTION',
        'question':'Research supports a materially different route. Which position should the article take?',
        'faithful_position_ref':state.get('faithful_position_ref',''),
        'better_reasoned_alternative_ref':state.get('better_reasoned_alternative_ref',''),
    }


def _next_regression_version(value:Any)->str:
    try: return str(int(str(value or '0'))+1)
    except ValueError: return str(value or '0')+'+owner'


def capture_owner_response(state:dict[str,Any],response:dict[str,Any],store:LearningStore,*,interrupt_kind:str='FINAL_REVIEW')->dict[str,Any]:
    moves=list(state.get('accepted_moves') or [])
    normalized=validate_owner_response(response,move_count=len(moves),interrupt_kind=interrupt_kind)
    kind=normalized['kind']
    project_id=str(state.get('project_id') or 'project')
    update={'owner_response':normalized,'status':'owner_feedback'}
    learning_kind=None
    payload={'note':str(normalized.get('note') or '')}

    if kind in {'BAD_EDGE','STOP_BEFORE'}:
        idx=int(normalized['move_index'])
        payload.update({
            'accepted_moves':moves[:idx-1],
            'candidate':moves[idx-1],
            'verdict':'FAIL' if kind=='BAD_EDGE' else 'STOP_BEFORE_CANDIDATE',
            'move_index':idx,
        })
        learning_kind=LearningKind.LOCAL_EDGE if kind=='BAD_EDGE' else LearningKind.STOP_BEFORE
    elif kind=='GLOBAL_PRECOMPUTED_SHAPE':
        payload.update({'candidate_moves':moves,'verdict':'GLOBAL_PRECOMPUTED_SHAPE'})
        learning_kind=LearningKind.GLOBAL_PRECOMPUTED_SHAPE
    elif kind=='MEANING_ISSUE':
        payload.update({'article_specific':True,'meaning':normalized.get('meaning') or normalized.get('note','')})
        learning_kind=LearningKind.MEANING_CORRECTION
    elif kind=='VOICE_ISSUE':
        payload.update({'voice':normalized.get('note','')})
        learning_kind=LearningKind.VOICE_CORRECTION
    elif interrupt_kind=='AUTHORIAL_AMBIGUITY' and kind=='ANSWER':
        payload.update({'article_specific':True,'answer':normalized['answer'],'unit_id':state.get('open_authorial_unit_id','')})
        learning_kind=LearningKind.MEANING_CORRECTION
        update['resolved_authorial_answer']=normalized['answer']
    elif interrupt_kind=='RESEARCH_ADOPTION' and kind in {'ADOPT_ALTERNATIVE','KEEP_POSITION'}:
        payload.update({'article_specific':True,'decision':kind,'alternative_ref':state.get('better_reasoned_alternative_ref','')})
        learning_kind=LearningKind.RESEARCH_DIRECTION
        if kind=='ADOPT_ALTERNATIVE':
            update['adopted_alternative_ref']=state.get('better_reasoned_alternative_ref','')
        else:
            update['kept_faithful_position_ref']=state.get('faithful_position_ref','')
    elif kind=='ACCEPT':
        update['status']='accepted'
        return update
    elif kind=='DEFER':
        update['status']='owner_review_deferred'
        return update

    if learning_kind is not None:
        rec=store.append_owner_judgment(kind=learning_kind,project_id=project_id,payload=payload)
        update['newly_added_label_ref']=rec.id
        update['regression_version']=_next_regression_version(state.get('regression_version'))
    return update


def owner_ambiguity_node(state:dict[str,Any])->dict[str,Any]:
    from langgraph.types import interrupt
    payload=dict(state.get("interrupt_payload") or {})
    payload.setdefault("kind","AUTHORIAL_AMBIGUITY")
    payload.setdefault("question","Which meaning is actually yours?")
    response=interrupt(payload)
    normalized=validate_owner_response(
        response,move_count=len(state.get("accepted_moves") or []),interrupt_kind="AUTHORIAL_AMBIGUITY"
    )
    return {
        "owner_response":normalized,
        "active_interrupt_kind":"AUTHORIAL_AMBIGUITY",
        "status":"owner_feedback" if normalized["kind"]=="ANSWER" else "owner_review_deferred",
    }


def owner_research_adoption_node(state:dict[str,Any])->dict[str,Any]:
    from langgraph.types import interrupt
    response=interrupt(research_adoption_payload(state))
    normalized=validate_owner_response(
        response,move_count=len(state.get("accepted_moves") or []),interrupt_kind="RESEARCH_ADOPTION"
    )
    return {
        "owner_response":normalized,
        "active_interrupt_kind":"RESEARCH_ADOPTION",
        "status":"owner_review_deferred" if normalized["kind"]=="DEFER" else "owner_feedback",
    }


def owner_review_node(state:dict[str,Any])->dict[str,Any]:
    from langgraph.types import interrupt
    response=interrupt(final_review_payload(state))
    normalized=validate_owner_response(response,move_count=len(state.get('accepted_moves') or []),interrupt_kind='FINAL_REVIEW')
    status={'ACCEPT':'accepted','DEFER':'owner_review_deferred'}.get(normalized['kind'],'owner_feedback')
    return {'owner_response':normalized,'active_interrupt_kind':'FINAL_REVIEW','status':status}


def _load_supervisor_snapshot(state: dict[str, Any], store: ArtifactStore) -> SupervisorSnapshot:
    ref = str(state.get("supervisor_snapshot_ref") or "")
    found = store.find(ref) if ref else None
    if found is None:
        raise ValueError("supervisor snapshot artifact is unavailable")
    return SupervisorSnapshot.model_validate_json(found.path.read_text(encoding="utf-8"))


def supervisor_pause_node(
    state: dict[str, Any],
    *,
    artifact_store: ArtifactStore,
    learning_store: LearningStore,
    journal: EventJournal | None,
    work_feed: WorkFeed,
    reconcile_coverage: Callable[[dict[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    from langgraph.types import interrupt

    snapshot = _load_supervisor_snapshot(state, artifact_store)
    response = interrupt({
        "kind": "SUPERVISOR",
        "snapshot_ref": str(state.get("supervisor_snapshot_ref") or ""),
        "session_ref": str(state.get("supervisor_session_ref") or ""),
        "snapshot": snapshot.model_dump(mode="json"),
        "validation_error": str(state.get("supervisor_validation_error") or ""),
    })
    try:
        action = SupervisorAction.model_validate(response)
        action_state = {**state, "supervisor_resume_node": snapshot.resume_node}
        update = apply_supervisor_action(
            action_state,
            action,
            snapshot=snapshot,
            reconcile_coverage=reconcile_coverage,
            learning_store=learning_store,
        )
    except (ValueError, StaleSupervisorAction, CoverageReconciliationBlocked) as exc:
        reason = str(work_feed.sanitize(str(exc)))
        work_feed.emit("supervisor.action", {
            "thread_id": str(state.get("thread_id") or ""),
            "action_kind": "INVALID",
            "scope": "NONE",
            "restart_depth": "CURRENT_STAGE",
            "resume_node": snapshot.resume_node,
            "reason": reason,
        })
        return {
            "status": "supervisor_action_invalid",
            "supervisor_validation_error": reason,
            "supervisor_resume_node": snapshot.resume_node,
        }

    work_feed.emit("supervisor.action", {
        "thread_id": str(state.get("thread_id") or ""),
        "action_kind": action.kind,
        "scope": action.scope,
        "restart_depth": action.restart_depth,
        "resume_node": update.get("supervisor_resume_node", ""),
        "reason": action.reason,
    })
    return update
