from authorial_flow.research.base import SearchHit, RetrievedSource, ResearchQuestion
from authorial_flow.research.evidence import AccessLevel, EvidenceRecord
from authorial_flow.nodes.research import run_bounded_research


class FakeProvider:
    def search(self,query,limit):
        return [SearchHit(title='Primary',url='https://example.test/primary',snippet='x',primary_hint=True)]


class FakeFetcher:
    def fetch(self,url):
        return RetrievedSource(url=url,final_url=url,mime_type='text/plain',body='Source says something different.',body_sha256='abc',retrieved_at=1.0,access_level=AccessLevel.FULL_TEXT,headers={})


def assessor(question,sources):
    return [EvidenceRecord(
        source_ref='abc',access_level=AccessLevel.FULL_TEXT,primary_status='primary',
        supports=['The inherited citation does not directly answer the live question'],
        resists=['Inherited source role'],system_inference=['A different route is better supported']
    )]


def test_research_can_create_better_reasoned_alternative_without_changing_owner_position():
    q=ResearchQuestion(uncertainty='Does citation answer the question?',material_consequence='May change route')
    out=run_bounded_research(
        q,provider=FakeProvider(),fetcher=FakeFetcher(),assessor=assessor,
        faithful_position_ref='owner:faithful',max_queries=1,max_sources=2,
    )
    assert out.faithful_position_ref == 'owner:faithful'
    assert out.better_reasoned_alternative_ref
    assert out.owner_position_changed is False
    assert out.evidence[0].supports != out.evidence[0].system_inference
