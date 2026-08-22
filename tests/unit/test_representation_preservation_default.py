from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "src" / "authorial_flow" / "prompts"


def test_representation_prompt_preserves_explicit_source_choice_before_owner_interrupt() -> None:
    text = (PROMPTS / "represent.md").read_text(encoding="utf-8")
    assert "explicit owner-supplied or higher-authority source choice is the default realization" in text
    assert "do not ask whether to remove, rename, reorder, or replace an existing owner-supplied choice" in text
    assert "Optional stylistic improvements, hypothetical alternatives" in text


def test_semantic_sanity_does_not_escalate_hypothetical_edit_to_owner() -> None:
    text = (PROMPTS / "semantic_sanity.md").read_text(encoding="utf-8")
    assert "not authorial ambiguity merely because" in text
    assert "preserve that choice for preservation-oriented work" in text
    assert "Do not escalate hypothetical renaming, deletion, reordering, or stylistic alternatives to OWNER" in text
