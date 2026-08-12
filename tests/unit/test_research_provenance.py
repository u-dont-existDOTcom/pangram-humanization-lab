from authorial_flow.research.evidence import EvidenceRecord, AccessLevel
from authorial_flow.research.base import SearchHit, ResearchQuestion
from authorial_flow.research.discovery import DirectURLProvider


def test_evidence_separates_source_support_from_inference():
    r=EvidenceRecord(
        source_ref='sha:1',access_level=AccessLevel.FULL_TEXT,primary_status='primary',
        supports=['AN 6.63 states X'],resists=[],system_inference=['This may bear on free will']
    )
    assert r.supports != r.system_inference


def test_direct_url_provider_extracts_existing_urls_without_search_credentials():
    p=DirectURLProvider('See https://example.org/a and https://example.org/b.')
    hits=p.search('question',limit=3)
    assert [h.url for h in hits] == ['https://example.org/a','https://example.org/b']


def test_research_question_records_material_consequence():
    q=ResearchQuestion(uncertainty='Does source X answer the question?',material_consequence='Could change the argument route')
    assert q.material_consequence
