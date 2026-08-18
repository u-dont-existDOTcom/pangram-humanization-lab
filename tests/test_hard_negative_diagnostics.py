import json
from pathlib import Path

import pytest

from pangram_lab import hard_negative_diagnostics as hnd


def _spec(*, ordinary_authors=("David Vardy", "Greg Goode")):
    authors = [
        {
            "author": "Joel Rosenblum",
            "role": "target-author",
            "status": "active",
        },
        {
            "author": "Stian Gudmundsen Høiland",
            "role": "owner-identified-hard-negative",
            "status": "active",
        },
    ]
    authors.extend(
        {
            "author": author,
            "role": "ordinary-matched-control",
            "status": "active",
        }
        for author in ordinary_authors
    )
    return {
        "schema_version": 1,
        "active_authors": authors,
        "minimum_evidence": {
            "ordinary_matched_controls_before_rewrite_degradation_claim": 2,
            "minimum_target_holdout_documents": 2,
            "minimum_hard_negative_holdout_documents": 1,
        },
        "forbidden_claims": ["hard-negative confusion proves erasure"],
    }


def _row(sample, actual, joel, stian, david, greg):
    return {
        "sample_id": sample,
        "source_group": f"group-{sample}",
        "actual": actual,
        "cosine_scores": {
            "Joel Rosenblum": joel,
            "Stian Gudmundsen Høiland": stian,
            "David Vardy": david,
            "Greg Goode": greg,
        },
    }


def _rows():
    return [
        # Full set chooses the hard negative, but ordinary-controls-only chooses Joel.
        _row("j1", "Joel Rosenblum", 0.80, 0.82, 0.50, 0.40),
        _row("j2", "Joel Rosenblum", 0.75, 0.74, 0.70, 0.68),
        _row("s1", "Stian Gudmundsen Høiland", 0.79, 0.80, 0.50, 0.40),
        _row("d1", "David Vardy", 0.50, 0.45, 0.90, 0.40),
        _row("g1", "Greg Goode", 0.50, 0.45, 0.40, 0.90),
    ]


def test_hard_negative_and_ordinary_control_results_are_separate():
    result = hnd.analyze_condition(_rows(), _spec())

    full = result["full_active_candidate_set"]
    hard = result["target_vs_hard_negatives"]["Stian Gudmundsen Høiland"]
    ordinary = result["target_vs_ordinary_controls"]
    sensitivity = result["without_hard_negative_sensitivity"]

    assert full["accuracy"] == 0.8
    assert full["target_accuracy"] == 0.5
    assert hard["accuracy"] == 0.666667
    assert hard["target_accuracy"] == 0.5
    assert ordinary["accuracy"] == 1.0
    assert ordinary["target_accuracy"] == 1.0
    assert sensitivity["accuracy"] == 1.0
    assert sensitivity["may_not_be_headline_result"] is True

    assert result["direct_full_set_confusions"] == {
        "target_to_hard_negative": {"Stian Gudmundsen Høiland": 1},
        "hard_negative_to_target": {},
    }
    assert result["rewrite_degradation_interpretation_ready"] is True


def test_target_margin_rows_show_near_neighbor_and_ordinary_control_margins():
    result = hnd.analyze_condition(_rows(), _spec())
    by_sample = {
        row["sample_id"]: row for row in result["target_document_margins"]
    }

    j1 = by_sample["j1"]
    assert j1["target_rank"] == 2
    assert j1["full_candidate_set_winner"] == "Stian Gudmundsen Høiland"
    assert j1["target_minus_best_ordinary_control_margin"] == 0.3
    assert j1["target_vs_ordinary_controls_restricted_winner"] == "Joel Rosenblum"
    assert j1["hard_negative_comparisons"] == [
        {
            "author": "Stian Gudmundsen Høiland",
            "score": 0.82,
            "target_minus_hard_negative_margin": -0.02,
            "restricted_winner": "Stian Gudmundsen Høiland",
        }
    ]


def test_one_ordinary_control_keeps_diagnostic_but_blocks_rewrite_interpretation():
    spec = _spec(ordinary_authors=("David Vardy",))
    rows = []
    for row in _rows():
        row = dict(row)
        row["cosine_scores"] = dict(row["cosine_scores"])
        row["cosine_scores"].pop("Greg Goode")
        if row["actual"] != "Greg Goode":
            rows.append(row)

    result = hnd.analyze_condition(rows, spec)
    assert result["rewrite_degradation_interpretation_ready"] is False
    assert any("only 1 active ordinary matched control" in blocker for blocker in result["readiness_blockers"])


def test_bundle_output_is_metadata_only_and_repeatable(tmp_path: Path):
    spec = _spec()
    bundle = {"schema_version": 1, "conditions": {"whole": _rows()}}

    first = hnd.analyze_prediction_bundle(bundle, spec)
    second = hnd.analyze_prediction_bundle(bundle, spec)
    assert first == second
    assert first["status"] == "hard-negative-stratified-diagnostic-not-IER-not-calibrated"
    assert first["raw_or_canonical_prose_in_output"] is False

    spec_path = tmp_path / "spec.json"
    input_path = tmp_path / "input.json"
    out_path = tmp_path / "out.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    input_path.write_text(json.dumps(bundle), encoding="utf-8")
    hnd.run(spec_path, input_path, out_path=out_path)

    encoded = out_path.read_text(encoding="utf-8")
    assert "local_text_path" not in encoded
    assert "raw_text" not in encoded
    assert "canonical_text" not in encoded
    assert "embedding" not in encoded


def test_missing_active_author_score_fails_closed():
    row = _rows()[0]
    row = dict(row)
    row["cosine_scores"] = dict(row["cosine_scores"])
    row["cosine_scores"].pop("Greg Goode")
    with pytest.raises(hnd.HardNegativeDiagnosticError, match="missing scores"):
        hnd.analyze_condition([row], _spec())


def test_prediction_bundle_rejects_prose_or_local_paths():
    bundle = {
        "conditions": {
            "whole": [
                {
                    **_rows()[0],
                    "local_text_path": "/private/corpus/j1.txt",
                }
            ]
        }
    }
    with pytest.raises(hnd.HardNegativeDiagnosticError, match="forbidden"):
        hnd._assert_metadata_only(bundle)
