from authorial_flow.authority import Authority, AuthorityUnit
from authorial_flow.nodes.generate import candidate_semantic_spans


def test_ai_provisional_is_not_automatically_mandatory():
    unit = AuthorityUnit(id="u1", text="AI bridge", authority=Authority.AI_PROVISIONAL)
    assert unit.must_preserve is False


def test_owner_locked_is_mandatory():
    unit = AuthorityUnit(id="u2", text="exact memory", authority=Authority.OWNER_LOCKED)
    assert unit.must_preserve is True


def test_atomicity_splits_polished_second_move():
    spans = candidate_semantic_spans("Choices arise from conditions, which raises the question of who chooses.")
    assert len(spans) == 2


def test_atomicity_keeps_simple_compound_predicate():
    spans = candidate_semantic_spans("Choices happen and matter.")
    assert spans == ["Choices happen and matter."]
