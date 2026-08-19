from pathlib import Path

import pytest

from pangram_lab import luar_target_verification as tv
from pangram_lab.luar_matched_pilot import _row_key


def _write_row(tmp_path: Path, sample_id: str, speaker: str, text: str, *, group=None):
    path = tmp_path / f"{sample_id}.txt"
    path.write_text(text, encoding="utf-8")
    return {
        "sample_id": sample_id,
        "source_group": group or f"g-{sample_id}",
        "speaker": speaker,
        "word_count": len(text.split()),
        "canonical_sha256": sample_id.ljust(64, "0")[:64],
        "quality_flags": [],
        "local_text_path": str(path),
    }


def _words(prefix: str, count: int = 60):
    return " ".join(f"{prefix}{index}" for index in range(count))


def test_prefix_audit_checks_only_normalized_boundary(tmp_path):
    clean = _write_row(tmp_path, "clean", "A", _words("word", 50))
    audit = tv.prefix_audit(clean)
    assert audit["clean"] is True
    assert audit["normalized_word_count"] == 50

    dialogue = _write_row(
        tmp_path,
        "dialogue",
        "A",
        "Other Person: " + _words("word", 55),
    )
    audit = tv.prefix_audit(dialogue)
    assert audit["clean"] is False
    assert "blocking-prefix-quality-flag" in audit["issues"]


def test_control_selection_skips_dirty_prefix_and_keeps_three_clean(tmp_path):
    author = "Stian Gudmundsen Høiland"
    rows = [
        _write_row(tmp_path, "dirty", author, "Other Person: " + _words("x", 60)),
        _write_row(tmp_path, "clean1", author, _words("a", 60)),
        _write_row(tmp_path, "clean2", author, _words("b", 60)),
        _write_row(tmp_path, "clean3", author, _words("c", 60)),
    ]
    spec = {
        "word_budget_per_document": 50,
        "profile_documents_per_author": 3,
        "control_profile_candidate_order": {
            author: ["dirty", "clean1", "clean2", "clean3"]
        },
    }
    selected, receipt = tv.select_control_profiles(
        spec,
        rows,
        working_dir=tmp_path / "normalized",
    )
    assert [row["sample_id"] for row in selected[author]] == [
        "clean1",
        "clean2",
        "clean3",
    ]
    assert receipt[author]["candidate_review"][0]["reason"] == "exact-prefix-cleanliness-failed"
    assert all(int(row["word_count"]) == 50 for row in selected[author])


def test_score_target_reports_hard_and_ordinary_margins(tmp_path):
    np = pytest.importorskip(
        "numpy",
        reason="LUAR/numpy is an optional isolated research dependency",
    )

    authors = ["Joel Rosenblum", "Stian", "David", "Greg"]
    row = _write_row(tmp_path, "target", "Joel Rosenblum", _words("j", 50))
    embeddings = {_row_key(row): np.array([1.0, 0.0])}
    profiles = {
        "Joel Rosenblum": np.array([1.0, 0.0]),
        "Stian": np.array([0.9, 0.1]),
        "David": np.array([0.0, 1.0]),
        "Greg": np.array([0.5, 0.5]),
    }
    scored = tv._score_target(
        row,
        profiles=profiles,
        authors=authors,
        target="Joel Rosenblum",
        hard_negative="Stian",
        ordinary_controls=["David", "Greg"],
        embeddings=embeddings,
    )
    assert scored["predicted"] == "Joel Rosenblum"
    assert scored["target_rank"] == 1
    assert scored["target_minus_hard_negative_margin"] > 0
    assert scored["best_ordinary_control"] == "Greg"
    assert scored["target_minus_best_ordinary_margin"] > 0


def test_stratum_summary_keeps_competitor_margins_separate():
    rows = [
        {
            "predicted": "Joel",
            "correct": True,
            "target_minus_competitor_margin": {"Stian": 0.1, "David": 0.2},
        },
        {
            "predicted": "Stian",
            "correct": False,
            "target_minus_competitor_margin": {"Stian": -0.05, "David": 0.3},
        },
    ]
    result = tv._stratum_summary(
        rows,
        authors=["Joel", "Stian", "David"],
        target="Joel",
    )
    assert result["target_top1_accuracy"] == 0.5
    assert result["target_margin_by_competitor"]["Stian"]["positive_count"] == 1
    assert result["target_margin_by_competitor"]["Stian"]["negative_count"] == 1
    assert result["target_margin_by_competitor"]["David"]["negative_count"] == 0
