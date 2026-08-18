import json
from pathlib import Path

import pytest

from pangram_lab import joel_register_corpus as rc
from pangram_lab.corpus_acquire import canonicalize


def _fake_acquirer(sample_texts, *, provenance="natural-owner-confirmed", modality="written"):
    def acquire(inventory_path, *, out_dir, manifest_out, sample_ids, timeout=30):
        del inventory_path, timeout
        out_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for sample_id in sorted(sample_ids):
            text = sample_texts[sample_id]
            canon = canonicalize(text)
            path = out_dir / f"{sample_id}.txt"
            path.write_text(canon.text + "\n", encoding="utf-8")
            results.append(
                {
                    "sample_id": sample_id,
                    "source_group": sample_id,
                    "site_group": "test-site",
                    "provenance": provenance,
                    "modality": modality,
                    "source_html_sha256": "a" * 64,
                    "canonical_sha256": canon.sha256,
                    "word_count": canon.word_count,
                    "quality_flags": canon.quality_flags,
                    "local_text_path": str(path),
                }
            )
        runtime = {"results": results, "errors": []}
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        manifest_out.write_text(json.dumps(runtime), encoding="utf-8")
        return runtime

    return acquire


def _write_spec(tmp_path: Path, register: dict) -> Path:
    spec = {
        "schema_version": 1,
        "status": "test-freeze",
        "purpose": "test",
        "method_decision": {"choice": "adapt-existing"},
        "inventories": {"test": "unused-inventory.json"},
        "registers": [register],
        "nonready_registers": [],
        "excluded_sources": [],
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


def test_empty_person_label_cleanup_is_conservative():
    text = (
        "Remember:\n"
        "Owner text.\n"
        "Ben asked:\n"
        "More owner text.\n"
        "Joel Rosenblum:\n"
        "Still owner text."
    )
    cleaned, effects = rc.apply_cleanup_pipeline(
        text, ["whole", "drop-empty-person-label-lines"]
    )
    assert "Remember:" in cleaned
    assert "Ben asked:" not in cleaned
    assert "Joel Rosenblum:" not in cleaned
    assert effects == {"empty_person_label_lines_removed": 2}


def test_register_freeze_is_metadata_only_and_enforces_partitions(tmp_path):
    sample_texts = {
        "profile-a": "Owner prose " * 150,
        "profile-b": "Another owner passage " * 100,
        "holdout-a": "Held out owner passage " * 70,
    }
    profile_a = canonicalize(sample_texts["profile-a"])
    profile_b = canonicalize(sample_texts["profile-b"])
    holdout_a = canonicalize(sample_texts["holdout-a"])
    register = {
        "register_id": "test-register",
        "status": "profile-and-holdout-frozen",
        "target_voice": "natural-owner-confirmed-written",
        "register_labels": ["test"],
        "profile": [
            {
                "inventory": "test",
                "sample_id": "profile-a",
                "cleanup_rules": ["whole"],
                "expected_source_canonical_sha256": profile_a.sha256,
                "expected_source_word_count": profile_a.word_count,
                "expected_source_quality_flags": profile_a.quality_flags,
                "expected_canonical_sha256": profile_a.sha256,
                "expected_word_count": profile_a.word_count,
            },
            {
                "inventory": "test",
                "sample_id": "profile-b",
                "cleanup_rules": ["whole"],
                "expected_source_canonical_sha256": profile_b.sha256,
                "expected_source_word_count": profile_b.word_count,
                "expected_source_quality_flags": profile_b.quality_flags,
                "expected_canonical_sha256": profile_b.sha256,
                "expected_word_count": profile_b.word_count,
            },
        ],
        "reserved_holdout": [
            {
                "inventory": "test",
                "sample_id": "holdout-a",
                "cleanup_rules": ["whole"],
                "expected_source_canonical_sha256": holdout_a.sha256,
                "expected_source_word_count": holdout_a.word_count,
                "expected_source_quality_flags": holdout_a.quality_flags,
                "expected_canonical_sha256": holdout_a.sha256,
                "expected_word_count": holdout_a.word_count,
            }
        ],
        "support": [],
        "gates": {
            "minimum_profile_sources": 2,
            "minimum_profile_words": 500,
            "maximum_largest_profile_source_fraction": 0.60,
            "minimum_reserved_holdout_sources": 1,
            "minimum_reserved_holdout_words": 250,
            "maximum_profile_thin_sources": 0,
            "maximum_reserved_holdout_thin_sources": 0,
        },
        "known_limitations": [],
    }
    spec_path = _write_spec(tmp_path, register)
    receipt_path = tmp_path / "receipt.json"
    result = rc.build_register_corpus(
        spec_path,
        out_dir=tmp_path / "out",
        receipt_out=receipt_path,
        acquire_fn=_fake_acquirer(sample_texts),
    )

    assert result["status"] == "test-freeze"
    assert result["errors"] == []
    assert len(result["corpus_identity_sha256"]) == 64
    frozen = result["registers"]["test-register"]
    assert frozen["partitions"]["profile"]["independent_source_count"] == 2
    assert frozen["partitions"]["reserved_holdout"]["independent_source_count"] == 1

    encoded = json.dumps(result, sort_keys=True)
    for forbidden in (
        "local_text_path",
        "raw_text",
        "canonical_text",
        "https://",
        "http://",
    ):
        assert forbidden not in encoded


def test_source_snapshot_drift_fails_closed_without_url_or_prose(tmp_path):
    sample_texts = {"profile-a": "Owner prose " * 80}
    register = {
        "register_id": "test-register",
        "status": "candidate",
        "target_voice": "natural-owner-confirmed-written",
        "register_labels": ["test"],
        "profile": [
            {
                "inventory": "test",
                "sample_id": "profile-a",
                "cleanup_rules": ["whole"],
                "expected_source_canonical_sha256": "0" * 64,
            }
        ],
        "reserved_holdout": [],
        "support": [],
        "gates": {},
        "known_limitations": [],
    }
    spec_path = _write_spec(tmp_path, register)
    result = rc.build_register_corpus(
        spec_path,
        out_dir=tmp_path / "out",
        receipt_out=tmp_path / "receipt.json",
        acquire_fn=_fake_acquirer(sample_texts),
    )

    assert result["status"] == "failed"
    assert "source canonical hash drift" in result["errors"][0]["error"]
    encoded = json.dumps(result)
    assert "Owner prose" not in encoded
    assert "http" not in encoded
    assert "local_text_path" not in encoded


def test_register_gate_failure_is_explicit(tmp_path):
    sample_texts = {"profile-a": "Owner prose " * 80}
    canon = canonicalize(sample_texts["profile-a"])
    register = {
        "register_id": "test-register",
        "status": "candidate",
        "target_voice": "natural-owner-confirmed-written",
        "register_labels": ["test"],
        "profile": [
            {
                "inventory": "test",
                "sample_id": "profile-a",
                "cleanup_rules": ["whole"],
                "expected_source_canonical_sha256": canon.sha256,
                "expected_source_word_count": canon.word_count,
                "expected_source_quality_flags": canon.quality_flags,
            }
        ],
        "reserved_holdout": [],
        "support": [],
        "gates": {"minimum_profile_sources": 2},
        "known_limitations": [],
    }
    spec_path = _write_spec(tmp_path, register)
    result = rc.build_register_corpus(
        spec_path,
        out_dir=tmp_path / "out",
        receipt_out=tmp_path / "receipt.json",
        acquire_fn=_fake_acquirer(sample_texts),
    )

    assert result["status"] == "failed-register-gates"
    assert result["errors"] == [
        {
            "register_id": "test-register",
            "gate": "minimum_profile_sources",
            "expected": 2,
            "actual": 1,
        }
    ]


def test_duplicate_source_group_across_partitions_is_rejected(tmp_path):
    sample_texts = {
        "profile-a": "Owner prose " * 80,
        "holdout-a": "Held out owner prose " * 80,
    }

    def acquire(inventory_path, *, out_dir, manifest_out, sample_ids, timeout=30):
        runtime = _fake_acquirer(sample_texts)(
            inventory_path,
            out_dir=out_dir,
            manifest_out=manifest_out,
            sample_ids=sample_ids,
            timeout=timeout,
        )
        for row in runtime["results"]:
            row["source_group"] = "same-source"
        return runtime

    register = {
        "register_id": "test-register",
        "status": "candidate",
        "target_voice": "natural-owner-confirmed-written",
        "register_labels": ["test"],
        "profile": [
            {"inventory": "test", "sample_id": "profile-a", "cleanup_rules": ["whole"]}
        ],
        "reserved_holdout": [
            {"inventory": "test", "sample_id": "holdout-a", "cleanup_rules": ["whole"]}
        ],
        "support": [],
        "gates": {},
        "known_limitations": [],
    }
    spec_path = _write_spec(tmp_path, register)
    with pytest.raises(ValueError, match="source_group appears in multiple partitions"):
        rc.build_register_corpus(
            spec_path,
            out_dir=tmp_path / "out",
            receipt_out=tmp_path / "receipt.json",
            acquire_fn=acquire,
        )
