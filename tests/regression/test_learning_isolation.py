import json
from authorial_flow.authority import Authority, AuthorityUnit
from authorial_flow.learning import LearningStore
from authorial_flow.nodes.generate import writer_payload


def test_writer_never_receives_owner_example_text(tmp_path):
    bad='Not that choices do not matter — this is the exact owner-labeled bad candidate.'
    store=LearningStore(tmp_path)
    store.append_owner_judgment(kind='LOCAL_EDGE',project_id='p',payload={'candidate':bad,'verdict':'FAIL'})
    payload=writer_payload('job',[AuthorityUnit(id='u',text='owner proposition',authority=Authority.OWNER_GROUNDED)],[],{'state':'OPEN'},promoted_rules=store.promoted_rules())
    blob=json.dumps(payload)
    assert bad not in blob
    assert 'owner_gold' not in blob


def test_locked_test_case_bodies_are_excluded_from_hypothesis_view(tmp_path):
    store=LearningStore(tmp_path)
    store.append_owner_judgment(kind='LOCAL_EDGE',project_id='p',payload={'candidate':'secret locked body'},partition='locked-test')
    assert 'secret locked body' not in json.dumps(store.hypothesis_view())
