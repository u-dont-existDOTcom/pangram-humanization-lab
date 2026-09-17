import numpy as np

from pangram_lab import fixed_split_luar as fixed


def test_fixed_split_spec_shape_validation_accepts_four_authors():
    authors = ["Joel", "Stian", "David", "Greg"]
    spec = {
        "schema_version": 1,
        "word_budget_per_document": 150,
        "profile_documents_per_author": 1,
        "holdout_documents_per_author": 1,
        "authors": [
            {
                "speaker": author,
                "role": "target-author" if author == "Joel" else "ordinary-matched-control",
                "profile_sample_ids": [f"{author}-profile"],
                "holdout_sample_ids": [f"{author}-holdout"],
            }
            for author in authors
        ],
    }
    assert set(fixed._validate_spec(spec)) == set(authors)


def test_profile_cosine_matrix_is_square_and_symmetric():
    authors = ["Joel", "Stian", "David", "Greg"]
    profiles = {
        "Joel": np.array([1.0, 0.0]),
        "Stian": np.array([0.8, 0.6]),
        "David": np.array([0.0, 1.0]),
        "Greg": np.array([-1.0, 0.0]),
    }
    result = fixed._profile_cosine_matrix(profiles, authors)
    assert result["labels"] == authors
    assert len(result["rows"]) == 4
    assert all(len(row) == 4 for row in result["rows"])
    assert result["rows"][0][1] == result["rows"][1][0]
    assert result["rows"][0][0] == 1.0
