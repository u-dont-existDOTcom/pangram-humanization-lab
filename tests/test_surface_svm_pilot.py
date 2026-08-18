from pathlib import Path

import pytest

from pangram_lab import surface_svm_pilot as sp


def test_select_largest_documents_is_deterministic_and_author_scoped():
    rows = [
        {"speaker": "A", "sample_id": "small", "source_group": "g1", "word_count": 100},
        {"speaker": "A", "sample_id": "large", "source_group": "g2", "word_count": 500},
        {"speaker": "A", "sample_id": "mid", "source_group": "g3", "word_count": 300},
        {"speaker": "B", "sample_id": "other", "source_group": "g4", "word_count": 1000},
    ]
    selected = sp.select_largest_documents(rows, "A", 2)
    assert [row["sample_id"] for row in selected] == ["large", "mid"]


def test_matched_test_keeps_only_groups_with_two_or_more_authors():
    rows = [
        {"source_group": "shared", "speaker": "A", "sample_id": "a"},
        {"source_group": "shared", "speaker": "B", "sample_id": "b"},
        {"source_group": "solo", "speaker": "A", "sample_id": "c"},
    ]
    selected = sp.select_matched_test(rows)
    assert {row["sample_id"] for row in selected} == {"a", "b"}


def test_source_group_leakage_is_rejected():
    with pytest.raises(ValueError, match="source_group leakage"):
        sp.assert_no_source_group_leakage(
            [{"source_group": "same"}],
            [{"source_group": "same"}],
        )


def test_group_bootstrap_is_deterministic():
    rows = [
        {"source_group": "g1", "actual": "A", "predicted": "A"},
        {"source_group": "g1", "actual": "B", "predicted": "A"},
        {"source_group": "g2", "actual": "A", "predicted": "A"},
    ]
    a = sp.group_bootstrap_accuracy(rows, iterations=100, seed=7)
    b = sp.group_bootstrap_accuracy(rows, iterations=100, seed=7)
    assert a == b
    assert a["groups"] == 2
    assert 0 <= a["p2_5"] <= a["p97_5"] <= 1


def test_surface_svm_smoke_if_optional_dependency_present(tmp_path):
    pytest.importorskip("sklearn")
    authors = ["A", "B", "C"]
    train = []
    test = []
    vocabulary = {
        "A": "apple orchard cider fruit",
        "B": "engine piston gearbox motor",
        "C": "meditation dharma awareness mind",
    }
    for author in authors:
        for idx in range(2):
            path = tmp_path / f"train-{author}-{idx}.txt"
            path.write_text((vocabulary[author] + " ") * 20, encoding="utf-8")
            train.append(
                {
                    "speaker": author,
                    "sample_id": f"train-{author}-{idx}",
                    "source_group": f"train-{author}-{idx}",
                    "local_text_path": str(path),
                }
            )
        path = tmp_path / f"test-{author}.txt"
        path.write_text((vocabulary[author] + " ") * 10, encoding="utf-8")
        test.append(
            {
                "speaker": author,
                "sample_id": f"test-{author}",
                "source_group": "heldout",
                "local_text_path": str(path),
            }
        )
    result = sp.fit_and_evaluate(
        train,
        test,
        authors=authors,
        feature_mode="char+word",
        bootstrap_iterations=20,
        bootstrap_seed=1,
    )
    assert result["accuracy"] == 1.0
    assert result["macro_f1"] == 1.0
