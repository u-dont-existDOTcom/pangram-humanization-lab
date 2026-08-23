import pytest

from authorial_flow.runtime import (
    _actionable_developmental_ambiguity,
    runtime_schema_inventory,
)


def test_developmental_schema_requires_actionable_ambiguity_fields() -> None:
    item = runtime_schema_inventory()["developmental"]["properties"]["unresolved_authorial"]["items"]

    assert item["type"] == "object"
    assert item["additionalProperties"] is False
    assert set(item["required"]) == {
        "unit_id", "question", "interpretations", "material_consequence",
    }


def test_actionable_developmental_ambiguity_preserves_options_and_consequence() -> None:
    unit_id, question = _actionable_developmental_ambiguity({
        "unit_id": "u7",
        "question": "Does the passage mean regulation or suppression?",
        "interpretations": [
            "The body settles while feeling remains available.",
            "The feeling is pushed out of awareness.",
        ],
        "material_consequence": (
            "The recommendation changes from allowing sensation to avoiding it."
        ),
    })

    assert unit_id == "u7"
    assert "regulation or suppression" in question
    assert "Option 1: The body settles while feeling remains available." in question
    assert "Option 2: The feeling is pushed out of awareness." in question
    assert "Why it matters: The recommendation changes" in question


@pytest.mark.parametrize(
    "payload",
    [
        {
            "unit_id": "",
            "question": "Which meaning?",
            "interpretations": ["A", "B"],
            "material_consequence": "The claim changes.",
        },
        {
            "unit_id": "u7",
            "question": "Which meaning?",
            "interpretations": ["Only one meaning."],
            "material_consequence": "The claim changes.",
        },
        {
            "unit_id": "u7",
            "question": "Which meaning?",
            "interpretations": ["A", "B"],
            "material_consequence": "",
        },
    ],
)
def test_non_actionable_developmental_ambiguity_fails_as_machine_contract(payload) -> None:
    with pytest.raises(ValueError, match="not actionable"):
        _actionable_developmental_ambiguity(payload)
