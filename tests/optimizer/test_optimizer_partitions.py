import json
from authorial_flow.learning import LearningStore
from authorial_flow.optimizer.program import ProgramBundle
from authorial_flow.optimizer.search import OptimizerSearch


def test_proposal_builder_never_receives_locked_test_bodies(tmp_path):
    store=LearningStore(tmp_path)
    store.append_owner_judgment(kind='LOCAL_EDGE',project_id='p',payload={'candidate':'DEV_CASE_TEXT'},partition='dev')
    store.append_owner_judgment(kind='LOCAL_EDGE',project_id='p',payload={'candidate':'LOCKED_SECRET_CASE_TEXT'},partition='locked-test')
    search=OptimizerSearch(proposer=lambda payload,base: None,evaluator=lambda program,partition: None)
    proposal_input=search.build_proposal_input(store)
    assert 'LOCKED_SECRET_CASE_TEXT' not in proposal_input
    assert 'DEV_CASE_TEXT' in proposal_input
    manifest=search.partition_manifest(store)
    assert 'locked-test' in manifest


def test_program_bundle_id_changes_with_prompt_hash():
    a=ProgramBundle.build({'edge':'aaa'},{'threshold':.8},graph_compatibility='1')
    b=ProgramBundle.build({'edge':'bbb'},{'threshold':.8},graph_compatibility='1')
    assert a.id != b.id
