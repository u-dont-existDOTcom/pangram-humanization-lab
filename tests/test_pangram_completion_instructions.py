from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPERATING_GUIDE = ROOT / "docs" / "CHATGPT-OPERATING-GUIDE.md"
RUNBOOK = ROOT / "docs" / "PANGRAM-ACTIONS-RUNBOOK.md"
ARCHITECTURE_GATE = ROOT / "docs" / "HUMANIZATION-ARCHITECTURE-REGRESSION.md"
HUMANIZATION_GATE = ROOT / "state" / "WORKING-LESSONS-SUPPLEMENT-2026-08-13-HUMANIZATION-GATE.md"
LESSON_INDEX = ROOT / "state" / "LESSON-INDEX.md"


TRIGGER = (
    "Whenever Joel asks to humanize text, make it pass Pangram, or otherwise makes "
    "Pangram success a delivery requirement, this gate applies."
)
FINAL_ARTICLE_ACCEPTANCE = "section-level 100% results do not aggregate into an article pass."
OCT20_POLICY = ROOT / "state" / "OWNER-PANGRAM-PRODUCTION-BUDGET-CORRECTION-20261020.md"
JOEL_GUIDANCE = ROOT / "AGENTS.md"

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
        # Owner correction (2026-10-20): an edit invalidates old certification
        # but does not authorize repeated whole-article tests during editing.
        assert FINAL_ARTICLE_ACCEPTANCE in text.lower(), label
        assert "after every accepted edit" not in text.lower(), label
        assert ("final readiness" in text.lower() or "finally ready" in text.lower()), label
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
    assert (
        "Historical hard upper limit: at most 6 new paid Pangram POSTs per genuine local repair section per audit"
        in operating
    )
    assert "a stricter direct owner production policy is now active" in operating
    assert "at most one localized final retest" in operating
    assert (
        "multi-section aggregate certification boundaries remain fully accounted but are not subject to the six-call section cap"
        in operating
    )
    assert "never overrides the six-paid-call local-section cap" in operating
    assert "A whole-article acceptance boundary counts as its own section" not in operating


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
        "architecture gate": ARCHITECTURE_GATE.read_text(encoding="utf-8"),
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


def test_oct20_owner_call_budget_and_human_tell_escalation_are_loaded():
    policy = OCT20_POLICY.read_text(encoding="utf-8")
    operating = OPERATING_GUIDE.read_text(encoding="utf-8")
    agents = JOEL_GUIDANCE.read_text(encoding="utf-8")
    index = LESSON_INDEX.read_text(encoding="utf-8")

    # Verify the new owner correction is reachable at routine execution entrypoints,
    # not merely preserved in an unused archival incident note.
    for label, text in {
        "operating guide": operating,
        "agents": agents,
        "lesson index": index,
    }.items():
        assert "OWNER-PANGRAM-PRODUCTION-BUDGET-CORRECTION-20261020.md" in text, label

    assert "two new paid/credit-consuming submissions total per paragraph" in policy
    assert "Two prediction misses" in policy
    assert "one natural section or about five paragraphs" in policy
    assert "at most one substantial targeted section retest" in policy
    assert "once at final readiness" in policy
    assert "I can't find AI tells here" in policy
    assert "the positive Human tells" in policy
    assert "New strategy, new task ID" in policy
    assert "no live provider call is authorized" in policy.lower()
    assert "after every accepted edit" not in operating.lower()
    assert "at most one localized final retest" in operating
