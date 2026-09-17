import json
from pathlib import Path

from pangram_lab import idiolect
from pangram_lab import idiolect_pangram_prescreen as prescreen


def _row(surface, content, safe, *, sha="a", family="romance"):
    return {
        "text_sha256": sha * 64 if len(sha) == 1 else sha,
        "measurement_keys": [f"{family}-x"],
        "article_family": family,
        "word_count": 100,
        "prediction_short": "Human" if safe else "Mixed",
        "fraction_ai": 0.0 if safe else 0.2,
        "fraction_ai_assisted": 0.0,
        "strict_full_human": safe,
        "headline_human": safe,
        "surface_profile_similarity": surface,
        "content_light_profile_similarity": content,
    }


def test_extract_profile_sections_clips_independently():
    source = (
        "===== ONE =====\n"
        + " ".join(f"a{i}" for i in range(80))
        + "\n===== TWO =====\n"
        + " ".join(f"b{i}" for i in range(90))
        + "\n"
    )
    rows = prescreen.extract_profile_sections(
        source, ["ONE", "TWO"], max_words_per_section=60
    )
    assert [row["section"] for row in rows] == ["ONE", "TWO"]
    assert [row["word_count"] for row in rows] == [60, 60]
    assert all(len(row["sha256"]) == 64 for row in rows)


def test_fit_rule_requires_zero_training_false_safes_and_prefers_coverage():
    rows = [
        _row(0.90, 0.90, True, sha="a"),
        _row(0.85, 0.88, True, sha="b"),
        _row(0.80, 0.86, True, sha="c"),
        _row(0.75, 0.50, False, sha="d"),
        _row(0.60, 0.82, False, sha="e"),
    ]
    rule, receipt = prescreen.fit_zero_false_safe_rule(
        rows, label_field="strict_full_human"
    )
    assert rule is not None
    cleared = [row for row in rows if rule.clears(row)]
    assert len(cleared) == 3
    assert all(row["strict_full_human"] for row in cleared)
    assert receipt["training_false_safe_count"] == 0


def test_cross_article_holdout_counts_false_safe():
    romance = [
        _row(0.90, 0.90, True, sha="a", family="romance"),
        _row(0.85, 0.88, True, sha="b", family="romance"),
        _row(0.80, 0.86, True, sha="c", family="romance"),
        _row(0.60, 0.60, False, sha="d", family="romance"),
    ]
    spiritual = [
        _row(0.92, 0.92, True, sha="e", family="spiritual-bypassing"),
        _row(0.87, 0.90, True, sha="f", family="spiritual-bypassing"),
        _row(0.83, 0.87, True, sha="1", family="spiritual-bypassing"),
        # This unsafe point sits above the threshold learned on Romance.
        _row(0.89, 0.89, False, sha="2", family="spiritual-bypassing"),
    ]
    result = prescreen.cross_article_calibration(
        romance + spiritual,
        label_field="strict_full_human",
        article_groups=["romance", "spiritual-bypassing"],
        substitution_acceptance={
            "required_independent_article_families": 2,
            "required_total_heldout_cleared": 1,
            "required_false_safe_count": 0,
            "maximum_one_sided_95pct_false_safe_upper_bound": 1.0,
        },
    )
    assert result["heldout_false_safe_count"] >= 1
    assert result["substitution_authorized"] is False
    assert "heldout_false_safe_detected" in result["substitution_blockers"]


def test_wilson_upper_is_conservative_with_zero_errors():
    assert prescreen._wilson_upper(0, 0) == 1.0
    assert 0.02 < prescreen._wilson_upper(0, 100) < 0.04
    assert prescreen._wilson_upper(1, 100) > prescreen._wilson_upper(0, 100)


def test_article_family_scope():
    assert prescreen._article_family("romance-vows-r1") == "romance"
    assert prescreen._article_family("historical-whitespace-audit-r1") == "romance"
    assert (
        prescreen._article_family("spiritual-bypassing-r1")
        == "spiritual-bypassing"
    )
    assert prescreen._article_family("pangram4-public-actions-smoke") is None


def test_strict_target_is_stricter_than_headline_human():
    result = {
        "prediction_short": "Human",
        "fraction_ai": 0.01,
        "fraction_ai_assisted": 0.0,
    }
    assert prescreen._headline_human(result) is True
    assert prescreen._strict_human(result) is False


def test_profile_features_are_existing_idiolect_channels():
    profile = idiolect.build_profile(
        [
            "I think this is useful because it leaves the question open. " * 20,
            "But what happens if you actually try it in ordinary life? " * 20,
            "So I changed my mind after I looked at the evidence again. " * 20,
        ]
    )
    candidate = "I changed my mind because the obvious answer did not work. " * 20
    channels = idiolect._feature_channels(candidate)
    surface = idiolect._cosine(profile.surface, channels["surface"])
    content = idiolect._cosine(profile.content_light, channels["content_light"])
    assert 0.0 <= surface <= 1.0
    assert 0.0 <= content <= 1.0
