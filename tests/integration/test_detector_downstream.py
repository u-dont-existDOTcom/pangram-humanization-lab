from dataclasses import replace

from authorial_flow.candidates import CandidateRecord, freeze_editorial_winner
from authorial_flow.nodes.detector_search import detector_node, choose_presentation
from authorial_flow.models.pangram import PangramResult


class RaisingPangram:
    def evaluate(self, *args, **kwargs):
        raise AssertionError("Pangram must not be called")


class HumanPangram:
    def __init__(self): self.calls=[]
    def evaluate(self, text, candidate_hash, pending=None):
        self.calls.append(text)
        return PangramResult("STAGE_SUCCESS","4.0","Human",0,0,(),{},True)


def test_pangram_skipped_when_local_gates_fail():
    c=freeze_editorial_winner([CandidateRecord(id="a",text="x",editorial_score=9,hard_pass=False,lineage_id="L0")])
    out=detector_node(c,RaisingPangram())
    assert out.status == "SKIPPED_LOCAL_FAILURE"


def test_weaker_human_variant_does_not_replace_editorial_winner():
    parent=freeze_editorial_winner([CandidateRecord(id="a",text="editorial winner",editorial_score=9,hard_pass=True,lineage_id="L0")])
    weaker=CandidateRecord(id="b",text="weaker human",editorial_score=7,hard_pass=True,lineage_id="L0",parent_id="a",pangram={"prediction_short":"Human"})
    assert choose_presentation(parent,[weaker]).recommended.id == "a"


def test_semantic_delta_variant_is_rejected_before_pangram():
    parent=freeze_editorial_winner([CandidateRecord(id="a",text="Choices matter.",editorial_score=9,hard_pass=True,lineage_id="L0")])
    variant=CandidateRecord(id="b",text="Choices do not matter.",editorial_score=9,hard_pass=True,lineage_id="L0",parent_id="a",meaning_equivalent=False)
    client=RaisingPangram()
    out=detector_node(variant,client,parent=parent)
    assert out.status == "REJECTED_SEMANTIC_DELTA"


def test_first_human_child_freezes_and_later_human_cannot_replace_it():
    parent=freeze_editorial_winner([CandidateRecord(id="a",text="parent",editorial_score=9,hard_pass=True,lineage_id="L0")])
    client=HumanPangram()
    first=CandidateRecord(id="b",text="first",editorial_score=9,hard_pass=True,lineage_id="L0",parent_id="a",meaning_equivalent=True)
    r1=detector_node(first,client,parent=parent)
    later=CandidateRecord(id="c",text="later",editorial_score=9.1,hard_pass=True,lineage_id="L0",parent_id="a",meaning_equivalent=True)
    r2=detector_node(later,client,parent=parent,lineage=r1.lineage)
    assert r1.lineage.first_human_id == "b"
    assert r2.lineage.first_human_id == "b"
