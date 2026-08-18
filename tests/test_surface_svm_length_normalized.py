from pathlib import Path

import pytest

from pangram_lab import surface_svm_length_normalized as ln


def test_centered_word_window_is_exact_and_deterministic():
    text = " ".join(f"w{idx}" for idx in range(60))
    a, start_a, total_a = ln.centered_word_window(text, 50)
    b, start_b, total_b = ln.centered_word_window(text, 50)
    assert a == b
    assert start_a == start_b == 5
    assert total_a == total_b == 60
    assert a.split() == [f"w{idx}" for idx in range(5, 55)]


def test_centered_word_window_rejects_short_document():
    with pytest.raises(ValueError, match="fewer than required window 50"):
        ln.centered_word_window(" ".join(["x"] * 49), 50)


def test_normalize_rows_writes_exact_window_and_metadata_only_audit(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text(" ".join(f"token{idx}" for idx in range(70)), encoding="utf-8")
    rows = [
        {
            "sample_id": "sample-a",
            "source_group": "group-a",
            "speaker": "A",
            "word_count": 70,
            "canonical_sha256": "source-sha",
            "local_text_path": str(source),
        }
    ]
    normalized, audit = ln._normalize_rows(rows, out_dir=tmp_path / "normalized", words=50)
    assert len(normalized) == 1
    assert normalized[0]["word_count"] == 50
    assert normalized[0]["canonical_sha256"] == audit[0]["window_sha256"]
    assert Path(normalized[0]["local_text_path"]).read_text(encoding="utf-8").split() == [
        f"token{idx}" for idx in range(10, 60)
    ]
    assert audit[0]["source_whitespace_token_count"] == 70
    assert audit[0]["window_start_token_index_zero_based"] == 10
    assert "local_text_path" not in audit[0]
    assert "text" not in audit[0]


def test_safe_name_removes_path_and_shell_punctuation():
    assert ln._safe_name("../a b/$c") == "..-a-b-c"
