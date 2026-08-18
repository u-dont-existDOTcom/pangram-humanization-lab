import json
from pathlib import Path

import pytest

from pangram_lab import dharma_logo_svm as logo


def test_logo_folds_hold_out_each_group_once_without_leakage():
    authors = ["A", "B", "C"]
    rows = [
        {"source_group": "g1", "speaker": "A", "sample_id": "g1-a"},
        {"source_group": "g1", "speaker": "B", "sample_id": "g1-b"},
        {"source_group": "g2", "speaker": "A", "sample_id": "g2-a"},
        {"source_group": "g2", "speaker": "C", "sample_id": "g2-c"},
        {"source_group": "g3", "speaker": "A", "sample_id": "g3-a"},
        {"source_group": "g3", "speaker": "B", "sample_id": "g3-b"},
        {"source_group": "g3", "speaker": "C", "sample_id": "g3-c"},
    ]
    folds = logo.build_leave_one_group_out_folds(rows, authors=authors)
    assert [fold["held_out_source_group"] for fold in folds] == ["g1", "g2", "g3"]
    for fold in folds:
        held = fold["held_out_source_group"]
        assert {row["source_group"] for row in fold["test_rows"]} == {held}
        assert held not in {row["source_group"] for row in fold["train_rows"]}
        assert {row["speaker"] for row in fold["train_rows"]} == set(authors)


def test_logo_rejects_fold_that_removes_only_training_text_for_author():
    rows = [
        {"source_group": "g1", "speaker": "A", "sample_id": "g1-a"},
        {"source_group": "g1", "speaker": "B", "sample_id": "g1-b"},
        {"source_group": "g2", "speaker": "A", "sample_id": "g2-a"},
        {"source_group": "g2", "speaker": "C", "sample_id": "g2-c"},
    ]
    with pytest.raises(ValueError, match="leaves authors without training text"):
        logo.build_leave_one_group_out_folds(rows, authors=["A", "B", "C"])


def test_logo_smoke_if_optional_dependency_present(tmp_path: Path):
    pytest.importorskip("sklearn")
    authors = ["A", "B", "C"]
    vocab = {
        "A": "apple orchard cider fruit",
        "B": "engine piston gearbox motor",
        "C": "meditation dharma awareness mind",
    }
    rows = []
    for group_idx in range(4):
        group = f"g{group_idx + 1}"
        for author in authors:
            path = tmp_path / f"{group}-{author}.txt"
            path.write_text(((vocab[author] + " ") * (18 + group_idx)).strip() + "\n", encoding="utf-8")
            rows.append(
                {
                    "sample_id": f"{group}-{author}",
                    "source_group": group,
                    "speaker": author,
                    "word_count": 4 * (18 + group_idx),
                    "canonical_sha256": f"sha-{group}-{author}",
                    "local_text_path": str(path),
                }
            )

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"results": rows, "errors": []}), encoding="utf-8")
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps(
            {
                "instrument_id": "test-logo",
                "authors": authors,
                "selection": {
                    "min_authors_per_group": 2,
                    "expected_documents": 12,
                    "expected_source_groups": 4,
                },
                "evaluation": {
                    "group_bootstrap_accuracy": {"iterations": 50, "seed": 7}
                },
                "interpretation": {"chance_accuracy": 1 / 3, "guardrails": []},
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "receipt.json"
    receipt = logo.run_logo_pilot(manifest, spec, out)
    assert receipt["fold_count"] == 4
    assert receipt["matched_document_count"] == 12
    assert receipt["source_group_leakage"] is False
    for model in receipt["models"].values():
        assert model["accuracy"] == 1.0
        assert len(model["predictions"]) == 12
        assert model["group_bootstrap_accuracy_95pct"]["groups"] == 4
    encoded = out.read_text(encoding="utf-8")
    assert "local_text_path" not in encoded
    assert "canonical_text" not in encoded
