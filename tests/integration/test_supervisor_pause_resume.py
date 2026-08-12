from pathlib import Path

import pytest

pytest.importorskip("langgraph")
from langgraph.types import Command

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.config import RuntimeConfig
from authorial_flow.events import EventJournal
from authorial_flow.graph import GraphDependencies, open_graph
from authorial_flow.nodes.owner_interrupt import supervisor_pause_node
from authorial_flow.pause import OperationContext, OwnerPauseRequested
from authorial_flow.routing import route_after_detector, route_after_repair, route_generation
from authorial_flow.runtime import RuntimeServices, _detector_node, _guarded_node


def _services(tmp_path):
    state_dir = tmp_path / ".state"
    services = RuntimeServices.for_tests(
        claude=object(),
        codex=object(),
        pangram=None,
        artifact_store=ArtifactStore(state_dir / "artifacts"),
    )
    journal = EventJournal(state_dir / "events.jsonl")
    services.journal = journal
    services.work_feed.journal = journal
    return services


def _supervisor(services):
    return lambda state: supervisor_pause_node(
        state,
        artifact_store=services.artifact_store,
        learning_store=services.learning_store,
        journal=services.journal,
        work_feed=services.work_feed,
    )


def _cancel_once_dependencies(services, calls):
    def generation(state):
        calls["generation"] += 1
        if calls["generation"] == 1:
            raise OwnerPauseRequested(OperationContext(
                node="generation",
                operation="model_call",
                provider="claude",
                model="claude-opus-5",
                role="writer",
                cancelable=True,
            ))
        return {
            "accepted_moves": [*(state.get("accepted_moves") or []), "new move"],
            "status": "generated",
        }

    return GraphDependencies(
        regressions=lambda _state: {"status": "regressions_pass"},
        representation=lambda _state: {"status": "represented"},
        generation=_guarded_node(
            "generation",
            generation,
            services,
            natural_next=route_generation,
        ),
        cold_audit=lambda _state: {"status": "audited"},
        freeze=lambda _state: {"status": "frozen"},
        detector=lambda _state: {"status": "done"},
        supervisor=_supervisor(services),
    )


def test_cancelled_generation_pauses_and_resumes_same_thread_without_duplicate_move(tmp_path):
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _services(tmp_path)
    calls = {"generation": 0}
    deps = _cancel_once_dependencies(services, calls)
    graph_config = {"configurable": {"thread_id": "same-thread"}}
    seed = {
        "thread_id": "same-thread",
        "status": "start",
        "accepted_moves": ["preserved"],
    }

    with open_graph(cfg, deps) as app:
        first = app.invoke(seed, graph_config)
        assert "__interrupt__" in first, first
        assert first["__interrupt__"][0].value["kind"] == "SUPERVISOR"
        assert first["thread_id"] == "same-thread"
        assert first["accepted_moves"] == ["preserved"]
        assert first["supervisor_resume_node"] == "generation"

    with open_graph(cfg, deps) as app:
        second = app.invoke(Command(resume={
            "kind": "RESUME_UNCHANGED",
            "reason": "Continue.",
            "instruction": "",
            "scope": "NONE",
            "restart_depth": "CURRENT_STAGE",
            "rollback_count": 0,
            "proposal_ref": "",
            "proposal_sha256": "",
        }), graph_config)

    assert second["thread_id"] == "same-thread"
    assert second["accepted_moves"] == ["preserved", "new move"]
    assert calls["generation"] == 2


def test_invalid_action_reinterrupts_without_losing_original_resume_destination(tmp_path):
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _services(tmp_path)
    secret = "INVALID-ACTION-SECRET-4927"
    services.work_feed.secret_values = lambda: [secret]
    calls = {"generation": 0}
    deps = _cancel_once_dependencies(services, calls)
    graph_config = {"configurable": {"thread_id": "invalid-action-thread"}}
    seed = {
        "thread_id": "invalid-action-thread",
        "status": "start",
        "accepted_moves": ["preserved"],
        "pangram_task_id": "task-1",
    }

    with open_graph(cfg, deps) as app:
        app.invoke(seed, graph_config)
        invalid = app.invoke(Command(resume={
            "kind": "ROLLBACK",
            "reason": "bad count",
            "rollback_count": 0,
            "unexpected": secret,
        }), graph_config)
        assert invalid["__interrupt__"][0].value["kind"] == "SUPERVISOR"
        assert invalid["accepted_moves"] == ["preserved"]
        assert invalid["pangram_task_id"] == "task-1"
        assert invalid["supervisor_resume_node"] == "generation"
        assert invalid["supervisor_validation_error"]
        assert secret not in invalid["supervisor_validation_error"]
        assert secret not in str(invalid["__interrupt__"][0].value)
        assert secret not in services.journal.path.read_text(encoding="utf-8")

        recovered = app.invoke(Command(resume={
            "kind": "RESUME_UNCHANGED",
            "reason": "Continue.",
        }), graph_config)

    assert recovered["accepted_moves"] == ["preserved", "new move"]
    assert calls["generation"] == 2


def test_atomic_completed_node_checkpoints_update_and_resumes_at_natural_next(tmp_path):
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _services(tmp_path)
    calls = {"freeze": 0, "detector": 0}

    def freeze(_state):
        calls["freeze"] += 1
        services.pause_controller.request()
        return {"status": "frozen", "candidate_ref": "checkpointed-candidate"}

    def detector(_state):
        calls["detector"] += 1
        return {"status": "done"}

    deps = GraphDependencies(
        regressions=lambda _state: {"status": "regressions_pass"},
        representation=lambda _state: {"status": "represented"},
        generation=lambda _state: {"status": "generated"},
        cold_audit=lambda _state: {"status": "audited"},
        freeze=_guarded_node(
            "freeze",
            freeze,
            services,
            natural_next=lambda _state: "detector",
        ),
        detector=detector,
        supervisor=_supervisor(services),
    )
    graph_config = {"configurable": {"thread_id": "atomic-thread"}}

    with open_graph(cfg, deps) as app:
        first = app.invoke({
            "thread_id": "atomic-thread",
            "status": "start",
        }, graph_config)
        assert first["__interrupt__"][0].value["kind"] == "SUPERVISOR"
        assert first["candidate_ref"] == "checkpointed-candidate"
        assert first["supervisor_pause_mode"] == "ATOMIC_COMPLETE"
        assert first["supervisor_resume_node"] == "detector"
        assert calls == {"freeze": 1, "detector": 0}

        second = app.invoke(Command(resume={
            "kind": "RESUME_UNCHANGED",
            "reason": "Continue.",
        }), graph_config)

    assert second["status"] == "done"
    assert calls == {"freeze": 1, "detector": 1}


def test_pangram_task_id_is_checkpointed_before_pause_and_resume_polls_without_resubmit(tmp_path):
    import json

    from authorial_flow.models.pangram import PangramResult, PangramTask

    cfg = RuntimeConfig.from_root(tmp_path)
    services = _services(tmp_path)

    class AsyncPangram:
        def __init__(self):
            self.submits = 0
            self.polls = 0

        def ensure_access(self):
            return None

        def request_identity(self, candidate_hash):
            return "identity:" + candidate_hash

        def submit(self, text, candidate_hash):
            self.submits += 1
            services.pause_controller.request()
            return PangramTask("task-1", self.request_identity(candidate_hash), candidate_hash, "pangram-4")

        def poll(self, task_id):
            self.polls += 1
            assert task_id == "task-1"
            return PangramResult(
                "STAGE_SUCCESS", "4.0", "Human", 0.0, 0.0, (),
                {"stage": "STAGE_SUCCESS", "version": "4.0", "prediction_short": "Human"},
                True,
            )

    pangram = AsyncPangram()
    services.pangram = pangram
    text = "A frozen editorial winner."
    candidate = {
        "id": "candidate-parent", "text": text, "editorial_score": 1.0,
        "hard_pass": True, "frozen": True, "accepted_moves": (text,),
        "text_artifact_ref": "", "role": "DEVELOPMENTAL", "material_route": "live-thought-flow",
    }
    candidate_ref = services.artifact_store.put_text(
        json.dumps(candidate, default=list), "json", {"kind": "candidate-record"},
    ).sha256
    detector = _guarded_node(
        "detector",
        lambda state: _detector_node(state, services, Path(__file__).resolve().parents[2], cfg),
        services,
        natural_next=route_after_detector,
    )
    deps = GraphDependencies(
        regressions=lambda _state: {"status": "regressions_passed"},
        representation=lambda _state: {"status": "represented"},
        generation=lambda _state: {"status": "generated"},
        cold_audit=lambda _state: {"status": "local_gates_passed"},
        freeze=lambda _state: {"status": "candidate_frozen"},
        detector=detector,
        supervisor=_supervisor(services),
    )
    graph_config = {"configurable": {"thread_id": "pangram-pause-thread"}}
    seed = {
        "thread_id": "pangram-pause-thread",
        "status": "start",
        "candidate_ref": candidate_ref,
        "recommended_candidate_ref": candidate_ref,
        "final_local_gates": {"hard_pass": True},
    }

    with open_graph(cfg, deps) as app:
        first = app.invoke(seed, graph_config)
        assert "__interrupt__" in first, first
        assert first["__interrupt__"][0].value["kind"] == "SUPERVISOR"
        assert first["pangram_task_id"] == "task-1"
        assert first["supervisor_pause_mode"] == "ATOMIC_COMPLETE"
        assert first["supervisor_resume_node"] == "detector"
        assert pangram.submits == 1

    with open_graph(cfg, deps) as app:
        second = app.invoke(Command(resume={
            "kind": "RESUME_UNCHANGED",
            "reason": "Continue polling the checkpointed task.",
        }), graph_config)

    assert second["__interrupt__"][0].value["kind"] == "FINAL_REVIEW"
    assert pangram.submits == 1
    assert pangram.polls == 1


def test_repair_promotion_is_checkpointed_before_pause_and_not_repeated(tmp_path):
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _services(tmp_path)
    calls = {"repair": 0}

    def repair(_state):
        calls["repair"] += 1
        services.pause_controller.request()
        return {
            "status": "repair_promoted_restart_required",
            "restart_required": True,
            "program_version": "new-program",
            "repair_commit": "repair-sha",
            "repair_resume_node": "generation",
        }

    deps = GraphDependencies(
        regressions=lambda _state: {
            "status": "machine_failure",
            "failure_class": "PROVIDER_PLUMBING",
            "failure_origin_node": "generation",
            "failure_record_ref": "failure-ref",
        },
        representation=lambda _state: {"status": "represented"},
        generation=lambda _state: {"status": "generated"},
        cold_audit=lambda _state: {"status": "audited"},
        freeze=lambda _state: {"status": "frozen"},
        detector=lambda _state: {"status": "done"},
        repair=_guarded_node(
            "repair",
            repair,
            services,
            natural_next=route_after_repair,
        ),
        supervisor=_supervisor(services),
    )
    graph_config = {"configurable": {"thread_id": "repair-pause-thread"}}

    with open_graph(cfg, deps) as app:
        first = app.invoke({"thread_id": "repair-pause-thread", "status": "start"}, graph_config)
        assert first["__interrupt__"][0].value["kind"] == "SUPERVISOR"
        assert first["program_version"] == "new-program"
        assert first["repair_commit"] == "repair-sha"
        assert first["supervisor_pause_mode"] == "ATOMIC_COMPLETE"
        assert first["supervisor_resume_node"] == "repair_restart"
        assert calls["repair"] == 1

        second = app.invoke(Command(resume={
            "kind": "RESUME_UNCHANGED",
            "reason": "Proceed to the existing restart boundary.",
        }), graph_config)

    assert second["__interrupt__"][0].value["kind"] == "MACHINE_RESTART"
    assert second["program_version"] == "new-program"
    assert second["repair_commit"] == "repair-sha"
    assert calls["repair"] == 1


def test_rejection_with_snapshot_hash_that_does_not_match_artifact_reinterrupts_without_mutation(tmp_path):
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _services(tmp_path)
    calls = {"generation": 0}
    proposal_text = "Visible complete proposal."
    proposal_ref = services.artifact_store.put_text(
        proposal_text, "md", {"kind": "writer-proposal"},
    ).sha256
    mismatched_hash = "b" * 64
    services.work_feed.emit("proposal.complete", {
        "node": "generation",
        "proposal_ref": proposal_ref,
        "proposal_sha256": mismatched_hash,
        "text": proposal_text,
    })
    deps = _cancel_once_dependencies(services, calls)
    graph_config = {"configurable": {"thread_id": "stale-artifact-thread"}}
    seed = {
        "thread_id": "stale-artifact-thread",
        "status": "start",
        "accepted_moves": ["preserved"],
        "candidate_ref": "candidate-ref",
        "pangram_task_id": "task-1",
    }

    with open_graph(cfg, deps) as app:
        first = app.invoke(seed, graph_config)
        before = {
            key: first.get(key)
            for key in ("accepted_moves", "candidate_ref", "pangram_task_id")
        }
        invalid = app.invoke(Command(resume={
            "kind": "REJECT_PROPOSAL",
            "reason": "Reject only if this is the exact visible artifact.",
            "proposal_ref": proposal_ref,
            "proposal_sha256": mismatched_hash,
        }), graph_config)

    assert invalid["__interrupt__"][0].value["kind"] == "SUPERVISOR"
    assert {
        key: invalid.get(key)
        for key in before
    } == before
    assert invalid["supervisor_validation_error"]
    assert calls["generation"] == 1


@pytest.mark.parametrize("action", [
    {
        "kind": "ROLLBACK",
        "reason": "zero is invalid",
        "rollback_count": 0,
    },
    {
        "kind": "ROLLBACK",
        "reason": "too many moves",
        "rollback_count": 2,
    },
    {
        "kind": "RESUME_UNCHANGED",
        "reason": "extra fields fail closed",
        "unexpected": "not allowed",
    },
    {
        "kind": "REJECT_PROPOSAL",
        "reason": "stale proposal",
        "proposal_ref": "a" * 64,
        "proposal_sha256": "a" * 64,
    },
])
def test_malformed_or_stale_action_reinterrupts_with_content_and_detector_state_unchanged(tmp_path, action):
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _services(tmp_path)
    calls = {"generation": 0}
    deps = _cancel_once_dependencies(services, calls)
    graph_config = {"configurable": {"thread_id": "invalid-action-matrix"}}
    seed = {
        "thread_id": "invalid-action-matrix",
        "status": "start",
        "accepted_moves": ["preserved"],
        "candidate_ref": "candidate-ref",
        "pangram_task_id": "task-1",
        "pangram_candidate_ref": "candidate-ref",
    }

    with open_graph(cfg, deps) as app:
        first = app.invoke(seed, graph_config)
        before = {
            key: first.get(key)
            for key in (
                "accepted_moves", "candidate_ref", "pangram_task_id", "pangram_candidate_ref",
            )
        }
        invalid = app.invoke(Command(resume=action), graph_config)

    assert invalid["__interrupt__"][0].value["kind"] == "SUPERVISOR"
    assert {key: invalid.get(key) for key in before} == before
    assert invalid["supervisor_validation_error"]
    assert calls["generation"] == 1


@pytest.mark.parametrize("failure", ["missing-move", "unknown-unit"])
def test_invalid_coverage_reconciliation_reinterrupts_without_truncating_moves(tmp_path, failure):
    from hashlib import sha256

    cfg = RuntimeConfig.from_root(tmp_path)
    services = _services(tmp_path)
    calls = {"generation": 0}
    moves = ["one", "two"]
    if failure == "missing-move":
        reconciled = {"moves": []}
    else:
        reconciled = {"moves": [
            {
                "index": index,
                "move_sha256": sha256(move.encode()).hexdigest(),
                "covered_unit_ids": ["unknown-unit"] if index == 0 else [],
            }
            for index, move in enumerate(moves)
        ]}
    deps = _cancel_once_dependencies(services, calls)
    deps = GraphDependencies(
        **{
            **deps.__dict__,
            "supervisor": lambda state: supervisor_pause_node(
                state,
                artifact_store=services.artifact_store,
                learning_store=services.learning_store,
                journal=services.journal,
                work_feed=services.work_feed,
                reconcile_coverage=lambda _state: reconciled,
            ),
        }
    )
    graph_config = {"configurable": {"thread_id": "coverage-thread"}}
    seed = {
        "thread_id": "coverage-thread",
        "status": "start",
        "accepted_moves": moves,
        "accepted_move_coverage": [],
        "atom_coverage": {"u1": True},
        "pangram_task_id": "task-1",
    }

    with open_graph(cfg, deps) as app:
        app.invoke(seed, graph_config)
        invalid = app.invoke(Command(resume={
            "kind": "ROLLBACK",
            "reason": "Remove the second move only after coverage validates.",
            "rollback_count": 1,
        }), graph_config)

    assert invalid["__interrupt__"][0].value["kind"] == "SUPERVISOR"
    assert invalid["accepted_moves"] == moves
    assert invalid["pangram_task_id"] == "task-1"
    assert invalid["supervisor_validation_error"]


def test_invalid_resume_destination_reinterrupts_without_running_machine_node(tmp_path):
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _services(tmp_path)
    calls = {"generation": 0}

    def generation(_state):
        calls["generation"] += 1
        services.pause_controller.request()
        return {"status": "continue_generation", "accepted_moves": ["preserved"]}

    deps = GraphDependencies(
        regressions=lambda _state: {"status": "regressions_pass"},
        representation=lambda _state: {"status": "represented"},
        generation=_guarded_node(
            "generation", generation, services, natural_next=lambda _state: "outside-graph",
        ),
        cold_audit=lambda _state: {"status": "audited"},
        freeze=lambda _state: {"status": "frozen"},
        detector=lambda _state: {"status": "done"},
        supervisor=_supervisor(services),
    )
    graph_config = {"configurable": {"thread_id": "invalid-resume-thread"}}

    with open_graph(cfg, deps) as app:
        first = app.invoke({"thread_id": "invalid-resume-thread", "status": "start"}, graph_config)
        assert first["supervisor_resume_node"] == "outside-graph"
        invalid = app.invoke(Command(resume={
            "kind": "RESUME_UNCHANGED",
            "reason": "Continue only to a fixed graph destination.",
        }), graph_config)

    assert invalid["__interrupt__"][0].value["kind"] == "SUPERVISOR"
    assert invalid["accepted_moves"] == ["preserved"]
    assert calls["generation"] == 1
