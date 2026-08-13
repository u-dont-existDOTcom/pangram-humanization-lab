from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPERATING_GUIDE = ROOT / "docs" / "CHATGPT-OPERATING-GUIDE.md"
RUNBOOK = ROOT / "docs" / "PANGRAM-ACTIONS-RUNBOOK.md"
HUMANIZATION_GATE = ROOT / "state" / "WORKING-LESSONS-SUPPLEMENT-2026-08-13-HUMANIZATION-GATE.md"
LESSON_INDEX = ROOT / "state" / "LESSON-INDEX.md"


TRIGGER = (
    "Whenever Joel asks to humanize text, make it pass Pangram, or otherwise makes "
    "Pangram success a delivery requirement, this gate applies."
)
TWO_TERMINAL_STATES = "The repair task has only two terminal states:"
KNOWN_REPAIR_CONTINUES = (
    "While a known faithful and coherent repair remains, continue the task."
)
FULL_ARTICLE_RETEST = (
    "For a full article, the complete exact article boundary must itself satisfy the "
    "gate after every accepted edit; section-level 100% results do not aggregate into "
    "an article pass."
)
EDITORIAL_GATE = (
    "A 100% Human result with semantic, rhetorical, editorial, fidelity, or provenance "
    "loss also fails the gate."
)


def test_joel_pangram_completion_requires_exact_100_percent_and_handoff():
    texts = {
        "operating guide": OPERATING_GUIDE.read_text(encoding="utf-8"),
        "actions runbook": RUNBOOK.read_text(encoding="utf-8"),
        "humanization gate": HUMANIZATION_GATE.read_text(encoding="utf-8"),
        "lesson index": LESSON_INDEX.read_text(encoding="utf-8"),
    }
    for label, text in texts.items():
        assert TRIGGER in text, label
        assert "the exact intended delivery boundary" in text, label
        assert 'detector.stage == "STAGE_SUCCESS"' in text, label
        assert 'detector.version == "4.0"' in text, label
        assert "fraction_human == 1.0" in text, label
        assert "fraction_ai == 0.0" in text, label
        assert "fraction_ai_assisted == 0.0" in text, label
        assert "93%" in text, label
        assert "is not a pass" in text, label
        assert TWO_TERMINAL_STATES in text, label
        assert KNOWN_REPAIR_CONTINUES in text, label
        assert "unresolved authorial handoff" in text, label
        assert "Section/window measurements are diagnostic" in text, label
        assert FULL_ARTICLE_RETEST in text, label
        assert EDITORIAL_GATE in text, label
        assert "`text_sha256`" in text, label
        assert "`fraction_human`, `fraction_ai`, and `fraction_ai_assisted`" in text, label
        assert "result path" in text, label
        assert "result commit" in text, label

    combined = "\n".join(texts.values())
    assert "result hash" not in combined
    assert "score and result hash" not in combined
    assert "may pause paid calls" not in combined
    assert "section/API-call budget" not in combined
    assert "when pangram success is an explicit delivery requirement" not in combined.lower()

    assert (
        "For controlled research probes, stop once the local hypothesis is adequately "
        "discriminated; avoid token hunting. This research stopping rule never ends "
        "requested humanization repair before one of the two terminal states above."
        in texts["operating guide"]
    )
