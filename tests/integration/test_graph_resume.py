import pytest

langgraph=pytest.importorskip("langgraph", reason="real LangGraph integration runs after dependency installation")
from langgraph.types import Command

from authorial_flow.config import RuntimeConfig
from authorial_flow.graph import GraphDependencies, open_graph


def passthrough(state):
    return {}


def test_owner_interrupt_resumes_same_thread_after_sqlite_reopen(tmp_path):
    cfg=RuntimeConfig.from_root(tmp_path)
    deps=GraphDependencies(
        regressions=passthrough,
        representation=passthrough,
        generation=lambda state: {"accepted_moves":["one","two"],"status":"generated"},
        cold_audit=passthrough,
        freeze=passthrough,
        # This stub represents the *post-Pangram Human* detector contract.
        # Local hard-pass alone must never authorize owner review, because that
        # would let the graph bypass the required Pangram-Human gate.
        detector=lambda state: {
            "status":"owner_review_ready",
            "final_local_gates":{"hard_pass":True,"pangram_human":True},
        },
    )
    run_cfg={"configurable":{"thread_id":"thread-1"}}
    with open_graph(cfg,deps) as app:
        first=app.invoke({"status":"start"},run_cfg)
        assert "__interrupt__" in first
        assert first["__interrupt__"][0].value["kind"] == "FINAL_REVIEW"

    with open_graph(cfg,deps) as app:
        second=app.invoke(Command(resume={"kind":"ACCEPT"}),run_cfg)
        assert second["status"] == "accepted"



def test_promoted_repair_restart_boundary_preserves_same_thread_and_moves(tmp_path):
    cfg=RuntimeConfig.from_root(tmp_path)

    def fail_machine(state):
        return {
            "status":"machine_failure",
            "failure_origin_node":"generation",
            "failure_record_ref":"failure-ref",
            "failure_class":"PROVIDER_PLUMBING",
        }

    deps=GraphDependencies(
        regressions=fail_machine,
        representation=passthrough,
        generation=lambda state: {"status":"generated"},
        cold_audit=passthrough,
        freeze=passthrough,
        detector=lambda state: {"status":"done"},
        repair=lambda state: {
            "status":"repair_promoted_restart_required",
            "restart_required":True,
            "program_version":"new-program",
            "repair_resume_node":"generation",
            "repair_commit":"repair-sha",
            "failure_record_ref":state.get("failure_record_ref","failure-ref"),
            "failure_class":state.get("failure_class","PROVIDER_PLUMBING"),
        },
    )
    run_cfg={"configurable":{"thread_id":"thread-repair"}}
    seed={"status":"start","thread_id":"thread-repair","accepted_moves":["one"],"section_job":"preserve-this-representation"}

    with open_graph(cfg,deps) as app:
        first=app.invoke(seed,run_cfg)
        assert "__interrupt__" in first
        assert first["__interrupt__"][0].value["kind"] == "MACHINE_RESTART"
        assert first["accepted_moves"] == ["one"]
        assert first["repair_resume_node"] == "generation"
        assert first["section_job"] == "preserve-this-representation"

    with open_graph(cfg,deps) as app:
        second=app.invoke(Command(resume={"kind":"MACHINE_RESTART_RESUME"}),run_cfg)
        assert second["accepted_moves"] == ["one"]
        assert second["section_job"] == "preserve-this-representation"
        assert second["failure_class"] == ""
        assert second["failure_record_ref"] == ""
        assert second["restart_required"] is False
        assert second["status"] == "done"


def test_terminal_bounded_stop_can_replay_failed_node_on_same_sqlite_thread(tmp_path):
    from authorial_flow.cli import replay_terminal_machine_failure_on_app

    cfg=RuntimeConfig.from_root(tmp_path)
    run_cfg={"configurable":{"thread_id":"thread-bounded-recovery"}}

    def old_generation_failure(state):
        return {
            "status":"machine_failure",
            "failure_origin_node":"generation",
            "failure_record_ref":"old-failure-ref",
            "failure_class":"PROVIDER_PLUMBING",
        }

    old_deps=GraphDependencies(
        regressions=passthrough, representation=passthrough, generation=old_generation_failure,
        cold_audit=passthrough, freeze=passthrough, detector=lambda state:{"status":"done"},
        repair=lambda state:{
            "status":"bounded_machine_stop", "repair_attempt":6,
            "failure_origin_node":"generation", "failure_record_ref":"old-failure-ref",
            "failure_class":"PROVIDER_PLUMBING",
        },
    )
    seed={
        "status":"start", "thread_id":"thread-bounded-recovery",
        "accepted_moves":["preserved move"], "section_job":"preserved representation",
    }
    with open_graph(cfg,old_deps) as app:
        terminal=app.invoke(seed,run_cfg)
        assert terminal["status"]=="bounded_machine_stop"
        assert app.get_state(run_cfg).next==()

    new_deps=GraphDependencies(
        regressions=passthrough, representation=passthrough,
        generation=lambda state:{"status":"generated"},
        cold_audit=passthrough, freeze=passthrough, detector=lambda state:{"status":"done"},
        repair=lambda state:{"status":"bounded_machine_stop"},
    )
    with open_graph(cfg,new_deps) as app:
        recovered=replay_terminal_machine_failure_on_app(app,run_cfg,terminal)
        assert recovered["status"]=="done"
        assert recovered["accepted_moves"]==["preserved move"]
        assert recovered["section_job"]=="preserved representation"
        assert recovered.get("failure_origin_node","") in {"","generation"}
