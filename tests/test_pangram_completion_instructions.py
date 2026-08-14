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
        assert "terminal states" in text, label
        assert "unresolved authorial handoff" in text, label
        assert "operational suspension" in text, label
        assert "seventh paid POST" in text, label
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
    assert "when pangram success is an explicit delivery requirement" not in combined.lower()

    operating = texts["operating guide"]
    assert "Hard limit: at most 6 new paid Pangram POSTs per section per audit" in operating
    assert "never overrides the six-paid-call section cap" in operating


# Regression for the source-vs-rendered representation failure discovered on Spiritual Bypassing.
def test_pangram_certification_uses_reader_visible_text_not_raw_markdown():
    texts = {
        "operating guide": OPERATING_GUIDE.read_text(encoding="utf-8"),
        "actions runbook": RUNBOOK.read_text(encoding="utf-8"),
        "humanization gate": HUMANIZATION_GATE.read_text(encoding="utf-8"),
        "lesson index": LESSON_INDEX.read_text(encoding="utf-8"),
    }
    for label, text in texts.items():
        lowered = text.lower()
        assert "raw markdown" in lowered, label
        assert "visible plaintext" in lowered, label
        assert "diagnostic only" in lowered, label
        assert "reader-visible" in lowered, label


# Regression for detector-window tunnel vision: a Pangram-green passage can still have broken article architecture.
def test_humanization_rechecks_global_architecture_after_detector_edits():
    texts = {
        "operating guide": OPERATING_GUIDE.read_text(encoding="utf-8"),
        "humanization gate": HUMANIZATION_GATE.read_text(encoding="utf-8"),
        "lesson index": LESSON_INDEX.read_text(encoding="utf-8"),
    }
    for label, text in texts.items():
        lowered = text.lower()
        assert "architecture regression" in lowered, label
        assert "after every detector-driven edit" in lowered, label
        assert "heading promise" in lowered, label
        assert "paragraph jobs" in lowered, label
        assert "live question" in lowered, label
        assert "article-wide" in lowered, label
        assert "owner realization" in lowered, label
        assert "100% human" in lowered, label
