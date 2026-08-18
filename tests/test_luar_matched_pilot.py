from pathlib import Path

import numpy as np

from pangram_lab import luar_matched_pilot as lp


def _row(tmp_path, sample, speaker, group, text):
    path = tmp_path / f"{sample}.txt"
    path.write_text(text, encoding="utf-8")
    return {
        "sample_id": sample,
        "speaker": speaker,
        "source_group": group,
        "word_count": len(text.split()),
        "canonical_sha256": lp._text_sha256(text),
        "local_text_path": str(path),
    }


def test_cosine_rejects_zero_norm_and_scores_identity():
    assert lp._cosine(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == 1.0
    try:
        lp._cosine(np.array([0.0, 0.0]), np.array([1.0, 0.0]))
    except ValueError as exc:
        assert "zero-norm" in str(exc)
    else:
        raise AssertionError("expected zero-norm cosine failure")


def test_nearest_profile_uses_mean_training_embeddings_and_author_order_tie_break(tmp_path):
    train = [
        _row(tmp_path, "a1", "A", "ta1", "alpha one"),
        _row(tmp_path, "a2", "A", "ta2", "alpha two"),
        _row(tmp_path, "b1", "B", "tb1", "beta one"),
        _row(tmp_path, "b2", "B", "tb2", "beta two"),
    ]
    test = [
        _row(tmp_path, "x", "A", "heldout", "test x"),
        _row(tmp_path, "tie", "A", "heldout", "test tie"),
    ]
    vectors = {
        lp._row_key(train[0]): np.array([1.0, 0.0]),
        lp._row_key(train[1]): np.array([1.0, 0.2]),
        lp._row_key(train[2]): np.array([0.0, 1.0]),
        lp._row_key(train[3]): np.array([0.2, 1.0]),
        lp._row_key(test[0]): np.array([1.0, 0.1]),
        lp._row_key(test[1]): np.array([1.0, 1.0]),
    }
    predictions = lp.nearest_profile_predictions(
        train,
        test,
        authors=["A", "B"],
        embeddings=vectors,
    )
    assert predictions[0]["predicted"] == "A"
    # Symmetric profiles make the second example an exact tie; author order wins.
    assert predictions[1]["predicted"] == "A"
    assert set(predictions[0]["cosine_scores"]) == {"A", "B"}


def test_whole_folds_are_balanced_and_exclude_heldout_group(tmp_path):
    authors = ["Joel Rosenblum", "David Vardy", "Stian Gudmundsen Høiland"]
    held = ["g1", "g2", "g3", "g4"]
    spec = {
        "authors": authors,
        "held_out_source_groups": held,
        "conditions": {
            "whole_document": {
                "documents_per_author_per_fold": 6,
                "joel_supplement_sample_ids": ["s1", "s2"],
            }
        },
    }
    matched = []
    for idx, group in enumerate(held, start=1):
        matched.append(_row(tmp_path, f"j{idx}", authors[0], group, "joel words here"))
        matched.append(_row(tmp_path, f"dtest{idx}", authors[1], group, "david test words"))
        if group != "g4":
            matched.append(_row(tmp_path, f"stest{idx}", authors[2], group, "stian test words"))
    # Fifth Joel source group is not a held-out matched group (the tiny Anatta lane in live data).
    matched.append(_row(tmp_path, "j5", authors[0], "joel-extra-matched", "joel tiny extra"))
    supplements = [
        _row(tmp_path, "s1", authors[0], "sup1", "supplement one"),
        _row(tmp_path, "s2", authors[0], "sup2", "supplement two"),
    ]
    controls = []
    for author, prefix in [(authors[1], "d"), (authors[2], "s")]:
        for idx in range(6):
            controls.append(
                _row(
                    tmp_path,
                    f"{prefix}{idx}",
                    author,
                    f"{prefix}-train-{idx}",
                    "control words " * (idx + 2),
                )
            )
    folds = lp._whole_folds(spec, matched, supplements, controls)
    assert len(folds) == 4
    for held_out, train, test in folds:
        assert {row["source_group"] for row in train}.isdisjoint(
            {row["source_group"] for row in test}
        )
        counts = {author: sum(row["speaker"] == author for row in train) for author in authors}
        assert counts == {author: 6 for author in authors}


def test_metadata_does_not_expose_embeddings_or_paths(tmp_path):
    row = _row(tmp_path, "x", "A", "g", "some text here")
    meta = lp._meta(row)
    assert "local_text_path" not in meta
    assert set(meta) == {
        "sample_id",
        "source_group",
        "speaker",
        "word_count",
        "canonical_sha256",
    }
