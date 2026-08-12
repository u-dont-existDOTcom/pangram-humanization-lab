from authorial_flow.learning import LearningKind, LearningScope, LearningStore
from authorial_flow.nodes.owner_interrupt import (
    capture_owner_response, minimal_authorial_question, validate_owner_response,
)
from authorial_flow.routing import route_after_owner_learning


def test_bad_edge_directly_becomes_project_authority_and_routes_regeneration(tmp_path):
    store=LearningStore(tmp_path)
    state={'project_id':'p','accepted_moves':['one','two','three','four'],'regression_version':'7'}
    update=capture_owner_response(
        state,{'kind':'BAD_EDGE','move_index':4,'note':'This does not follow.'},store
    )
    records=store.records()
    assert len(records)==1
    assert records[0].kind is LearningKind.LOCAL_EDGE
    assert records[0].scope is LearningScope.PROJECT_AUTHORITY
    assert update['regression_version']=='8'
    assert route_after_owner_learning(update) == 'regressions'


def test_global_shape_is_separate_label_not_fake_edge(tmp_path):
    store=LearningStore(tmp_path)
    state={'project_id':'p','accepted_moves':['one','two','three'],'regression_version':'1'}
    update=capture_owner_response(state,{'kind':'GLOBAL_PRECOMPUTED_SHAPE','note':'Feels outlined.'},store)
    rec=store.records()[0]
    assert rec.kind is LearningKind.GLOBAL_PRECOMPUTED_SHAPE
    assert 'move_index' not in rec.payload
    assert route_after_owner_learning(update) == 'regressions'


def test_minimal_authorial_question_contains_competing_interpretations_only():
    q=minimal_authorial_question(
        'u7',['No chooser exists','Choosing exists but no separate chooser is needed'],
        'The choice changes which claim the next paragraph develops.'
    )
    assert q['kind']=='AUTHORIAL_AMBIGUITY'
    assert q['unit_id']=='u7'
    assert q['interpretations']==['No chooser exists','Choosing exists but no separate chooser is needed']
    assert 'model' not in str(q).lower()
    assert 'log' not in str(q).lower()


def test_research_adoption_is_project_authority_not_general_rule(tmp_path):
    store=LearningStore(tmp_path)
    state={'project_id':'p','accepted_moves':['one'],'regression_version':'2','better_reasoned_alternative_ref':'alt:1'}
    update=capture_owner_response(state,{'kind':'ADOPT_ALTERNATIVE','note':'Use the researched route.'},store,interrupt_kind='RESEARCH_ADOPTION')
    rec=store.records()[0]
    assert rec.scope is LearningScope.PROJECT_AUTHORITY
    assert rec.kind is LearningKind.RESEARCH_DIRECTION
    assert update['adopted_alternative_ref']=='alt:1'


def test_runtime_owner_learning_preserves_authorial_ambiguity_interrupt_kind(tmp_path):
    from types import SimpleNamespace
    from authorial_flow.runtime import _owner_learning_node

    store = LearningStore(tmp_path)
    state = {
        'project_id': 'p',
        'accepted_moves': [],
        'regression_version': '2',
        'active_interrupt_kind': 'AUTHORIAL_AMBIGUITY',
        'open_authorial_unit_id': 'u7',
        'owner_response': {'kind': 'ANSWER', 'answer': 'Choosing happens without a separate chooser.'},
    }
    update = _owner_learning_node(state, SimpleNamespace(learning_store=store))

    assert update['status'] == 'owner_feedback'
    assert update['resolved_authorial_answer'] == 'Choosing happens without a separate chooser.'
    assert store.records()[0].kind is LearningKind.MEANING_CORRECTION


def test_research_adoption_interrupt_node_marks_response_context_for_learning(monkeypatch):
    import sys, types
    from authorial_flow.nodes import owner_interrupt as module

    langgraph = types.ModuleType('langgraph')
    langgraph_types = types.ModuleType('langgraph.types')
    langgraph_types.interrupt = lambda payload: {'kind':'ADOPT_ALTERNATIVE','note':'Use research route.'}
    monkeypatch.setitem(sys.modules,'langgraph',langgraph)
    monkeypatch.setitem(sys.modules,'langgraph.types',langgraph_types)

    update = module.owner_research_adoption_node({
        'faithful_position_ref':'faithful:1',
        'better_reasoned_alternative_ref':'alt:1',
        'accepted_moves':[],
    })
    assert update['owner_response']['kind']=='ADOPT_ALTERNATIVE'
    assert update['active_interrupt_kind']=='RESEARCH_ADOPTION'
