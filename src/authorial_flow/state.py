from __future__ import annotations

from typing import Annotated, Any, TypedDict
import operator


class AuthorialState(TypedDict, total=False):
    # Identity
    project_id: str
    thread_id: str
    source_hash: str
    protected_input_hashes: dict[str, str]
    graph_version: str
    regression_version: str

    # Inputs: content-addressed refs only
    source_ref: str
    requirements_ref: str
    author_context_ref: str
    owner_gold_ref: str
    semantic_gold_ref: str
    diagnostic_positive_ref: str

    # Provenance / operation mode / semantic escalation
    requested_operation: str
    source_metadata: dict[str, Any]
    source_provenance: str
    task_mode: str
    semantic_sanity_ref: str
    escalation_reason: str
    escalation_count: int
    resolved_concept_ref: str
    developmental_ref: str
    research_ref: str
    faithful_position_ref: str
    better_reasoned_alternative_ref: str
    open_authorial_unit_id: str

    # Semantic representation
    section_job: str
    atom_refs: list[str]
    exact_identity_strings: list[str]
    atom_coverage: dict[str, bool]

    # Generation
    accepted_moves: list[str]
    accepted_move_coverage: list[dict[str, Any]]
    coverage_reconciliation_required: bool
    accepted_prefix_hash: str
    move_index: int
    retry_count: int
    rollback_count: int
    branch_memory: Annotated[list[dict[str, Any]], operator.add]
    pressure_votes: list[dict[str, Any]]
    committed_pressure: dict[str, Any]
    candidate_ref: str
    candidate_text_ref: str
    candidate_spans: list[str]

    # Judgments
    entry_edge_result: dict[str, Any]
    full_edge_result: dict[str, Any]
    relation_result: dict[str, Any]
    semantic_result: dict[str, Any]
    stop_result: dict[str, Any]
    final_local_gates: dict[str, Any]
    pangram_result_ref: str
    recommended_candidate_ref: str
    pending_detector_variant_ref: str
    pangram_human_variant_ref: str
    detector_variant_attempt: int
    pangram_task_id: str
    pangram_request_identity: str
    pangram_candidate_ref: str
    pangram_submitted_at: float
    detector_required_version: str
    detector_returned_version: str
    detector_account_action: str

    # Human supervision
    interrupt_payload: dict[str, Any]
    active_interrupt_kind: str
    owner_response: dict[str, Any]
    newly_added_label_ref: str
    resolved_authorial_answer: str
    adopted_alternative_ref: str
    kept_faithful_position_ref: str
    owner_directives: list[dict[str, Any]]
    consumed_directive_ids: list[str]
    rejected_proposals: list[dict[str, Any]]
    owner_authority_corrections: list[dict[str, Any]]
    supervisor_resume_node: str
    supervisor_snapshot_ref: str
    supervisor_session_ref: str
    supervisor_pause_mode: str
    supervisor_pre_pause_status: str
    supervisor_interrupted_node: str
    supervisor_interrupted_operation: str
    supervisor_validation_error: str
    new_supervisor_learning_ref: str

    # Repair
    failure_class: str
    failure_record_ref: str
    failure_origin_node: str
    authorial_information_missing: bool
    repair_attempt: int
    restart_required: bool
    program_version: str
    plan_ref: str
    patch_ref: str
    test_ref: str
    review_ref: str
    repair_resume_node: str
    repair_commit: str
    failure_evidence_ref: str

    # Runtime
    phase: str
    status: str
    active_process: dict[str, Any]
    heartbeat: dict[str, Any]
    last_error_ref: str
    event_sequence: int
