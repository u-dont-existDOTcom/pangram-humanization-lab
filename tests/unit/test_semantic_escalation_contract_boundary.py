from authorial_flow.nodes.repair import repair_node
from authorial_flow.routing import route_after_representation


def test_invalid_semantic_contract_routes_to_machine_repair_before_owner_interrupt():
    state = {
        "status": "owner_ambiguity_required",
        "semantic_escalation_error": "FAIL_WITHOUT_ACTION",
        "interrupt_payload": {
            "kind": "AUTHORIAL_AMBIGUITY",
            "question": "Semantic sanity failed without a valid bounded escalation. Which meaning and source role should control?",
        },
    }
    assert route_after_representation(state) == "repair"


def test_genuine_owner_ambiguity_still_routes_to_owner():
    assert route_after_representation({"status": "owner_ambiguity_required"}) == "owner_ambiguity"


def test_repair_sanitizes_semantic_contract_failure_before_cycle_and_on_bounded_stop():
    seen = {}

    def exhausted_cycle(state):
        seen.update(state)
        return {
            "outcome": "NON_APPLICABLE_STOP",
            "reason": "REPAIR_BUDGET_EXHAUSTED",
            "exhausted": True,
            "error_ref": "",
        }

    result = repair_node(
        {
            "status": "owner_ambiguity_required",
            "semantic_escalation_error": "FAIL_WITHOUT_ACTION",
            "interrupt_payload": {
                "kind": "AUTHORIAL_AMBIGUITY",
                "question": "synthetic fallback question",
            },
            "authorial_information_missing": True,
        },
        exhausted_cycle,
    )

    assert seen["status"] == "machine_failure"
    assert seen["failure_class"] == "SEMANTIC_DEVELOPMENTAL"
    assert seen["failure_origin_node"] == "semantic_sanity"
    assert seen["failure_code"] == "SEMANTIC_ESCALATION_CONTRACT_FAIL_WITHOUT_ACTION"
    assert seen["authorial_information_missing"] is False
    assert seen["interrupt_payload"] == {}

    assert result["status"] == "bounded_machine_stop"
    assert result["failure_class"] == "SEMANTIC_DEVELOPMENTAL"
    assert result["authorial_information_missing"] is False
    assert result["interrupt_payload"] == {}
    assert result["active_interrupt_kind"] == ""


def test_semantic_contract_failure_cannot_reenter_owner_lane_from_repair_planner():
    def bad_cycle(_state):
        return {
            "outcome": "STAGED_FOR_OWNER",
            "owner_judgment_required": True,
            "owner_question": "fake owner question",
            "error_ref": "plan-ref",
        }

    result = repair_node(
        {
            "status": "owner_ambiguity_required",
            "semantic_escalation_error": "CONTRADICTORY_PASS",
            "interrupt_payload": {
                "kind": "AUTHORIAL_AMBIGUITY",
                "question": "old fallback",
            },
        },
        bad_cycle,
    )

    assert result["status"] == "bounded_machine_stop"
    assert result["repair_error"] == "UNJUSTIFIED_OWNER_ESCALATION_FROM_SEMANTIC_CONTRACT_FAILURE"
    assert result["interrupt_payload"] == {}
    assert result["authorial_information_missing"] is False


def test_semantic_sanity_prompt_forbids_fail_basic_and_requires_concrete_owner_question():
    from pathlib import Path

    prompt = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "authorial_flow"
        / "prompts"
        / "semantic_sanity.md"
    ).read_text(encoding="utf-8")
    assert "Never return `FAIL` + `BASIC`" in prompt
    assert "must name the concrete competing meanings" in prompt
