import collections
import re
from pathlib import Path

from pangram_lab import luar_content_controls as controls


def test_block_shuffle_is_deterministic_and_preserves_exact_slots_and_multiset():
    text = "One  two\nthree four\tFIVE, six seven eight nine ten eleven twelve."
    a, audit_a = controls.deterministic_block_shuffle(text, seed=17, block_words=5)
    b, audit_b = controls.deterministic_block_shuffle(text, seed=17, block_words=5)
    assert a == b
    assert audit_a == audit_b
    assert a != text
    assert collections.Counter(re.findall(r"\S+", a)) == collections.Counter(re.findall(r"\S+", text))
    assert re.findall(r"\s+", a) == re.findall(r"\s+", text)
    assert audit_a["token_multiset_preserved"] is True
    assert audit_a["whitespace_pattern_preserved"] is True


def test_block_shuffle_keeps_tokens_inside_fixed_blocks():
    text = " ".join(f"t{idx}" for idx in range(12))
    output, _ = controls.deterministic_block_shuffle(text, seed=99, block_words=4)
    source = text.split()
    result = output.split()
    for start in range(0, 12, 4):
        assert collections.Counter(source[start:start + 4]) == collections.Counter(result[start:start + 4])


def test_function_mask_retains_closed_class_words_and_form():
    text = "The unusually happy person is here, but quantum-zebra42 works; and you are there.\nReally?"
    output, audit = controls.function_word_mask(text)
    assert "The" in output
    assert "is" in output
    assert "here" in output
    assert "but" in output
    assert "and" in output
    assert "you" in output
    assert "are" in output
    assert "there" in output
    assert "unusually" not in output
    assert "happy" not in output
    assert "person" not in output
    assert "quantum" not in output
    assert "zebra42" not in output
    assert "Really" not in output
    assert re.findall(r"\s+", output) == re.findall(r"\s+", text)
    assert len(re.findall(r"\S+", output)) == len(re.findall(r"\S+", text))
    assert audit["masked_tokens"] > 0
    assert audit["retained_function_tokens"] > 0
    assert audit["function_word_list_sha256"] == controls._FUNCTION_WORD_SHA256


def test_transform_folds_writes_runtime_text_but_audit_contains_no_text(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text(" ".join(f"word{idx}" for idx in range(60)), encoding="utf-8")
    row = {
        "sample_id": "sample-a",
        "source_group": "group-a",
        "speaker": "Author A",
        "word_count": 60,
        "canonical_sha256": "before",
        "local_text_path": str(source),
    }
    folds = [("held", [row], [row])]
    transformed, audit = controls.transform_folds(
        folds,
        transform_name="shuffle",
        out_dir=tmp_path / "out",
        seed=3,
        block_words=50,
    )
    assert len(transformed) == 1
    assert len(audit) == 2
    for record in audit:
        assert "local_text_path" not in record
        assert "text" not in record
        assert record["token_multiset_preserved"] is True
    for _, train, test in transformed:
        for transformed_row in train + test:
            assert Path(transformed_row["local_text_path"]).exists()
            assert transformed_row["canonical_sha256"] != "before"


def test_function_word_inventory_is_frozen_and_nontrivial():
    assert len(controls._FUNCTION_WORDS) > 150
    assert len(controls._FUNCTION_WORD_SHA256) == 64
    assert "the" in controls._FUNCTION_WORD_SET
    assert "because" in controls._FUNCTION_WORD_SET
    assert "here" in controls._FUNCTION_WORD_SET
    assert "there" in controls._FUNCTION_WORD_SET
