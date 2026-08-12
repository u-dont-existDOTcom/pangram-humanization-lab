from authorial_flow.candidates import CandidateRecord, select_presentation
from authorial_flow.nodes.rank_candidates import rank_candidates_blind


def test_cosmetic_variants_do_not_create_multiple_visible_options():
    a=CandidateRecord(id='a',text='A',role='CONSERVATIVE',material_route='route-1',editorial_score=9)
    b=CandidateRecord(id='b',text='B',role='CONSERVATIVE',material_route='route-1',editorial_score=8)
    shown=select_presentation([a,b])
    assert shown.recommended_id == 'a'
    assert shown.alternatives == []


def test_materially_different_better_reasoned_route_can_be_shown():
    a=CandidateRecord(id='a',text='faithful',role='DEVELOPMENTAL',material_route='owner-position',editorial_score=9)
    b=CandidateRecord(id='b',text='alternative',role='BETTER_REASONED_ALTERNATIVE',material_route='evidence-diverges',editorial_score=9.2)
    shown=select_presentation([a,b])
    assert {shown.recommended_id,*shown.alternatives} == {'a','b'}


def test_editorial_rank_ignores_pangram_fields():
    a=CandidateRecord(id='a',text='strong',role='DEVELOPMENTAL',material_route='r1',editorial_score=9,pangram={'prediction_short':'AI'})
    b=CandidateRecord(id='b',text='weak',role='CONSERVATIVE',material_route='r2',editorial_score=7,pangram={'prediction_short':'Human'})
    ranking=rank_candidates_blind([a,b])
    assert ranking.winner_id == 'a'
    assert ranking.order[0] == 'a'
