import pytest

from pangram_lab import surface_svm_matched_cv as cv


def test_aggregate_predictions_reports_per_author_and_group_bootstrap():
    pytest.importorskip("sklearn")
    authors = ["A", "B", "C"]
    predictions = [
        {"source_group": "g1", "actual": "A", "predicted": "A"},
        {"source_group": "g1", "actual": "B", "predicted": "B"},
        {"source_group": "g2", "actual": "A", "predicted": "B"},
        {"source_group": "g2", "actual": "C", "predicted": "C"},
    ]
    result = cv._aggregate_predictions(predictions, authors, iterations=100, seed=3)
    assert result["accuracy"] == 0.75
    assert result["per_author"]["A"]["accuracy"] == 0.5
    assert result["per_author"]["B"]["accuracy"] == 1.0
    assert result["per_author"]["C"]["accuracy"] == 1.0
    assert result["group_bootstrap_accuracy_95pct"]["groups"] == 2


def test_metadata_row_never_contains_local_text_path():
    row = {
        "sample_id": "x",
        "source_group": "g",
        "speaker": "A",
        "word_count": 12,
        "canonical_sha256": "abc",
        "local_text_path": "/private/text.txt",
    }
    result = cv._metadata_row(row)
    assert result == {
        "sample_id": "x",
        "source_group": "g",
        "speaker": "A",
        "word_count": 12,
        "canonical_sha256": "abc",
    }
