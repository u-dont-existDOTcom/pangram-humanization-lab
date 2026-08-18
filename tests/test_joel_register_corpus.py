import json
from pathlib import Path

import pytest

from pangram_lab import joel_register_corpus as jrc
from pangram_lab.corpus_acquire import canonicalize


def test_prefix_to_word_budget_is_exact_and_keeps_trailing_punctuation():
    text = "One, two three. Four five."
    result = jrc.prefix_to_word_budget(text, 3)
    assert result == "One, two three."
    assert canonicalize(result).word_count == 3


def test_prefix_to_word_budget_preserves_short_source():
    assert jrc.prefix_to_word_budget("Only two.", 10) == "Only two."


def test_validate_spec_rejects_duplicate_document_ids():
    spec = {
        "schema_version": 1,
        "documents": [
            {"sample_id": "same"},
            {"sample_id": "same"},
        ],
        "views": [{"view_id": "v", "sample_ids": ["same"]}],
    }
    with pytest.raises(ValueError, match="sample_ids must be unique"):
        jrc._validate_spec(spec)


def test_build_register_corpus_creates_metadata_only_balanced_views(
    monkeypatch, tmp_path: Path
):
    source_a = tmp_path / "source-a.txt"
    source_b = tmp_path / "source-b.txt"
    source_a.write_text("Alpha one two three four.\n", encoding="utf-8")
    source_b.write_text("Beta one two three four five.\n", encoding="utf-8")

    def fake_acquire_inventory(
        inventory_path, *, out_dir, manifest_out, sample_ids, timeout
    ):
        assert sample_ids == {"a", "b"}
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        manifest_out.write_text("{}\n", encoding="utf-8")
        rows = []
        for sample_id, path, site in (
            ("a", source_a, "site-a"),
            ("b", source_b, "site-b"),
        ):
            canon = canonicalize(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "sample_id": sample_id,
                    "source_group": f"group-{sample_id}",
                    "site_group": site,
                    "date": "2020-01-01",
                    "source_html_sha256": "1" * 64,
                    "canonical_sha256": canon.sha256,
                    "word_count": canon.word_count,
                    "local_text_path": str(path),
                }
            )
        return {"results": rows, "errors": []}

    monkeypatch.setattr(jrc, "acquire_inventory", fake_acquire_inventory)

    inventory = tmp_path / "inventory.json"
    inventory.write_text("{}\n", encoding="utf-8")
    spec = {
        "schema_version": 1,
        "date": "2026-08-18",
        "source_inventory": str(inventory),
        "corpus_status": "candidate",
        "method_decision": "adapt",
        "method_note": "test",
        "documents": [
            {
                "sample_id": "a",
                "cleanup_rule": "whole-after-existing-blockquote-drop",
                "site_group": "site-a",
                "primary_register": "register-a",
                "registers": ["register-a"],
                "review_status": "reviewed",
                "role": "profile-candidate",
            },
            {
                "sample_id": "b",
                "cleanup_rule": "whole-after-existing-blockquote-drop",
                "site_group": "site-b",
                "primary_register": "register-b",
                "registers": ["register-b"],
                "review_status": "manual-audit-pending",
                "role": "profile-candidate-pending-audit",
            },
        ],
        "views": [
            {
                "view_id": "full",
                "sample_ids": ["a", "b"],
                "word_budget_per_source": None,
                "status": "candidate",
            },
            {
                "view_id": "equal-two",
                "sample_ids": ["a", "b"],
                "word_budget_per_source": 2,
                "require_exact_budget": True,
                "status": "diagnostic",
            },
        ],
        "excluded_or_deferred": [],
        "blocking_reasons": ["test blocker"],
        "interpretation_rule": "not calibrated",
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    receipt_path = tmp_path / "receipt.json"

    receipt = jrc.build_register_corpus(
        spec_path,
        out_dir=tmp_path / "out",
        receipt_out=receipt_path,
    )

    assert receipt["document_count"] == 2
    assert receipt["pending_manual_audit_count"] == 1
    assert receipt["benchmark_eligible"] is False
    equal = next(row for row in receipt["views"] if row["view_id"] == "equal-two")
    assert equal["total_words"] == 4
    assert equal["all_sources_exact_budget"] is True
    assert equal["largest_source_fraction"] == 0.5
    assert equal["site_group_count"] == 2
    assert len(equal["canonical_hash_set_sha256"]) == 64

    encoded = receipt_path.read_text(encoding="utf-8")
    assert "local_text_path" not in encoded
    assert "Alpha one" not in encoded
    assert "Beta one" not in encoded


def test_exact_budget_view_fails_closed_for_short_source(tmp_path: Path):
    path = tmp_path / "short.txt"
    path.write_text("One word.\n", encoding="utf-8")
    source = {
        "sample_id": "short",
        "source_group": "short",
        "site_group": "site",
        "primary_register": "register",
        "review_status": "reviewed",
        "role": "candidate",
        "profile_word_count": 2,
        "profile_canonical_sha256": canonicalize("One word.").sha256,
        "local_text_path": str(path),
    }
    with pytest.raises(ValueError, match="fewer than required 3 words"):
        jrc._build_view(
            {
                "view_id": "equal-three",
                "sample_ids": ["short"],
                "word_budget_per_source": 3,
                "require_exact_budget": True,
                "status": "test",
            },
            {"short": source},
            out_dir=tmp_path / "out",
        )
