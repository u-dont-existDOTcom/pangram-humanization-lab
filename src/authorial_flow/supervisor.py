from __future__ import annotations

from collections.abc import Callable
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .artifacts import ArtifactStore
from .events import EventJournal
from .learning import LearningStore
from .work_feed import EVENT_FIELDS, redact_secret_values


ActionKind = Literal[
    "RESUME_UNCHANGED",
    "REJECT_PROPOSAL",
    "ROLLBACK",
    "REDIRECT",
    "CORRECT_MEANING",
]
ActionScope = Literal[
    "NONE",
    "NEXT_ATTEMPT",
    "CURRENT_ARTICLE",
    "GENERAL_RULE_CANDIDATE",
]
RestartDepth = Literal[
    "CURRENT_STAGE",
    "GENERATION_FROM_PREFIX",
    "REPRESENTATION_FROM_SOURCE",
]


class CoverageReconciliationBlocked(RuntimeError):
    pass


class StaleSupervisorAction(RuntimeError):
    pass


def _valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value.lower())


def _validate_action_fields(action: Any, *, allow_none: bool) -> Any:
    if action.kind == "NONE":
        if allow_none:
            if any((
                action.instruction,
                action.scope != "NONE",
                action.restart_depth != "CURRENT_STAGE",
                action.rollback_count,
                action.proposal_ref,
                action.proposal_sha256,
            )):
                raise ValueError("NONE cannot carry action fields")
            return action
        raise ValueError("NONE is not a graph action")
    if not str(action.reason).strip():
        raise ValueError("a confirmed action requires a reason")
    if action.kind in {"REDIRECT", "CORRECT_MEANING"} and not str(action.instruction).strip():
        raise ValueError(f"{action.kind} requires an instruction")
    if action.kind == "REDIRECT" and action.scope == "NONE":
        raise ValueError("REDIRECT requires an explicit scope")
    if action.kind == "ROLLBACK" and action.rollback_count <= 0:
        raise ValueError("ROLLBACK requires a positive rollback_count")
    if action.kind == "REJECT_PROPOSAL":
        if not action.proposal_ref or not _valid_sha256(action.proposal_sha256):
            raise ValueError("REJECT_PROPOSAL requires an exact proposal ref and SHA-256")
    if action.kind == "RESUME_UNCHANGED" and any((
        action.instruction,
        action.scope != "NONE",
        action.restart_depth != "CURRENT_STAGE",
        action.rollback_count,
        action.proposal_ref,
        action.proposal_sha256,
    )):
        raise ValueError("RESUME_UNCHANGED cannot carry unrelated action fields")
    if action.kind == "REJECT_PROPOSAL" and any((
        action.instruction,
        action.scope != "NONE",
        action.restart_depth != "CURRENT_STAGE",
        action.rollback_count,
    )):
        raise ValueError("REJECT_PROPOSAL cannot carry unrelated action fields")
    if action.kind == "ROLLBACK" and any((
        action.instruction,
        action.scope != "NONE",
        action.restart_depth != "CURRENT_STAGE",
        action.proposal_ref,
        action.proposal_sha256,
    )):
        raise ValueError("ROLLBACK cannot carry unrelated action fields")
    if action.kind == "REDIRECT" and any((
        action.rollback_count,
        action.proposal_ref,
        action.proposal_sha256,
    )):
        raise ValueError("REDIRECT cannot carry proposal or rollback fields")
    if action.kind == "CORRECT_MEANING" and any((
        action.scope != "NONE",
        action.rollback_count,
        action.proposal_ref,
        action.proposal_sha256,
    )):
        raise ValueError("CORRECT_MEANING cannot carry scope, proposal, or rollback fields")
    return action


class SupervisorAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ActionKind
    reason: str
    instruction: str = ""
    scope: ActionScope = "NONE"
    restart_depth: RestartDepth = "CURRENT_STAGE"
    rollback_count: int = 0
    proposal_ref: str = ""
    proposal_sha256: str = ""

    @model_validator(mode="after")
    def validate_contract(self) -> "SupervisorAction":
        return _validate_action_fields(self, allow_none=False)


class ProposedSupervisorAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal[
        "NONE",
        "RESUME_UNCHANGED",
        "REJECT_PROPOSAL",
        "ROLLBACK",
        "REDIRECT",
        "CORRECT_MEANING",
    ]
    reason: str = ""
    instruction: str = ""
    scope: ActionScope = "NONE"
    restart_depth: RestartDepth = "CURRENT_STAGE"
    rollback_count: int = 0
    proposal_ref: str = ""
    proposal_sha256: str = ""

    @model_validator(mode="after")
    def validate_contract(self) -> "ProposedSupervisorAction":
        return _validate_action_fields(self, allow_none=True)


class SupervisorReply(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    inferences: list[str]
    uncertainties: list[str]
    proposed_action: ProposedSupervisorAction


def ask_owner_supervisor(
    snapshot: "SupervisorSnapshot",
    transcript: list[dict[str, Any]],
    services: Any,
) -> SupervisorReply:
    visible_transcript = []
    for raw in list(transcript)[-50:]:
        if not isinstance(raw, dict) or raw.get("role") not in {"user", "assistant"}:
            continue
        visible_transcript.append({
            "role": str(raw["role"]),
            "text": str(raw.get("text") or "")[:8000],
        })
    role_prompt = (
        Path(__file__).resolve().parent / "prompts" / "owner_supervisor.md"
    ).read_text(encoding="utf-8")
    prompt = role_prompt + "\n\nSAFE SUPERVISOR INPUT:\n" + json.dumps({
        "snapshot": snapshot.model_dump(mode="json"),
        "visible_session_transcript": visible_transcript,
    }, ensure_ascii=False, sort_keys=True, indent=2)
    from .models.common import ModelCall
    result = services.codex.call(
        ModelCall(prompt, SupervisorReply.model_json_schema(), "owner_supervisor"),
        services.runner,
        services.artifact_store,
    )
    return SupervisorReply.model_validate(result.parsed)


class VisibleProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_ref: str
    proposal_sha256: str
    text: str
    node: str = ""


class SupervisorSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    thread_id: str = ""
    project_id: str = ""
    source_hash: str = ""
    task_mode: str = ""
    source_provenance: str = ""
    section_job: str = ""
    interrupted_node: str = ""
    interrupted_operation: str = ""
    pause_mode: str = ""
    resume_node: str = ""
    phase: str = ""
    status: str = ""
    accepted_moves: list[str] = Field(default_factory=list)
    current_passage: str = ""
    latest_proposal: VisibleProposal | None = None
    guard_results: list[dict[str, Any]] = Field(default_factory=list)
    retry_count: int = 0
    rollback_count: int = 0
    repair_attempt: int = 0
    pangram: dict[str, Any] = Field(default_factory=dict)
    owner_directives: list[dict[str, Any]] = Field(default_factory=list)
    artifact_refs: dict[str, str] = Field(default_factory=dict)
    recent_events: list[dict[str, Any]] = Field(default_factory=list)
    journal_corrupt_line: int = 0


class SupervisorActionEffect(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_kind: ActionKind
    scope: ActionScope = "NONE"
    restart_depth: RestartDepth = "CURRENT_STAGE"
    resume_node: str
    invalidated_fields: list[str] = Field(default_factory=list)
    removed_moves: list[str] = Field(default_factory=list)


PROSE_DOWNSTREAM_CLEAR: dict[str, Any] = {
    "candidate_ref": "",
    "candidate_text_ref": "",
    "candidate_spans": [],
    "entry_edge_result": {},
    "full_edge_result": {},
    "relation_result": {},
    "semantic_result": {},
    "stop_result": {},
    "recommended_candidate_ref": "",
    "pending_detector_variant_ref": "",
    "pangram_human_variant_ref": "",
    "pangram_result_ref": "",
    "pangram_task_id": "",
    "pangram_request_identity": "",
    "pangram_candidate_ref": "",
    "pangram_submitted_at": 0.0,
    "detector_returned_version": "",
    "detector_account_action": "",
    "interrupt_payload": {},
    "owner_response": {},
    "active_interrupt_kind": "",
}


REPRESENTATION_CLEAR: dict[str, Any] = {
    "section_job": "",
    "atom_refs": [],
    "atom_coverage": {},
    "accepted_moves": [],
    "accepted_move_coverage": [],
    "accepted_prefix_hash": "",
    "move_index": 0,
    "retry_count": 0,
    "rollback_count": 0,
    "semantic_sanity_ref": "",
    "resolved_concept_ref": "",
    "developmental_ref": "",
    "research_ref": "",
    "faithful_position_ref": "",
    "better_reasoned_alternative_ref": "",
    "adopted_alternative_ref": "",
    "kept_faithful_position_ref": "",
    "resolved_authorial_answer": "",
    "open_authorial_unit_id": "",
}


def _safe_event(row: dict[str, Any]) -> dict[str, Any] | None:
    kind = str(row.get("kind") or "")
    fields = EVENT_FIELDS.get(kind)
    if fields is None:
        return None
    return {
        "sequence": int(row.get("sequence") or 0),
        "kind": kind,
        **{key: row[key] for key in fields if key in row},
    }


def build_supervisor_snapshot(
    state: dict[str, Any],
    *,
    journal: EventJournal,
    store: ArtifactStore,
) -> SupervisorSnapshot:
    del store  # Artifact bytes are never loaded implicitly into a supervisor snapshot.
    journal_read = journal.read_since(0)
    events = [safe for row in journal_read.events if (safe := _safe_event(row)) is not None]
    latest_proposal: VisibleProposal | None = None
    for event in events:
        if event["kind"] == "proposal.complete":
            latest_proposal = VisibleProposal(
                proposal_ref=str(event.get("proposal_ref") or ""),
                proposal_sha256=str(event.get("proposal_sha256") or ""),
                text=str(event.get("text") or ""),
                node=str(event.get("node") or ""),
            )
        elif (
            event["kind"] == "move.accepted"
            and latest_proposal is not None
            and event.get("proposal_ref") == latest_proposal.proposal_ref
        ):
            latest_proposal = None

    accepted_moves = [str(move) for move in state.get("accepted_moves") or []]
    directives = []
    directive_fields = {"id", "instruction", "scope", "restart_depth", "consumed"}
    for directive in state.get("owner_directives") or []:
        if isinstance(directive, dict):
            directives.append({
                key: directive[key]
                for key in directive_fields
                if key in directive
            })
    artifact_keys = {
        "source_ref",
        "requirements_ref",
        "author_context_ref",
        "semantic_sanity_ref",
        "developmental_ref",
        "research_ref",
        "candidate_ref",
        "candidate_text_ref",
        "pangram_result_ref",
        "failure_record_ref",
    }
    pangram = {
        "task_id": str(state.get("pangram_task_id") or ""),
        "candidate_ref": str(state.get("pangram_candidate_ref") or ""),
        "required_version": str(state.get("detector_required_version") or ""),
        "returned_version": str(state.get("detector_returned_version") or ""),
        "result_ref": str(state.get("pangram_result_ref") or ""),
        "account_action": str(state.get("detector_account_action") or ""),
    }
    snapshot = SupervisorSnapshot(
        thread_id=str(state.get("thread_id") or ""),
        project_id=str(state.get("project_id") or ""),
        source_hash=str(state.get("source_hash") or ""),
        task_mode=str(state.get("task_mode") or ""),
        source_provenance=str(state.get("source_provenance") or ""),
        section_job=str(state.get("section_job") or ""),
        interrupted_node=str(state.get("supervisor_interrupted_node") or ""),
        interrupted_operation=str(state.get("supervisor_interrupted_operation") or ""),
        pause_mode=str(state.get("supervisor_pause_mode") or ""),
        resume_node=str(state.get("supervisor_resume_node") or ""),
        phase=str(state.get("phase") or ""),
        status=str(state.get("status") or ""),
        accepted_moves=accepted_moves,
        current_passage=" ".join(accepted_moves),
        latest_proposal=latest_proposal,
        guard_results=[event for event in events if event["kind"] == "guard.result"],
        retry_count=int(state.get("retry_count") or 0),
        rollback_count=int(state.get("rollback_count") or 0),
        repair_attempt=int(state.get("repair_attempt") or 0),
        pangram=pangram,
        owner_directives=directives,
        artifact_refs={
            key: str(state[key])
            for key in artifact_keys
            if state.get(key)
        },
        recent_events=events[-50:],
        journal_corrupt_line=journal_read.corrupt_line,
    )
    secret_names = (
        "PANGRAM_API_KEY",
        "BRAVE_SEARCH_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    )
    secrets = tuple(
        sorted(
            {os.environ.get(name, "") for name in secret_names if os.environ.get(name, "")},
            key=len,
            reverse=True,
        )
    )
    if not secrets:
        return snapshot
    return SupervisorSnapshot.model_validate(
        redact_secret_values(snapshot.model_dump(mode="python"), secrets)
    )


def persist_supervisor_snapshot(snapshot: SupervisorSnapshot, store: ArtifactStore) -> str:
    text = json.dumps(
        snapshot.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ) + "\n"
    return store.put_text(
        text,
        "json",
        {"kind": "supervisor-snapshot", "thread_id": snapshot.thread_id},
    ).sha256


def _prose_invalidation(state: dict[str, Any]) -> dict[str, Any]:
    regressions = (state.get("final_local_gates") or {}).get("regressions_hard_pass")
    update = dict(PROSE_DOWNSTREAM_CLEAR)
    update["final_local_gates"] = (
        {"regressions_hard_pass": bool(regressions)}
        if regressions is not None
        else {}
    )
    return update


def _base_resume_update(state: dict[str, Any], resume_node: str) -> dict[str, Any]:
    return {
        "status": str(state.get("supervisor_pre_pause_status") or "supervisor_resumed"),
        "supervisor_resume_node": resume_node,
        "supervisor_validation_error": "",
        "active_interrupt_kind": "",
        "interrupt_payload": {},
        "owner_response": {},
    }


def _proposal_matches(action: SupervisorAction, snapshot: SupervisorSnapshot | None) -> None:
    visible = snapshot.latest_proposal if snapshot is not None else None
    if (
        visible is None
        or visible.proposal_ref != visible.proposal_sha256
        or action.proposal_ref != visible.proposal_ref
        or action.proposal_sha256 != visible.proposal_sha256
    ):
        raise StaleSupervisorAction("the visible proposal reference or hash changed")


def _validate_coverage_rows(
    moves: list[str],
    rows: Any,
    known_unit_ids: set[str],
    *,
    require_indices: bool = False,
) -> list[dict[str, Any]] | None:
    if isinstance(rows, dict):
        rows = rows.get("moves")
    if not isinstance(rows, list) or len(rows) != len(moves):
        return None
    validated = []
    for index, (move, row) in enumerate(zip(moves, rows, strict=True)):
        if not isinstance(row, dict):
            return None
        if (require_indices and row.get("index") != index) or (
            "index" in row and row.get("index") != index
        ):
            return None
        digest = str(row.get("move_sha256") or "")
        if digest != sha256(move.encode("utf-8")).hexdigest():
            return None
        covered = row.get("covered_unit_ids")
        if not isinstance(covered, list) or any(not isinstance(item, str) for item in covered):
            return None
        if not set(covered).issubset(known_unit_ids):
            return None
        validated.append({
            "move_sha256": digest,
            "covered_unit_ids": sorted(set(covered)),
        })
    return validated


def _coverage_rows(
    state: dict[str, Any],
    reconcile_coverage: Callable[[dict[str, Any]], Any] | None,
) -> list[dict[str, Any]]:
    moves = [str(move) for move in state.get("accepted_moves") or []]
    known = set((state.get("atom_coverage") or {}).keys())
    rows = _validate_coverage_rows(moves, state.get("accepted_move_coverage"), known)
    if rows is not None:
        return rows
    if reconcile_coverage is None:
        raise CoverageReconciliationBlocked("rollback needs validated per-move coverage")
    rows = _validate_coverage_rows(
        moves,
        reconcile_coverage(dict(state)),
        known,
        require_indices=True,
    )
    if rows is None:
        raise CoverageReconciliationBlocked("coverage reconciliation did not validate")
    return rows


def _directive_id(state: dict[str, Any], action: SupervisorAction) -> str:
    payload = {
        "thread_id": state.get("thread_id", ""),
        "instruction": action.instruction,
        "scope": action.scope,
        "restart_depth": action.restart_depth,
        "ordinal": len(state.get("owner_directives") or []),
    }
    digest = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"directive-{digest[:16]}"


def apply_supervisor_action(
    state: dict[str, Any],
    action: SupervisorAction,
    *,
    snapshot: SupervisorSnapshot | None = None,
    reconcile_coverage: Callable[[dict[str, Any]], Any] | None = None,
    learning_store: LearningStore | None = None,
) -> dict[str, Any]:
    if action.kind == "RESUME_UNCHANGED":
        resume_node = str(state.get("supervisor_resume_node") or "generation")
        return _base_resume_update(state, resume_node)

    if action.kind == "REJECT_PROPOSAL":
        _proposal_matches(action, snapshot)
        record = {
            "proposal_ref": action.proposal_ref,
            "proposal_sha256": action.proposal_sha256,
            "reason": action.reason,
        }
        update = {
            **_prose_invalidation(state),
            **_base_resume_update(state, "generation"),
            "rejected_proposals": [*(state.get("rejected_proposals") or []), record],
            "branch_memory": [{"kind": "owner_rejected_proposal", **record}],
        }
        return update

    if action.kind == "ROLLBACK":
        moves = [str(move) for move in state.get("accepted_moves") or []]
        if action.rollback_count > len(moves):
            raise ValueError("rollback_count exceeds accepted move count")
        rows = _coverage_rows(state, reconcile_coverage)
        keep = len(moves) - action.rollback_count
        retained_moves = moves[:keep]
        retained_rows = rows[:keep]
        retained_units = {
            unit_id
            for row in retained_rows
            for unit_id in row["covered_unit_ids"]
        }
        atom_coverage = {
            unit_id: unit_id in retained_units
            for unit_id in (state.get("atom_coverage") or {})
        }
        return {
            **_prose_invalidation(state),
            **_base_resume_update(state, "generation"),
            "accepted_moves": retained_moves,
            "accepted_move_coverage": retained_rows,
            "accepted_prefix_hash": sha256(" ".join(retained_moves).encode("utf-8")).hexdigest(),
            "atom_coverage": atom_coverage,
            "move_index": len(retained_moves),
            "rollback_count": int(state.get("rollback_count") or 0) + 1,
            "coverage_reconciliation_required": False,
            "branch_memory": [{
                "kind": "owner_rollback",
                "removed": moves[keep:],
                "reason": action.reason,
            }],
        }

    if action.kind == "REDIRECT":
        directive = {
            "id": _directive_id(state, action),
            "instruction": action.instruction,
            "scope": action.scope,
            "restart_depth": action.restart_depth,
            "reason": action.reason,
            "consumed": False,
        }
        if action.restart_depth == "REPRESENTATION_FROM_SOURCE":
            resume_node = "representation"
            invalidation = {**_prose_invalidation(state), **REPRESENTATION_CLEAR}
        else:
            resume_node = (
                str(state.get("supervisor_resume_node") or "generation")
                if action.restart_depth == "CURRENT_STAGE"
                else "generation"
            )
            invalidation = _prose_invalidation(state)
        update = {
            **invalidation,
            **_base_resume_update(state, resume_node),
            "owner_directives": [*(state.get("owner_directives") or []), directive],
            "consumed_directive_ids": list(state.get("consumed_directive_ids") or []),
            "new_supervisor_learning_ref": "",
        }
        if action.scope == "GENERAL_RULE_CANDIDATE":
            if learning_store is None:
                raise ValueError("GENERAL_RULE_CANDIDATE requires a learning store")
            record = learning_store.append_hypothesis(
                kind="OWNER_DIRECTION",
                project_id=str(state.get("project_id") or ""),
                payload={
                    "abstract_rule": action.instruction,
                    "reason": action.reason,
                    "directive_id": directive["id"],
                    "article_specific": False,
                },
            )
            update["new_supervisor_learning_ref"] = record.id
        return update

    if action.kind == "CORRECT_MEANING":
        digest = sha256(
            f"{state.get('thread_id', '')}\0{action.instruction}\0{action.reason}".encode("utf-8")
        ).hexdigest()
        correction = {
            "id": f"correction-{digest[:16]}",
            "instruction": action.instruction,
            "reason": action.reason,
            "authority": "OWNER_GROUNDED",
        }
        return {
            **_prose_invalidation(state),
            **REPRESENTATION_CLEAR,
            **_base_resume_update(state, "representation"),
            "owner_authority_corrections": [
                *(state.get("owner_authority_corrections") or []),
                correction,
            ],
        }

    raise ValueError(f"unsupported supervisor action: {action.kind}")


def normalize_action(
    proposed: ProposedSupervisorAction,
    snapshot: SupervisorSnapshot,
) -> tuple[SupervisorAction, SupervisorActionEffect]:
    if proposed.kind == "NONE":
        raise ValueError("there is no proposed graph action to normalize")
    payload = proposed.model_dump(mode="python")
    if proposed.kind == "CORRECT_MEANING":
        payload["restart_depth"] = "REPRESENTATION_FROM_SOURCE"
    action = SupervisorAction.model_validate(payload)
    if action.kind == "REJECT_PROPOSAL":
        _proposal_matches(action, snapshot)
    if action.kind == "ROLLBACK" and action.rollback_count > len(snapshot.accepted_moves):
        raise ValueError("rollback_count exceeds accepted move count")
    if action.kind == "RESUME_UNCHANGED":
        resume_node = snapshot.resume_node or "generation"
        invalidated: list[str] = []
        removed: list[str] = []
    elif action.kind == "CORRECT_MEANING" or action.restart_depth == "REPRESENTATION_FROM_SOURCE":
        resume_node = "representation"
        invalidated = sorted({*PROSE_DOWNSTREAM_CLEAR, *REPRESENTATION_CLEAR, "final_local_gates"})
        removed = list(snapshot.accepted_moves)
    elif action.kind == "ROLLBACK":
        resume_node = "generation"
        invalidated = sorted({*PROSE_DOWNSTREAM_CLEAR, "final_local_gates"})
        removed = snapshot.accepted_moves[-action.rollback_count:]
    elif action.kind == "REJECT_PROPOSAL":
        resume_node = "generation"
        invalidated = sorted({*PROSE_DOWNSTREAM_CLEAR, "final_local_gates"})
        removed = []
    else:
        resume_node = (
            snapshot.resume_node or "generation"
            if action.restart_depth == "CURRENT_STAGE"
            else "generation"
        )
        invalidated = sorted({*PROSE_DOWNSTREAM_CLEAR, "final_local_gates"})
        removed = []
    return action, SupervisorActionEffect(
        action_kind=action.kind,
        scope=action.scope,
        restart_depth=action.restart_depth,
        resume_node=resume_node,
        invalidated_fields=invalidated,
        removed_moves=removed,
    )


_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9._-]+$")


class SupervisorSessionStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    @staticmethod
    def _component(value: str) -> str:
        if not value or not _SAFE_COMPONENT.fullmatch(value):
            raise ValueError("unsafe supervisor session component")
        return value

    def create(self, thread_id: str, pause_id: str) -> str:
        ref = f"{self._component(thread_id)}/{self._component(pause_id)}.jsonl"
        path = self._resolve(ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        return ref

    def _resolve(self, ref: str) -> Path:
        relative = Path(ref)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe supervisor session reference")
        root = self.root.resolve()
        target = (root / relative).resolve()
        if target != root and root not in target.parents:
            raise ValueError("supervisor session reference escapes its root")
        return target

    def append(self, ref: str, role: Literal["user", "assistant"], text: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("unsupported supervisor session role")
        path = self._resolve(ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                fh.write(json.dumps({
                    "role": role,
                    "text": str(text),
                    "time": time.time(),
                }, ensure_ascii=False, sort_keys=True) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

    def read(self, ref: str) -> list[dict[str, Any]]:
        path = self._resolve(ref)
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_SH)
            try:
                lines = fh.read().splitlines()
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        rows = []
        for raw in lines:
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                break
            if (
                not isinstance(row, dict)
                or row.get("role") not in {"user", "assistant"}
                or not isinstance(row.get("text"), str)
            ):
                break
            rows.append({
                "role": row["role"],
                "text": row["text"],
                "time": float(row.get("time") or 0.0),
            })
        return rows
