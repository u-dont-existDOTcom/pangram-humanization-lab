from authorial_flow.authority import Authority, AuthorityUnit
from authorial_flow.learning import LearningScope, LearningStore
from authorial_flow.modes import TaskMode, choose_mode
from authorial_flow.nodes.developmental import ArchitectureCard, build_developmental_result
from authorial_flow.nodes.generate import writer_payload
from authorial_flow.nodes.owner_interrupt import capture_owner_response, minimal_authorial_question
from authorial_flow.nodes.semantic_sanity import evaluate_semantic_sanity
from authorial_flow.research.base import ResearchQuestion, SearchHit, RetrievedSource
from authorial_flow.research.evidence import AccessLevel, EvidenceRecord
from authorial_flow.nodes.research import run_bounded_research
from authorial_flow.source_provenance import SourceProvenance


class Provider:
    def search(self,q,limit): return [SearchHit(title='source',url='https://example.test',primary_hint=True)]
class Fetcher:
    def fetch(self,url): return RetrievedSource(url=url,final_url=url,mime_type='text/plain',body='primary',body_sha256='sha',retrieved_at=1,access_level=AccessLevel.FULL_TEXT,headers={})


def test_ai_draft_semantic_repair_drops_ai_bridge_without_forcing_coverage():
    mode=choose_mode('humanize',SourceProvenance.AI_FROM_OWNER_INPUTS,semantic_sanity=False)
    assert mode.mode is TaskMode.P3
    sanity=evaluate_semantic_sanity({'wrong_thought':True},task_mode=mode.mode)
    assert sanity.recommended_escalation == 'P4'
    units=[
        AuthorityUnit(id='owner',text='My choices arise from conditions.',authority=Authority.OWNER_GROUNDED),
        AuthorityUnit(id='bridge',text='The suttas answer the question.',authority=Authority.AI_PROVISIONAL),
    ]
    card=ArchitectureCard(real_pressure='If choices are conditioned, what exactly is choosing?',reader_stake='understand the question',controlling_claim='choices are conditioned',governing_movement='inquiry',stopping_point='unresolved chooser question')
    dev=build_developmental_result(units,[
        {'id':'owner','disposition':'use','text':'My choices arise from conditions.','reason':'owner-grounded'},
        {'id':'bridge','disposition':'omit','reason':'AI bridge was not source-licensed'},
    ],card=card)
    payload=writer_payload('develop the inquiry',[units[0]],[],{'state':'OPEN'})
    assert 'The suttas answer the question.' not in str(payload)
    assert dev.corrected_units[1]['disposition']=='omit'


def test_research_route_stays_separate_from_owner_position_and_detector_fields():
    q=ResearchQuestion(uncertainty='Does citation answer question?',material_consequence='Changes route')
    out=run_bounded_research(q,provider=Provider(),fetcher=Fetcher(),faithful_position_ref='owner:position',max_queries=1,max_sources=1,
        assessor=lambda q,s:[EvidenceRecord(source_ref='sha',access_level=AccessLevel.FULL_TEXT,primary_status='primary',supports=['citation content'],resists=['answer relation'],system_inference=['consider another route'])])
    assert out.faithful_position_ref=='owner:position'
    assert out.better_reasoned_alternative_ref
    assert out.owner_position_changed is False


def test_irreducible_authorial_answer_becomes_project_authority_then_rejoins_thought_flow(tmp_path):
    q=minimal_authorial_question('u-open',['There is no chooser','There is choosing but no separate chooser'],'The next thought differs.')
    assert q['kind']=='AUTHORIAL_AMBIGUITY'
    store=LearningStore(tmp_path)
    state={'project_id':'p','accepted_moves':['Choices are conditioned.'],'regression_version':'3','open_authorial_unit_id':'u-open'}
    update=capture_owner_response(state,{'kind':'ANSWER','answer':'There is choosing but no separate chooser'},store,interrupt_kind='AUTHORIAL_AMBIGUITY')
    rec=store.records()[0]
    assert rec.scope is LearningScope.PROJECT_AUTHORITY
    assert update['resolved_authorial_answer']=='There is choosing but no separate chooser'
    resolved=AuthorityUnit(id='u-open',text=update['resolved_authorial_answer'],authority=Authority.OWNER_GROUNDED)
    payload=writer_payload('continue from corrected concept',[resolved],['Choices are conditioned.'],{'state':'OPEN','live_pressure':'then what is choosing?'})
    assert payload['units'][0]['authority']=='OWNER_GROUNDED'
