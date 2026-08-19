from pangram_lab import luar_target_verification_v2 as v2


def _audit(*, flags=None, issues=None, ambiguous=0, quotes=0):
    return {
        "clean": False,
        "issues": issues or ["blocking-prefix-quality-flag"],
        "blocking_prefix_quality_flags": flags or ["possible-unremoved-dialogue"],
        "ambiguous_single_word_line_count": ambiguous,
        "leading_quote_marker_line_count": quotes,
    }


def test_hash_matched_historical_dialogue_heuristic_only_is_admitted():
    allowed, reason = v2.historical_matched_prefix_exception(
        _audit(),
        current_canonical_sha256="a" * 64,
        historical_canonical_sha256="a" * 64,
    )
    assert allowed is True
    assert reason == (
        "hash-matched-historical-exact50-target-generic-dialogue-heuristic-only"
    )


def test_hash_drift_fails_closed():
    allowed, reason = v2.historical_matched_prefix_exception(
        _audit(),
        current_canonical_sha256="a" * 64,
        historical_canonical_sha256="b" * 64,
    )
    assert allowed is False
    assert reason is None


def test_additional_prefix_problem_fails_closed():
    allowed, _ = v2.historical_matched_prefix_exception(
        _audit(ambiguous=1),
        current_canonical_sha256="a" * 64,
        historical_canonical_sha256="a" * 64,
    )
    assert allowed is False

    allowed, _ = v2.historical_matched_prefix_exception(
        _audit(flags=["possible-platform-chrome"]),
        current_canonical_sha256="a" * 64,
        historical_canonical_sha256="a" * 64,
    )
    assert allowed is False

    allowed, _ = v2.historical_matched_prefix_exception(
        _audit(quotes=1),
        current_canonical_sha256="a" * 64,
        historical_canonical_sha256="a" * 64,
    )
    assert allowed is False
