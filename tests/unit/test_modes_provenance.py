from authorial_flow.modes import TaskMode, choose_mode
from authorial_flow.source_provenance import SourceProvenance, classify_provenance


def test_explicit_p2s_disables_research_and_substantive_change():
    d=choose_mode('P2S',SourceProvenance.AI_FROM_OWNER_INPUTS,semantic_sanity=True)
    assert d.mode is TaskMode.P2S
    assert d.research_permission is False
    assert d.substantive_permission is False


def test_plain_humanize_ai_draft_can_choose_p3():
    d=choose_mode('humanize',SourceProvenance.AI_FROM_OWNER_INPUTS,semantic_sanity=True)
    assert d.mode in {TaskMode.P2S,TaskMode.P3}
    assert d.reason


def test_plain_humanize_ai_draft_with_thought_repair_chooses_p3():
    d=choose_mode('humanize',SourceProvenance.AI_FROM_OWNER_INPUTS,semantic_sanity=False)
    assert d.mode is TaskMode.P3
    assert d.substantive_permission is True


def test_owner_final_does_not_auto_escalate_without_defect():
    d=choose_mode('humanize',SourceProvenance.OWNER_FINAL,semantic_sanity=True)
    assert d.mode in {TaskMode.P1,TaskMode.P2,TaskMode.P2S}


def test_source_pool_humanize_routes_p4():
    assert choose_mode('humanize',SourceProvenance.SOURCE_POOL,semantic_sanity=True).mode is TaskMode.P4


def test_provenance_override_is_deterministic():
    result=classify_provenance('whatever',metadata={'provenance_override':'AI_FROM_OWNER_INPUTS'})
    assert result.provenance is SourceProvenance.AI_FROM_OWNER_INPUTS
