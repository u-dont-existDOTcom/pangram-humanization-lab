import json
from pathlib import Path

import numpy as np
import pytest

from pangram_lab import fixed_split_luar as fixed


AUTHORS = [
    "Joel Rosenblum",
    "Stian Gudmundsen Høiland",
    "David Vardy",
    "Greg Goode",
]


def _spec():
    return {
        "schema_version": 1,
        "word_budget_per_document": 150,
        "profile_documents_per_author": 2,
        "holdout_documents_per_author": 1,
        "authors": [
            {
                "speaker": author,
                "role": (
                    "target-author"
                    if author == "Joel Rosenblum"
                    else "owner-identified-hard-negative"
                    if author == "Stian Gudmundsen Høiland"
                    else "ordinary-matched-control"
                ),
                "profile_sample_ids": [f"{author}-p1", f"{author}-p2"],
                "holdout_sample_ids": [f"{author}-h1"],
            }
            for author in AUTHORS
        ],
    }


def test_validate_spec_requires_exact_partition_counts():
    spec = _spec()
    authors = fixed._validate_spec(spec)
    assert set(authors) == set(AUTHORS)

    spec["authors"][0]["profile_sample_ids"].pop()
    with pytest.raises(fixed.FixedSplitLuarError, match="expected 2\+1"):
        fixed._validate_spec(spec)


def test_verify_selected_rows_assigns_partitions_and_fails_on_hash_drift():
    author = {
        "speaker": "Joel Rosenblum",
        "profile_sample_ids": ["p"],
        "holdout_sample_ids": ["h"],
        "expected_canonical_sha256": {"p": "a" * 64, "h": "b" * 64},
    }
    rows = [
        {
            "sample_id": "p",
            "canonical_sha256": "a" * 64,
            "word_count": 200,
            "quality_flags": [],
            "local_text_path": "/tmp/p",
        },
        {
            "sample_id": "h",
            "canonical_sha256": "b" * 64,
            "word_count": 180,
            "quality_flags": ["thin-for-authorship-attribution"],
            "local_text_path": "/tmp/h",
        },
    ]
    selected = fixed._verify_selected_rows(rows, author_spec=author)
    assert [row["partition"] for row in selected] == [
        "profile",
        "reserved_holdout",
    ]
    assert selected[1]["source_quality_flags"] == [
        "thin-for-authorship-attribution"
    ]

    rows[1]["canonical_sha256"] = "c" * 64
    with pytest.raises(fixed.FixedSplitLuarError, match="canonical hash drift"):
        fixed._verify_selected_rows(rows, author_spec=author)


def test_profile_cosine_matrix_is_symmetric():
    profiles = {
        "Joel Rosenblum": np.array([1.0, 0.0]),
        "Stian Gudmundsen Høiland": np.array([0.8, 0.6]),
        "David Vardy": np.array([0.0, 1.0]),
        "Greg Goode": np.array([-1.0, 0.0]),
    }
    result = fixed._profile_cosine_matrix(profiles, AUTHORS)
    matrix = result["rows"]
    assert result["labels"] == AUTHORS
    assert matrix[0][0] == 1.0
    assert matrix[0][1] == matrix[1][0] == 0.8
    assert matrix[0][3] == -1.0


def test_predictions_preserve_every_author_score(tmp_path: Path):
    text_path = tmp_path / "holdout.txt"
    text_path.write_text("held out text", encoding="utf-8")
    row = {
        "sample_id": "joel-h",
        "source_group": "group-h",
        "speaker": "Joel Rosenblum",
        "local_text_path": str(text_path),
    }
    key = fixed._row_key(row)
    profiles = {
        "Joel Rosenblum": np.array([1.0, 0.0]),
        "Stian Gudmundsen Høiland": np.array([0.9, 0.1]),
        "David Vardy": np.array([0.0, 1.0]),
        "Greg Goode": np.array([-1.0, 0.0]),
    }
    result = fixed._predictions(
        [row],
        authors=AUTHORS,
        profiles=profiles,
        embeddings={key: np.array([1.0, 0.0])},
    )
    assert result[0]["predicted"] == "Joel Rosenblum"
    assert result[0]["correct"] is True
    assert set(result[0]["cosine_scores"]) == set(AUTHORS)


def test_metadata_row_excludes_local_paths_and_prose():
    row = {
        "sample_id": "a",
        "source_group": "g",
        "speaker": "Joel Rosenblum",
        "partition": "profile",
        "source_word_count": 200,
        "source_canonical_sha256": "a" * 64,
        "word_count": 150,
        "canonical_sha256": "b" * 64,
        "source_quality_flags": [],
        "quality_flags": [],
        "local_text_path": "/private/a.txt",
        "text": "private prose",
    }
    encoded = json.dumps(fixed._metadata_row(row))
    assert "local_text_path" not in encoded
    assert "private prose" not in encoded
