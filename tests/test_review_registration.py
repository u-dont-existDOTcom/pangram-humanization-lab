import json
from pathlib import Path

from pangram_lab.review_registration import register_result


def test_result_registration_keeps_tested_text_out_of_review_state(tmp_path: Path):
    out = tmp_path / "state" / "experiments" / "result.json"
    out.parent.mkdir(parents=True)
    result = {
        "experiment_id": "exp",
        "audit_id": "audit",
        "results": [
            {"id": "A", "section_id": "opening", "text": "PRIVATE TESTED PASSAGE", "detector": {"prediction_short": "Mixed", "fraction_human": 0.8, "fraction_ai": 0.2, "fraction_ai_assisted": 0.0}},
            {"id": "B", "section_id": "opening", "text": "ANOTHER PRIVATE PASSAGE", "detector": {"prediction_short": "Human", "fraction_human": 0.95, "fraction_ai": 0.05, "fraction_ai_assisted": 0.0}},
        ],
    }
    out.write_text(json.dumps(result), encoding="utf-8")
    entry = register_result(tmp_path, out, "evidence-branch", result)
    assert entry["experiment_id"] == "exp"
    assert entry["audit_id"] == "audit"
    assert entry["sections"] == ["opening"]
    assert [v["prediction_short"] for v in entry["variants"]] == ["Mixed", "Human"]
    raw = (tmp_path / "state" / "LESSON-INBOX.json").read_text(encoding="utf-8")
    assert "PRIVATE TESTED PASSAGE" not in raw
    assert "ANOTHER PRIVATE PASSAGE" not in raw
