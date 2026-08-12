from authorial_flow.nodes.semantic_sanity import SemanticSanityResult, evaluate_semantic_sanity
from authorial_flow.routing import route_after_semantic_sanity
from authorial_flow.modes import TaskMode


def test_bad_ai_architecture_routes_to_p4_not_writer():
    result=SemanticSanityResult(status='FAIL',defect_types=('wrong_thought',),recommended_escalation='P4')
    assert route_after_semantic_sanity(result) == 'developmental'


def test_source_choice_uncertainty_routes_to_research():
    result=SemanticSanityResult(status='FAIL',defect_types=('source_role',),research_trigger=True,recommended_escalation='RESEARCH')
    assert route_after_semantic_sanity(result) == 'research'


def test_explicit_p2s_substantive_failure_routes_owner_boundary():
    result=evaluate_semantic_sanity(
        {'wrong_thought':True}, task_mode=TaskMode.P2S
    )
    assert result.recommended_escalation == 'OWNER'
    assert route_after_semantic_sanity(result) == 'owner_ambiguity'


def test_sane_thought_stays_basic():
    result=evaluate_semantic_sanity({},task_mode=TaskMode.P3)
    assert result.status == 'PASS'
    assert route_after_semantic_sanity(result) == 'basic'


def test_runtime_representation_owner_ambiguity_routes_to_interrupt_not_writer():
    from authorial_flow.routing import route_after_representation
    assert route_after_representation({'status':'owner_ambiguity_required'}) == 'owner_ambiguity'
