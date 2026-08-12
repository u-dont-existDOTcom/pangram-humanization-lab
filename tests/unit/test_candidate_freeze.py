from dataclasses import FrozenInstanceError
import pytest

from authorial_flow.candidates import (
    CandidateRecord,
    CandidateLineage,
    choose_editorial_winner,
    freeze_editorial_winner,
)


def test_detector_score_cannot_change_editorial_ranking():
    better = CandidateRecord(id="a", text="better", editorial_score=9.0, pangram=None)
    weaker = CandidateRecord(id="b", text="weaker", editorial_score=7.0, pangram={"prediction_short":"Human"})
    assert choose_editorial_winner([weaker, better]).id == "a"


def test_frozen_editorial_winner_is_immutable_and_keeps_lineage():
    c = CandidateRecord(id="a", text="best", editorial_score=9.0, lineage_id="L0")
    frozen = freeze_editorial_winner([c])
    assert frozen.frozen is True
    assert frozen.lineage_id == "L0"
    with pytest.raises(FrozenInstanceError):
        frozen.text = "changed"  # type: ignore[misc]


def test_first_human_lineage_freezes_once():
    lineage = CandidateLineage(root_id="L0")
    lineage = lineage.freeze_first_human("child-1")
    assert lineage.first_human_id == "child-1"
    assert lineage.freeze_first_human("child-2").first_human_id == "child-1"
