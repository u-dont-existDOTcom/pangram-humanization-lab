import hashlib
import json
from pathlib import Path

import pytest

from pangram_lab.result_paths import (
    canonical_result_path,
    load_compatible_existing_result,
    new_result_envelope,
    resolve_result_path,
    result_is_complete,
    spec_sha256,
)


def spec(text="one", experiment_id="exp-1"):
    return {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": experiment_id,
        "audit_id": "audit-1",
        "variants": [{"id": "A", "section_id": "section-a", "text": text}],
    }


def test_canonical_result_path_is_derived_from_experiment_id(tmp_path: Path):
    assert canonical_result_path(tmp_path, "exp-1") == tmp_path / "state/experiments/exp-1-results.json"


def test_canonical_result_path_rejects_unsafe_experiment_id(tmp_path: Path):
    for bad in ("../exp", "a/b", ".hidden", "two words"):
        with pytest.raises(ValueError, match="safe filename segment"):
            canonical_result_path(tmp_path, bad)


def test_resolve_result_path_rejects_workflow_path_that_does_not_match_experiment(tmp_path: Path):
    with pytest.raises(ValueError, match="must be derived from experiment_id"):
        resolve_result_path(tmp_path, spec(), Path("state/experiments/reused-results.json"))


def test_spec_hash_is_stable_across_json_key_order():
    a = spec()
    b = {
        "variants": a["variants"],
        "audit_id": "audit-1",
        "experiment_id": "exp-1",
        "format": "pangram-fixed-batch-v1",
    }
    assert spec_sha256(a) == spec_sha256(b)


def test_existing_fingerprinted_result_rejects_changed_spec(tmp_path: Path):
    path = canonical_result_path(tmp_path, "exp-1")
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "format": "pangram-fixed-batch-results-v1",
                "experiment_id": "exp-1",
                "spec_sha256": spec_sha256(spec("one")),
                "results": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="different fixed-batch spec"):
        load_compatible_existing_result(spec("two"), path)


def test_completed_same_spec_is_reusable_without_rewrite(tmp_path: Path):
    current = spec("one")
    path = canonical_result_path(tmp_path, "exp-1")
    path.parent.mkdir(parents=True)
    saved = {
        "format": "pangram-fixed-batch-results-v1",
        "experiment_id": "exp-1",
        "spec_sha256": spec_sha256(current),
        "results": [{"id": "A", "text_sha256": "ignored-for-fingerprinted-result"}],
    }
    path.write_text(json.dumps(saved), encoding="utf-8")
    assert load_compatible_existing_result(current, path) == saved


def test_legacy_result_without_spec_hash_must_match_complete_variant_set(tmp_path: Path):
    current = spec("one")
    path = canonical_result_path(tmp_path, "exp-1")
    path.parent.mkdir(parents=True)
    saved = {
        "format": "pangram-fixed-batch-results-v1",
        "experiment_id": "exp-1",
        "results": [
            {
                "id": "A",
                "text_sha256": hashlib.sha256(b"one").hexdigest(),
                "section_id": "section-a",
            }
        ],
    }
    path.write_text(json.dumps(saved), encoding="utf-8")
    assert load_compatible_existing_result(current, path) == saved


def test_partial_legacy_result_fails_closed(tmp_path: Path):
    current = spec("one")
    current["variants"].append({"id": "B", "section_id": "section-a", "text": "two"})
    path = canonical_result_path(tmp_path, "exp-1")
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "format": "pangram-fixed-batch-results-v1",
                "experiment_id": "exp-1",
                "results": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="legacy result.*new experiment_id"):
        load_compatible_existing_result(current, path)


def test_new_result_envelope_binds_exact_spec_hash():
    current = spec("one")
    assert new_result_envelope(current) == {
        "format": "pangram-fixed-batch-results-v1",
        "experiment_id": "exp-1",
        "audit_id": "audit-1",
        "spec_sha256": spec_sha256(current),
        "results": [],
    }


def test_completed_result_is_recognized_only_when_all_variants_present():
    current = spec("one")
    saved = {
        "format": "pangram-fixed-batch-results-v1",
        "experiment_id": "exp-1",
        "spec_sha256": spec_sha256(current),
        "results": [{"id": "A"}],
    }
    assert result_is_complete(current, saved) is True
    saved["status"] = "section_call_cap_reached"
    assert result_is_complete(current, saved) is False
