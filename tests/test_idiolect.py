import json

import pytest

from pangram_lab.idiolect import (
    IdiolectError,
    closed_set_ier_report,
    retention_report,
)


PROFILE = [
    (
        "I don't think people work that way. I mean, maybe sometimes they do, "
        "but usually there's another thing going on—and that's the part I care about."
    ),
    (
        "I've tried the polished answer before, and it didn't help. What helped? "
        "Not pretending I knew more than I did, for one thing."
    ),
    (
        "We can make a theory out of it, sure. But I still want to know what "
        "somebody actually did, what happened next, and whether it worked."
    ),
]


def test_identical_candidate_has_zero_edit_and_full_relative_retention():
    original = (
        "I don't know why we'd turn this into a framework. The useful question "
        "is what happened, and what I noticed after it happened."
    )
    report = retention_report(PROFILE, original, original)

    assert report["report_type"] == "single_author_retention_proxy"
    assert report["is_closed_set_ier"] is False
    assert report["edit"]["token_change_fraction"] == 0.0
    assert report["edit"]["length_ratio"] == 1.0
    for channel in ("surface", "content_light"):
        metrics = report["profile_similarity"][channel]
        assert metrics["candidate_minus_original"] == pytest.approx(0.0)
        assert metrics["retention_ratio"] == pytest.approx(1.0)


def test_polished_generic_rewrite_moves_away_on_both_channels():
    original = (
        "I don't think this is mainly about clarity. I've heard clear answers "
        "that didn't tell me what the person actually saw, so I kept asking."
    )
    candidate = (
        "This issue can be understood through a structured analytical framework. "
        "Effective communication requires clarity, consistency, and a comprehensive "
        "account of the relevant observations."
    )
    report = retention_report(PROFILE, original, candidate)

    assert report["interpretation"]["direction"] == (
        "farther_from_profile_on_both_measured_channels"
    )
    assert report["profile_similarity"]["surface"]["candidate_minus_original"] < 0
    assert (
        report["profile_similarity"]["content_light"]["candidate_minus_original"]
        < 0
    )


def test_report_is_metadata_only_and_does_not_embed_source_text():
    secret_phrase = "private owner phrase that must not enter the report"
    report = retention_report(PROFILE, secret_phrase, secret_phrase + " again")
    payload = json.dumps(report)

    assert secret_phrase not in payload
    assert report["privacy"]["raw_text_stored_in_report"] is False
    assert len(report["texts"]["original_sha256"]) == 64
    assert len(report["texts"]["candidate_sha256"]) == 64


def test_closed_set_ier_reports_attribution_drop_in_percentage_points():
    profiles = {
        "a": [
            "I don't buy that. I reckon we'd notice, wouldn't we?",
            "I've seen it go wrong, and I still don't call it settled.",
            "We'd better ask what happened next, because I don't know yet.",
        ],
        "b": [
            "The analysis therefore establishes a consistent formal conclusion.",
            "The available evidence supports the stated institutional framework.",
            "Accordingly, the procedure yields a comprehensive determination.",
        ],
    }
    items = [
        {
            "id": "a1",
            "author": "a",
            "original": "I don't reckon that's settled, and I'd ask what happened next.",
            "rewrite": "Accordingly, the evidence establishes a comprehensive conclusion.",
        },
        {
            "id": "b1",
            "author": "b",
            "original": "Accordingly, the procedure supports the formal conclusion.",
            "rewrite": "I don't buy that, and I'd still ask what happened next.",
        },
    ]
    report = closed_set_ier_report(profiles, items)

    assert report["report_type"] == "closed_set_idiolect_erasure_rate"
    assert report["paper_instrument_equivalent"] is False
    assert report["channels"]["surface"]["baseline_accuracy"] == 1.0
    assert report["channels"]["surface"]["rewrite_accuracy"] == 0.0
    assert (
        report["channels"]["surface"][
            "idiolect_erasure_rate_percentage_points"
        ]
        == 100.0
    )


def test_closed_set_ier_requires_multiple_authors():
    with pytest.raises(IdiolectError, match="at least two authors"):
        closed_set_ier_report(
            {"only": ["I write one way.", "Still one way.", "Again one way."]},
            [
                {
                    "author": "only",
                    "original": "I write one way.",
                    "rewrite": "The prose was revised.",
                }
            ],
        )
