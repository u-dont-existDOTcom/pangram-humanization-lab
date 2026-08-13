from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPERATING_GUIDE = ROOT / "docs" / "CHATGPT-OPERATING-GUIDE.md"
RUNBOOK = ROOT / "docs" / "PANGRAM-ACTIONS-RUNBOOK.md"
HUMANIZATION_GATE = ROOT / "state" / "WORKING-LESSONS-SUPPLEMENT-2026-08-13-HUMANIZATION-GATE.md"


def test_joel_pangram_completion_requires_exact_100_percent_and_handoff():
    texts = {
        "operating guide": OPERATING_GUIDE.read_text(encoding="utf-8"),
        "actions runbook": RUNBOOK.read_text(encoding="utf-8"),
        "humanization gate": HUMANIZATION_GATE.read_text(encoding="utf-8"),
    }
    for label, text in texts.items():
        assert "fraction_human == 1.0" in text, label
        assert "fraction_ai == 0.0" in text, label
        assert "fraction_ai_assisted == 0.0" in text, label

    assert "93%" in texts["operating guide"]
    assert "unresolved authorial handoff" in texts["operating guide"]
    assert "93%" in texts["humanization gate"]
    assert "unresolved authorial handoff" in texts["humanization gate"]
    assert "93%" in texts["actions runbook"]
    assert "unresolved authorial handoff" in texts["actions runbook"]
