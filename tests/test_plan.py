import pytest
from pangram_lab.plan import validate_plan


def base_plan():
    return {
      "status":"planned","summary":"x","owner_question":"","objective":"o",
      "factors":[{"id":"A","name":"A","description":"d","level0":"a0","level1":"a1"}],
      "probes":[
        {"id":"AI_ENDPOINT","text":"ai","provenance":"endpoint","controlled_variable":"control","semantic_fidelity_note":"exact","synthetic":False,"assignments":[]},
        {"id":"HUMAN_ENDPOINT","text":"human","provenance":"endpoint","controlled_variable":"control","semantic_fidelity_note":"exact","synthetic":False,"assignments":[]},
        {"id":"P0","text":"x","provenance":"s","controlled_variable":"A","semantic_fidelity_note":"same meaning","synthetic":True,"assignments":[{"factor_id":"A","level":0}]},
        {"id":"P1","text":"y","provenance":"s","controlled_variable":"A","semantic_fidelity_note":"same meaning","synthetic":True,"assignments":[{"factor_id":"A","level":1}]}
      ],
      "contrasts":[{"id":"C1","label":"A edge","left_probe":"P0","right_probe":"P1","interpretive_question":"q","repeat_eligible":True}],
      "repeat_threshold":0.03,"blind_editorial_judgments":["human preferred"],"stop_rule":"stop","why_high_information":"why"
    }


def test_plan_uses_assignments_not_factor_bits_and_validates_refs():
    p=base_plan(); validate_plan(p,"ai","human")


def test_unknown_contrast_probe_is_rejected():
    p=base_plan(); p["contrasts"][0]["right_probe"]="mean[(P0-P1)]"
    with pytest.raises(ValueError,match="unknown probe"):
        validate_plan(p,"ai","human")


def test_endpoint_text_must_be_exact():
    p=base_plan(); p["probes"][0]["text"]="changed"
    with pytest.raises(ValueError,match="AI_ENDPOINT"):
        validate_plan(p,"ai","human")
