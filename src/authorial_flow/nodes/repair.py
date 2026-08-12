from __future__ import annotations

from typing import Any, Callable


_REPAIR_RESUME_NODES={
    'regressions','representation','generation','cold_audit','freeze','detector','owner_learning'
}


def repair_node(state:dict[str,Any],repair_cycle:Callable[[dict[str,Any]],dict[str,Any]])->dict[str,Any]:
    """Graph-facing repair boundary. The supplied cycle owns worktree isolation and verification."""
    try:
        result=repair_cycle(state)
    except Exception as exc:
        reason=f'{type(exc).__name__}: {exc}'
        history=[dict(row) for row in list(state.get('repair_history') or [])[-9:] if isinstance(row,dict)]
        history.append({
            'attempt':int(state.get('repair_attempt',0))+1,
            'signature':'','outcome':'REJECTED_WITH_REASON',
            'reason':reason[:2000],
        })
        return {
            'status':'repair_retry',
            'repair_attempt':int(state.get('repair_attempt',0))+1,
            'repair_error':reason,
            'repair_outcome':'REJECTED_WITH_REASON',
            'repair_plan_signature':'',
            'repair_history':history,
        }
    inferred_outcome=(
        'APPLIED_VERIFIED' if result.get('pass')
        else 'STAGED_FOR_OWNER' if result.get('owner_judgment_required')
        else 'NON_APPLICABLE_STOP' if result.get('exhausted')
        else 'REJECTED_WITH_REASON'
    )
    outcome=str(result.get('outcome') or inferred_outcome)
    signature=str(result.get('plan_signature') or '')
    history=[dict(row) for row in list(state.get('repair_history') or [])[-9:] if isinstance(row,dict)]
    history_entry=result.get('history_entry')
    if isinstance(history_entry,dict):
        history.append(dict(history_entry))
    else:
        history.append({
            'attempt':int(state.get('repair_attempt',0))+1,
            'signature':signature,'outcome':outcome,
            'reason':str(result.get('reason') or '')[:2000],
        })
    outcome_fields={
        'repair_outcome':outcome,
        'repair_plan_signature':signature,
        'repair_history':history,
    }
    if result.get('pass'):
        restart=bool(result.get('restart_required'))
        origin=str(state.get('failure_origin_node') or 'regressions')
        resume_node=origin if origin in _REPAIR_RESUME_NODES else 'regressions'
        return {
            'status':'repair_promoted_restart_required' if restart else 'repair_promoted',
            'program_version':result.get('program_version',state.get('program_version','')),
            'repair_attempt':int(state.get('repair_attempt',0))+1,
            'restart_required':restart,
            'repair_resume_node':resume_node,
            'repair_commit':str(result.get('repair_commit') or ''),
            'plan_ref':str(result.get('plan_ref') or ''),
            'test_ref':str(result.get('test_ref') or ''),
            'review_ref':str(result.get('review_ref') or ''),
            'failure_evidence_ref':str(result.get('failure_evidence_ref') or state.get('failure_record_ref') or ''),
            # Keep the active failure markers until the new program image crosses the restart interrupt.
            'failure_class':str(state.get('failure_class') or ''),
            'failure_record_ref':str(state.get('failure_record_ref') or ''),
            'last_error_ref':str(state.get('last_error_ref') or state.get('failure_record_ref') or ''),
            **outcome_fields,
        }
    if result.get('owner_judgment_required'):
        return {
            'status':'owner_ambiguity_required',
            'repair_attempt':int(state.get('repair_attempt',0))+1,
            'interrupt_payload':{
                'kind':'AUTHORIAL_AMBIGUITY',
                'question':str(result.get('owner_question') or 'Which meaning is actually yours?'),
            },
            'last_error_ref':result.get('error_ref',''),
            **outcome_fields,
        }
    error_ref=str(result.get('error_ref') or state.get('failure_record_ref') or state.get('last_error_ref') or '')
    exhausted=bool(result.get('exhausted'))
    return {
        'status':'bounded_machine_stop' if exhausted else 'repair_retry',
        'repair_attempt':int(state.get('repair_attempt',0))+1,
        'last_error_ref':error_ref,
        'failure_evidence_ref':error_ref,
        'failure_class':str(state.get('failure_class') or ''),
        'authorial_information_missing':False if exhausted else bool(state.get('authorial_information_missing')),
        **outcome_fields,
    }


def repair_restart_boundary_node(state:dict[str,Any])->dict[str,Any]:
    """Durably pause after promotion so the stale process cannot execute repaired paths."""
    from langgraph.types import interrupt

    payload={
        'kind':'MACHINE_RESTART',
        'thread_id':str(state.get('thread_id') or ''),
        'program_version':str(state.get('program_version') or ''),
        'repair_commit':str(state.get('repair_commit') or ''),
        'repair_resume_node':str(state.get('repair_resume_node') or 'regressions'),
        'failure_evidence_ref':str(state.get('failure_evidence_ref') or state.get('failure_record_ref') or ''),
    }
    response=interrupt(payload)
    kind=str(response.get('kind') if isinstance(response,dict) else response or '').upper()
    if kind != 'MACHINE_RESTART_RESUME':
        raise RuntimeError('machine repair restart requires MACHINE_RESTART_RESUME')
    return {
        'status':'repair_resumed',
        'restart_required':False,
        'failure_class':'',
        'failure_record_ref':'',
        'failure_origin_node':'',
        'authorial_information_missing':False,
        'last_error_ref':'',
    }
