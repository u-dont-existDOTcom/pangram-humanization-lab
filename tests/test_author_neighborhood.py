import copy

import pytest

from pangram_lab.author_neighborhood import analyze_author_neighborhood


AUTHORS = ["Joel Rosenblum", "Stian Gudmundsen Høiland", "David Vardy"]


def _spec():
    return {
        "schema_version": 1,
        "owner_author": "Joel Rosenblum",
        "owner_supplied_neighbor_hypotheses": [
            {"author": "Stian Gudmundsen Høiland"}
        ],
        "input_contract": {"required_author_count_minimum": 3},
        "reliability_boundary": {"eligible_status_literal": "eligible"},
        "interpretation_guardrails": ["nearest-author flip is not erasure"],
    }


def _profile(author: str, letter: str):
    return {
        "author": author,
        "profile_identity": f"profile-{letter}",
        "source_groups": [f"source-{letter}-1", f"source-{letter}-2"],
        "word_count": 1000,
        "canonical_hash_set_sha256": letter * 64,
    }


def _dataset():
    return {
        "schema_version": 1,
        "condition_id": "unit-test-condition",
        "instrument": {"name": "synthetic-score-fixture", "version": "1"},
        "authors": AUTHORS,
        "owner_author": "Joel Rosenblum",
        "declared_neighbor_hypotheses": ["Stian Gudmundsen Høiland"],
        "profile_identities": [
            _profile("Joel Rosenblum", "a"),
            _profile("Stian Gudmundsen Høiland", "b"),
            _profile("David Vardy", "c"),
        ],
        "profile_cosine_matrix": {
            "Joel Rosenblum": {
                "Joel Rosenblum": 1.0,
                "Stian Gudmundsen Høiland": 0.84,
                "David Vardy": 0.41,
            },
            "Stian Gudmundsen Høiland": {
                "Joel Rosenblum": 0.84,
                "Stian Gudmundsen Høiland": 1.0,
                "David Vardy": 0.45,
            },
            "David Vardy": {
                "Joel Rosenblum": 0.41,
                "Stian Gudmundsen Høiland": 0.45,
                "David Vardy": 1.0,
            },
        },
        "originals": [
            {
                "sample_id": "joel-clear",
                "true_author": "Joel Rosenblum",
                "source_group": "joel-holdout-1",
                "register": "philosophical-dialogue",
                "canonical_sha256": "d" * 64,
                "word_count": 400,
                "scores_by_author": {
                    "Joel Rosenblum": 0.91,
                    "Stian Gudmundsen Høiland": 0.82,
                    "David Vardy": 0.25,
                },
                "original_reliability_status": "eligible",
            },
            {
                "sample_id": "joel-ambiguous",
                "true_author": "Joel Rosenblum",
                "source_group": "joel-holdout-2",
                "register": "philosophical-dialogue",
                "canonical_sha256": "e" * 64,
                "word_count": 250,
                "scores_by_author": {
                    "Joel Rosenblum": 0.78,
                    "Stian Gudmundsen Høiland": 0.79,
                    "David Vardy": 0.20,
                },
                "original_reliability_status": "ambiguous",
            },
            {
                "sample_id": "stian-clear",
                "true_author": "Stian Gudmundsen Høiland",
                "source_group": "stian-holdout-1",
                "register": "philosophical-dialogue",
                "canonical_sha256": "f" * 64,
                "word_count": 300,
                "scores_by_author": {
                    "Joel Rosenblum": 0.75,
                    "Stian Gudmundsen Høiland": 0.88,
                    "David Vardy": 0.22,
                },
                "original_reliability_status": "eligible",
            },
            {
                "sample_id": "david-clear",
                "true_author": "David Vardy",
                "source_group": "david-holdout-1",
                "register": "philosophical-dialogue",
                "canonical_sha256": "1" * 64,
                "word_count": 300,
                "scores_by_author": {
                    "Joel Rosenblum": 0.31,
                    "Stian Gudmundsen Høiland": 0.30,
                    "David Vardy": 0.90,
                },
                "original_reliability_status": "eligible",
            },
        ],
        "rewrites": [
            {
                "candidate_id": "joel-clear-rewrite",
                "original_sample_id": "joel-clear",
                "edit_condition": "owner-one-pass",
                "edit_dose": "D2",
                "canonical_sha256": "2" * 64,
                "word_count": 390,
                "scores_by_author": {
                    "Joel Rosenblum": 0.94,
                    "Stian Gudmundsen Høiland": 0.96,
                    "David Vardy": 0.29,
                },
            },
            {
                "candidate_id": "joel-ambiguous-rewrite",
                "original_sample_id": "joel-ambiguous",
                "edit_condition": "owner-one-pass",
                "edit_dose": "D2",
                "canonical_sha256": "3" * 64,
                "word_count": 245,
                "scores_by_author": {
                    "Joel Rosenblum": 0.82,
                    "Stian Gudmundsen Høiland": 0.85,
                    "David Vardy": 0.24,
                },
            },
        ],
    }


def test_near_neighbor_confusion_and_rewrite_are_separated():
    result = analyze_author_neighborhood(_dataset(), _spec())

    owner = result["original_aggregate"]["owner_neighbor_summary"]
    assert owner["owner_original_count"] == 2
    assert owner["owner_to_declared_neighbor_confusion_count"] == 1
    assert owner["owner_to_declared_neighbor_confusion_rate"] == 0.5
    assert owner["declared_neighbor_highest_alternative_count"] == 2

    ranking = result["original_aggregate"]["hard_negative_rankings"][
        "Joel Rosenblum"
    ]
    assert ranking[0]["alternative_author"] == "Stian Gudmundsen Høiland"

    eligible = result["rewrites"][0]
    assert eligible["target_score_delta"] == pytest.approx(0.03)
    assert eligible["target_margin_delta"] == pytest.approx(-0.11)
    assert eligible["candidate_winner_is_declared_owner_neighbor"] is True
    assert eligible["eligible_for_rewrite_degradation_interpretation"] is True
    assert (
        eligible["attribution_observation_status"]
        == "eligible-top1-attribution-loss-observation"
    )

    ambiguous = result["rewrites"][1]
    assert ambiguous["eligible_for_rewrite_degradation_interpretation"] is False
    assert (
        ambiguous["attribution_observation_status"]
        == "not-eligible-original-ambiguous-or-insufficient"
    )

    aggregate = result["rewrite_aggregate"]
    assert aggregate["eligible_rewrite_count"] == 1
    assert aggregate["eligible_top1_attribution_loss_observation_count"] == 1
    assert aggregate[
        "eligible_top1_attribution_loss_to_declared_owner_neighbor_count"
    ] == 1
    assert aggregate["ier_computed"] is False


def test_eligible_original_must_be_uniquely_correct():
    dataset = _dataset()
    dataset["originals"][0]["scores_by_author"]["Joel Rosenblum"] = 0.81
    dataset["originals"][0]["scores_by_author"][
        "Stian Gudmundsen Høiland"
    ] = 0.82
    with pytest.raises(
        ValueError, match="eligible original must be uniquely attributed"
    ):
        analyze_author_neighborhood(dataset, _spec())


def test_score_vectors_must_cover_exact_author_set():
    dataset = _dataset()
    del dataset["originals"][0]["scores_by_author"]["David Vardy"]
    with pytest.raises(ValueError, match="author mismatch"):
        analyze_author_neighborhood(dataset, _spec())


def test_profile_matrix_must_be_symmetric():
    dataset = _dataset()
    dataset["profile_cosine_matrix"]["Joel Rosenblum"][
        "Stian Gudmundsen Høiland"
    ] = 0.80
    with pytest.raises(ValueError, match="not symmetric"):
        analyze_author_neighborhood(dataset, _spec())


def test_forbidden_prose_or_embedding_fields_fail_closed():
    dataset = _dataset()
    dataset["originals"][0]["raw_text"] = "must never enter durable input"
    with pytest.raises(ValueError, match="forbidden field"):
        analyze_author_neighborhood(dataset, _spec())

    dataset = _dataset()
    dataset["profile_identities"][0]["embedding"] = [0.1, 0.2]
    with pytest.raises(ValueError, match="forbidden field"):
        analyze_author_neighborhood(dataset, _spec())


def test_declared_neighbor_must_be_a_known_nonowner_author():
    dataset = _dataset()
    dataset["declared_neighbor_hypotheses"] = ["Unknown Person"]
    with pytest.raises(ValueError, match="not in authors"):
        analyze_author_neighborhood(dataset, _spec())

    dataset = _dataset()
    dataset["declared_neighbor_hypotheses"] = ["Joel Rosenblum"]
    with pytest.raises(ValueError, match="cannot be its own neighbor"):
        analyze_author_neighborhood(dataset, _spec())


def test_no_rewrites_is_valid_for_original_neighborhood_calibration():
    dataset = _dataset()
    dataset["rewrites"] = []
    result = analyze_author_neighborhood(dataset, _spec())
    assert result["rewrites"] == []
    assert result["rewrite_aggregate"]["rewrite_count"] == 0
    assert result["rewrite_aggregate"]["ier_computed"] is False


def test_input_objects_are_not_mutated():
    dataset = _dataset()
    spec = _spec()
    dataset_before = copy.deepcopy(dataset)
    spec_before = copy.deepcopy(spec)
    analyze_author_neighborhood(dataset, spec)
    assert dataset == dataset_before
    assert spec == spec_before
