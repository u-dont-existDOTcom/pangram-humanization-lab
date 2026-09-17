from pangram_lab import idiolect_pangram_prescreen_v2 as v2


def test_submitted_text_wins_when_hash_matches_even_if_result_differs():
    submitted = "This is the exact submitted text."
    returned = "This is the detector-returned text with normalization."
    expected = v2.base._sha256_text(submitted)
    text, source = v2.select_cache_text(
        {"text": submitted, "result": {"text": returned}},
        expected_sha256=expected,
    )
    assert text == submitted
    assert source == "top_level_submitted_text_hash_match"


def test_result_text_is_allowed_only_as_hash_matched_fallback():
    returned = "Detector-returned text preserved exactly."
    expected = v2.base._sha256_text(returned)
    text, source = v2.select_cache_text(
        {"result": {"text": returned}},
        expected_sha256=expected,
    )
    assert text == returned
    assert source == "result_text_hash_match"


def test_submitted_hash_mismatch_fails_closed_even_if_result_exists():
    submitted = "Submitted bytes changed."
    returned = "Returned bytes changed too."
    expected = "0" * 64
    text, source = v2.select_cache_text(
        {"text": submitted, "result": {"text": returned}},
        expected_sha256=expected,
    )
    assert text is None
    assert source == "top_level_submitted_text_hash_mismatch"


def test_missing_text_fails_closed():
    text, source = v2.select_cache_text({}, expected_sha256="0" * 64)
    assert text is None
    assert source == "missing_text"
