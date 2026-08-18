import pytest

from pangram_lab import joel_legacy_profile as jp


def test_after_first_label_drops_question_and_keeps_answer():
    text = "Question: Someone else's question.\nMore question.\nAnswer: Joel starts here.\nJoel continues."
    assert jp.apply_cleanup_rule(text, "after-first-label:Answer") == (
        "Joel starts here.\nJoel continues."
    )


def test_before_first_label_drops_external_snippet_and_everything_after():
    text = "Joel paragraph one.\nJoel paragraph two.\nAnd here's a useful snippet I snagged: external text\nMore external text."
    assert jp.apply_cleanup_rule(
        text,
        "before-first-label:And here's a useful snippet I snagged",
    ) == "Joel paragraph one.\nJoel paragraph two."


def test_cleanup_marker_absence_fails_closed():
    with pytest.raises(ValueError, match="cleanup marker not found"):
        jp.apply_cleanup_rule("Owner prose only.", "after-first-label:Answer")


def test_whole_rule_is_identity_except_outer_whitespace():
    assert jp.apply_cleanup_rule(
        "\nOwner prose.\n",
        "whole-after-existing-blockquote-drop",
    ) == "Owner prose."
