import re

import pytest

from pangram_lab import surface_svm_equal_budget as eb


def test_prefix_exact_words_preserves_original_punctuation_and_spacing():
    text = "Hello,   world! This—isn't reconstructed; it stays. Extra words here."
    prefix = eb.prefix_exact_words(text, 5)
    assert prefix == "Hello,   world! This—isn't reconstructed; it"
    assert len(eb._WORD_RE.findall(prefix)) == 5


def test_prefix_exact_words_fails_closed_when_too_short():
    with pytest.raises(ValueError, match="needs at least 5"):
        eb.prefix_exact_words("only three words", 5)


def test_largest_eligible_filters_short_docs_before_ranking():
    rows = [
        {"speaker": "A", "sample_id": "short", "word_count": 49, "source_group": "g0"},
        {"speaker": "A", "sample_id": "big", "word_count": 500, "source_group": "g1"},
        {"speaker": "A", "sample_id": "mid", "word_count": 100, "source_group": "g2"},
        {"speaker": "B", "sample_id": "other", "word_count": 1000, "source_group": "g3"},
    ]
    selected = eb._largest_eligible(rows, "A", count=2, min_words=50)
    assert [row["sample_id"] for row in selected] == ["big", "mid"]


def test_normalized_row_keeps_source_group_and_exact_budget(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("One, two three four five six seven.", encoding="utf-8")
    row = {
        "sample_id": "sample",
        "source_group": "thread",
        "speaker": "A",
        "word_count": 7,
        "local_text_path": str(source),
    }
    normalized = eb._normalized_row(
        row,
        words=5,
        out_dir=tmp_path / "out",
        prefix="x",
    )
    assert normalized["source_group"] == "thread"
    assert normalized["word_count"] == 5
    assert normalized["original_word_count"] == 7
    assert len(eb._WORD_RE.findall((tmp_path / "out" / "x-sample.txt").read_text())) == 5
    assert normalized["canonical_sha256"]
