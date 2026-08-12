import json
from hashlib import sha256

import pytest
from pydantic import ValidationError

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.events import EventJournal
from authorial_flow.learning import LearningScope, LearningStore
from authorial_flow.supervisor import (
    CoverageReconciliationBlocked,
    ProposedSupervisorAction,
    StaleSupervisorAction,
    SupervisorAction,
    SupervisorSessionStore,
    SupervisorSnapshot,
    VisibleProposal,
    apply_supervisor_action,
    build_supervisor_snapshot,
    normalize_action,
    persist_supervisor_snapshot,
)


def test_snapshot_contains_only_safe_operational_state(tmp_path):
    journal = EventJournal(tmp_path / "events.jsonl")
    journal.append("proposal.complete", {
        "schema_version": 1,
        "proposal_ref": "proposal-1",
        "proposal_sha256": "a" * 64,
        "text": "Complete unaccepted proposal.",
        "node": "generation",
    })
    state = {
        "thread_id": "thread-1",
        "project_id": "project-1",
        "source_hash": "source-hash",
        "task_mode": "P2S",
        "section_job": "follow the question",
        "accepted_moves": ["Accepted."],
        "atom_coverage": {"u1": True},
        "entry_edge_result": {"verdict": "FAIL", "reason": "bad edge"},
        "pangram_task_id": "task-1",
        "PANGRAM_API_KEY": "SECRET",
        "raw_prompt": "HIDDEN",
    }
    store = ArtifactStore(tmp_path / "artifacts")

    snapshot = build_supervisor_snapshot(state, journal=journal, store=store)
    blob = json.dumps(snapshot.model_dump(mode="json"))

    assert snapshot.current_passage == "Accepted."
    assert snapshot.latest_proposal is not None
    assert snapshot.latest_proposal.text == "Complete unaccepted proposal."
    assert snapshot.pangram["task_id"] == "task-1"
    assert "Complete unaccepted proposal." in blob
    assert "Accepted." in blob
    assert "task-1" in blob
    assert "SECRET" not in blob
    assert "HIDDEN" not in blob
    assert "raw_prompt" not in blob

    ref = persist_supervisor_snapshot(snapshot, store)
    found = store.find(ref)
    assert found is not None
    assert json.loads(found.path.read_text())["thread_id"] == "thread-1"


def test_snapshot_redacts_current_credentials_from_legacy_direct_events(tmp_path, monkeypatch):
    secret = "PANGRAM-SNAPSHOT-SECRET-4927"
    monkeypatch.setenv("PANGRAM_API_KEY", secret)
    journal = EventJournal(tmp_path / "events.jsonl")
    journal.append("guard.result", {
        "gate": "fidelity",
        "verdict": "FAIL",
        "reason": f"legacy reason accidentally contained {secret}",
    })

    snapshot = build_supervisor_snapshot(
        {"thread_id": "thread-1"},
        journal=journal,
        store=ArtifactStore(tmp_path / "artifacts"),
    )
    blob = json.dumps(snapshot.model_dump(mode="json"))

    assert secret not in blob
    assert "[REDACTED]" in blob


def test_accepted_proposal_is_not_reported_as_unaccepted(tmp_path):
    journal = EventJournal(tmp_path / "events.jsonl")
    journal.append("proposal.complete", {
        "proposal_ref": "p1",
        "proposal_sha256": "a" * 64,
        "text": "Accepted proposal.",
        "node": "generation",
    })
    journal.append("move.accepted", {
        "proposal_ref": "p1",
        "text": "Accepted proposal.",
        "node": "generation",
    })

    snapshot = build_supervisor_snapshot(
        {"thread_id": "t", "accepted_moves": ["Accepted proposal."]},
        journal=journal,
        store=ArtifactStore(tmp_path / "artifacts"),
    )

    assert snapshot.latest_proposal is None


def test_rollback_truncates_moves_and_recomputes_coverage():
    moves = ["one", "two", "three"]
    state = {
        "accepted_moves": moves,
        "accepted_move_coverage": [
            {"move_sha256": sha256(b"one").hexdigest(), "covered_unit_ids": ["u1"]},
            {"move_sha256": sha256(b"two").hexdigest(), "covered_unit_ids": ["u2"]},
            {"move_sha256": sha256(b"three").hexdigest(), "covered_unit_ids": ["u3"]},
        ],
        "atom_coverage": {"u1": True, "u2": True, "u3": True},
        "candidate_ref": "stale",
        "pangram_task_id": "remote-task",
        "supervisor_resume_node": "generation",
        "supervisor_pre_pause_status": "continue_generation",
    }

    update = apply_supervisor_action(
        state,
        SupervisorAction(kind="ROLLBACK", rollback_count=2, reason="The turn went wrong."),
    )

    assert state["accepted_moves"] == moves
    assert update["accepted_moves"] == ["one"]
    assert update["atom_coverage"] == {"u1": True, "u2": False, "u3": False}
    assert update["candidate_ref"] == ""
    assert update["pangram_task_id"] == ""
    assert update["supervisor_resume_node"] == "generation"


def test_legacy_rollback_fails_closed_without_validated_reconciliation():
    state = {
        "accepted_moves": ["one", "two"],
        "accepted_move_coverage": [],
        "atom_coverage": {"u1": True},
    }
    with pytest.raises(CoverageReconciliationBlocked):
        apply_supervisor_action(
            state,
            SupervisorAction(kind="ROLLBACK", rollback_count=1, reason="bad"),
            reconcile_coverage=lambda _state: None,
        )


def test_general_rule_candidate_is_not_promoted(tmp_path):
    store = LearningStore(tmp_path)
    state = {"project_id": "p", "supervisor_resume_node": "generation"}

    update = apply_supervisor_action(
        state,
        SupervisorAction(
            kind="REDIRECT",
            instruction="Follow the concrete contradiction.",
            scope="GENERAL_RULE_CANDIDATE",
            restart_depth="GENERATION_FROM_PREFIX",
            reason="Try this here and preserve it only as a hypothesis.",
        ),
        learning_store=store,
    )

    record = store.get(update["new_supervisor_learning_ref"])
    assert record.scope is LearningScope.REUSABLE_HYPOTHESIS
    assert store.promoted_rules() == []


def test_meaning_correction_clears_representation_and_preserves_immutable_inputs():
    state = {
        "thread_id": "thread-1",
        "source_ref": "source",
        "requirements_ref": "requirements",
        "owner_gold_ref": "owner-gold",
        "protected_input_hashes": {"INPUT.md": "hash"},
        "section_job": "old job",
        "atom_refs": ["u1"],
        "accepted_moves": ["old prose"],
        "candidate_ref": "candidate",
        "pangram_task_id": "task",
        "final_local_gates": {"regressions_hard_pass": True, "hard_pass": True},
        "supervisor_resume_node": "generation",
    }

    update = apply_supervisor_action(
        state,
        SupervisorAction(
            kind="CORRECT_MEANING",
            instruction="The choice belongs to the community, not the institution.",
            reason="The actor was wrong.",
            restart_depth="REPRESENTATION_FROM_SOURCE",
        ),
    )
    merged = {**state, **update}

    assert merged["thread_id"] == "thread-1"
    assert merged["source_ref"] == "source"
    assert merged["requirements_ref"] == "requirements"
    assert merged["owner_gold_ref"] == "owner-gold"
    assert merged["protected_input_hashes"] == {"INPUT.md": "hash"}
    assert merged["section_job"] == ""
    assert merged["atom_refs"] == []
    assert merged["accepted_moves"] == []
    assert merged["candidate_ref"] == ""
    assert merged["pangram_task_id"] == ""
    assert merged["final_local_gates"] == {"regressions_hard_pass": True}
    assert merged["supervisor_resume_node"] == "representation"
    assert merged["owner_authority_corrections"][-1]["instruction"].startswith("The choice")


def test_reject_proposal_requires_exact_visible_reference_and_hash():
    proposal_text = "Visible proposal."
    proposal_ref = sha256(proposal_text.encode()).hexdigest()
    snapshot = SupervisorSnapshot(
        thread_id="thread-1",
        resume_node="generation",
        latest_proposal=VisibleProposal(
            proposal_ref=proposal_ref,
            proposal_sha256=proposal_ref,
            text=proposal_text,
            node="generation",
        ),
    )
    state = {"accepted_moves": ["preserved"], "supervisor_resume_node": "generation"}

    with pytest.raises(StaleSupervisorAction):
        apply_supervisor_action(
            state,
            SupervisorAction(
                kind="REJECT_PROPOSAL",
                reason="It dodges the question.",
                proposal_ref="b" * 64,
                proposal_sha256=proposal_ref,
            ),
            snapshot=snapshot,
        )

    update = apply_supervisor_action(
        state,
        SupervisorAction(
            kind="REJECT_PROPOSAL",
            reason="It dodges the question.",
            proposal_ref=proposal_ref,
            proposal_sha256=proposal_ref,
        ),
        snapshot=snapshot,
    )
    merged = {**state, **update}
    assert merged["accepted_moves"] == ["preserved"]
    assert merged["rejected_proposals"][-1]["proposal_ref"] == proposal_ref
    assert merged["supervisor_resume_node"] == "generation"


def test_resume_unchanged_preserves_atomic_pangram_task_and_destination():
    state = {
        "pangram_task_id": "task-1",
        "pangram_candidate_ref": "candidate-1",
        "supervisor_resume_node": "detector",
        "supervisor_pre_pause_status": "detector_poll",
    }

    update = apply_supervisor_action(
        state,
        SupervisorAction(kind="RESUME_UNCHANGED", reason="Continue."),
    )
    merged = {**state, **update}

    assert merged["pangram_task_id"] == "task-1"
    assert merged["pangram_candidate_ref"] == "candidate-1"
    assert merged["supervisor_resume_node"] == "detector"
    assert merged["status"] == "detector_poll"


@pytest.mark.parametrize("payload", [
    {"kind": "ROLLBACK", "reason": "bad", "rollback_count": 0},
    {"kind": "REDIRECT", "reason": "bad", "instruction": "x", "scope": "NONE"},
    {"kind": "REDIRECT", "reason": "bad", "instruction": "", "scope": "NEXT_ATTEMPT"},
    {"kind": "CORRECT_MEANING", "reason": "bad", "instruction": ""},
    {"kind": "REJECT_PROPOSAL", "reason": "bad", "proposal_ref": "", "proposal_sha256": ""},
    {"kind": "RESUME_UNCHANGED", "reason": "ok", "extra": "forbidden"},
    {"kind": "RESUME_UNCHANGED", "reason": "ok", "rollback_count": 1},
    {"kind": "RESUME_UNCHANGED", "reason": "ok", "scope": "CURRENT_ARTICLE"},
    {"kind": "ROLLBACK", "reason": "bad", "rollback_count": 1, "proposal_ref": "p"},
    {"kind": "REDIRECT", "reason": "bad", "instruction": "x", "scope": "NEXT_ATTEMPT", "rollback_count": 1},
])
def test_malformed_actions_fail_before_mutation(payload):
    with pytest.raises(ValidationError):
        SupervisorAction.model_validate(payload)


def test_normalized_action_describes_effect_without_mutating_snapshot():
    snapshot = SupervisorSnapshot(
        thread_id="thread-1",
        accepted_moves=["one", "two"],
        resume_node="generation",
    )
    before = snapshot.model_dump(mode="json")

    action, effect = normalize_action(
        ProposedSupervisorAction(
            kind="ROLLBACK",
            reason="Remove the false turn.",
            rollback_count=1,
        ),
        snapshot,
    )

    assert action.kind == "ROLLBACK"
    assert effect.removed_moves == ["two"]
    assert "candidate_ref" in effect.invalidated_fields
    assert snapshot.model_dump(mode="json") == before


def test_supervisor_session_store_is_durable_and_path_bounded(tmp_path):
    sessions = SupervisorSessionStore(tmp_path / "supervisor")
    ref = sessions.create("thread-1", "pause-1")
    sessions.append(ref, "user", "What is happening?")
    sessions.append(ref, "assistant", "The fidelity guard rejected the proposal.")

    reopened = SupervisorSessionStore(tmp_path / "supervisor")
    assert [row["role"] for row in reopened.read(ref)] == ["user", "assistant"]
    assert reopened.read(ref)[0]["text"] == "What is happening?"

    with pytest.raises(ValueError):
        sessions.append("../escape.jsonl", "user", "no")
