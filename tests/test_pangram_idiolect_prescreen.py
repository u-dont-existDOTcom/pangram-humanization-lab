import json
from pathlib import Path

from pangram_lab.pangram_idiolect_prescreen import calibrate


def test_pilot_excludes_short_boundaries_and_fails_closed(tmp_path: Path):
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    (profile_dir / "p1.txt").write_text(("I think this is ordinary human writing. " * 80), encoding="utf-8")
    (profile_dir / "p2.txt").write_text(("But I still want to ask what happens next. " * 80), encoding="utf-8")
    (profile_dir / "p3.txt").write_text(("You can disagree with me and that's fine. " * 80), encoding="utf-8")

    results = {
        "human-a": {
            "stage": "STAGE_SUCCESS",
            "prediction_short": "Human",
            "fraction_ai": 0.0,
            "text": "I think this is ordinary human writing and I still want to ask what happens next. " * 5,
        },
        "ai-a": {
            "stage": "STAGE_SUCCESS",
            "prediction_short": "AI",
            "fraction_ai": 1.0,
            "text": "Consequently the framework provides a comprehensive synthesis of all relevant considerations. " * 7,
        },
    }
    results_path = tmp_path / "results.json"
    results_path.write_text(json.dumps(results), encoding="utf-8")

    spec = {
        "schema_version": 1,
        "purpose": "test",
        "profile": {"provenance": "natural-owner-confirmed", "register": "relationship"},
        "cached_case": {"group_id": "g1", "results_path": str(results_path), "evidence_class": "cache"},
        "recorded_examples": [
            {
                "id": "human-b",
                "group_id": "g2",
                "pangram_label": "Human",
                "evidence_class": "recorded",
                "text": "But I still want to ask what happens next because there is another ordinary thing here. " * 5,
            },
            {
                "id": "ai-b",
                "group_id": "g2",
                "pangram_label": "NonHuman",
                "evidence_class": "recorded",
                "text": "Moreover this integrated conceptual architecture systematically resolves the underlying tension. " * 7,
            },
            {
                "id": "short",
                "group_id": "g3",
                "pangram_label": "Human",
                "evidence_class": "recorded",
                "text": "This is short and descriptive only.",
            },
        ],
        "evaluation": {
            "candidate_rule_family": "two-threshold",
            "validation_minimums": {
                "independent_groups": 5,
                "examples": 30,
                "nonhuman_examples": 10,
                "heldout_false_safe_count": 0,
                "heldout_safe_coverage_minimum": 0.5,
            },
        },
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    out = tmp_path / "out.json"
    result = calibrate(spec_path, profile_dir, out)

    assert result["status"] == "pilot-not-validated"
    assert result["validation"]["substitution_validated"] is False
    assert result["dataset"]["short_descriptive_only_count"] == 1
    assert result["dataset"]["eligible_50plus_count"] == 4
    assert "text" not in json.dumps(result)
    assert out.exists()


def test_result_never_persists_profile_prose(tmp_path: Path):
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    secret = "unique private profile phrase"
    (profile_dir / "p1.txt").write_text((secret + " ordinary words. ") * 100, encoding="utf-8")
    results_path = tmp_path / "results.json"
    results_path.write_text(json.dumps({
        "a": {"stage": "STAGE_SUCCESS", "prediction_short": "Human", "fraction_ai": 0.0, "text": "ordinary words " * 60}
    }), encoding="utf-8")
    spec = {
        "schema_version": 1,
        "purpose": "privacy test",
        "profile": {"provenance": "natural-owner-confirmed", "register": "relationship"},
        "cached_case": {"group_id": "g", "results_path": str(results_path), "evidence_class": "cache"},
        "recorded_examples": [],
        "evaluation": {
            "candidate_rule_family": "two-threshold",
            "validation_minimums": {
                "independent_groups": 5, "examples": 30, "nonhuman_examples": 10,
                "heldout_false_safe_count": 0, "heldout_safe_coverage_minimum": 0.5
            },
        },
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    out = tmp_path / "out.json"
    result = calibrate(spec_path, profile_dir, out)
    assert secret not in json.dumps(result)
    assert secret not in out.read_text(encoding="utf-8")
