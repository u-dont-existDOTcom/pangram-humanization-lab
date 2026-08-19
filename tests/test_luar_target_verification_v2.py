from pathlib import Path

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


def _source(tmp_path: Path, sample_id: str, text: str):
    path = tmp_path / f"{sample_id}.txt"
    path.write_text(text, encoding="utf-8")
    return {
        "sample_id": sample_id,
        "source_group": f"group-{sample_id}",
        "word_count": len(text.split()),
        "canonical_sha256": sample_id.ljust(64, "0")[:64],
        "quality_flags": [],
        "local_text_path": str(path),
    }


def _words(prefix: str, count: int = 60):
    return " ".join(f"{prefix}{index}" for index in range(count))


def test_independent_joel_selection_skips_dirty_prefix_and_never_reuses_holdout(
    tmp_path,
):
    rows = [
        _source(tmp_path, "dirty", "Heading\n" + _words("d")),
        _source(tmp_path, "profile1", _words("a")),
        _source(tmp_path, "profile2", _words("b")),
        _source(tmp_path, "profile3", _words("c")),
        _source(tmp_path, "hold1", _words("h")),
        _source(tmp_path, "hold2", _words("i")),
    ]
    spec = {
        "word_budget_per_document": 50,
        "profile_documents_per_author": 3,
        "independent_joel_holdout_count": 2,
        "target_author": "Joel Rosenblum",
        "independent_joel_profile_candidate_order": [
            "dirty",
            "profile1",
            "profile2",
            "profile3",
        ],
        "independent_joel_holdout_candidate_order": [
            "profile1",
            "hold1",
            "hold2",
        ],
    }
    profile, holdout = v2.normalize_independent_joel(
        spec,
        rows,
        working_dir=tmp_path / "normalized",
    )
    assert [row["sample_id"] for row in profile] == [
        "profile1",
        "profile2",
        "profile3",
    ]
    assert [row["sample_id"] for row in holdout] == ["hold1", "hold2"]
    assert not (
        {row["source_group"] for row in profile}
        & {row["source_group"] for row in holdout}
    )
