from __future__ import annotations

# Temporary PR touch: rerun the base branch's code-only immutable-source CI after the ordinary-client compatibility fix.
import hashlib
import json
from pathlib import Path

import pytest

from pangram_lab.fixed_batch import load_spec, run_batch
from pangram_lab.result_paths import spec_sha256
from pangram_lab.text_sources import TextSourceError, resolve_text_sources, validate_text_source
from scripts.validate_paid_dispatch import validate_dispatch


SOURCE_TEXT = "exact reader-visible aggregate text\n"
SOURCE_SHA = hashlib.sha256(SOURCE_TEXT.encode("utf-8")).hexdigest()
SOURCE = {
    "kind": "github_blob",
    "repository": "u-dont-existDOTcom/joel-articles",
    "blob_sha": "0" * 40,
    "text_sha256": SOURCE_SHA,
}
HUMAN = {
    "stage": "STAGE_SUCCESS",
    "version": "4.0",
    "headline": "Human Written",
    "prediction_short": "Human",
    "fraction_ai": 0.0,
    "fraction_ai_assisted": 0.0,
    "fraction_human": 1.0,
}


class FakeClient:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def detect_cached(self, text, cache, measurement_key="base"):
        self.calls.append((text, measurement_key))
        return dict(HUMAN)


def write_spec(path: Path, variant: dict) -> Path:
    path.write_text(
        json.dumps(
            {
                "format": "pangram-fixed-batch-v1",
                "experiment_id": "blob-source-exp",
                "audit_id": "audit",
                "variants": [
                    {
                        "id": "A",
                        "section_id": "aggregate-a",
                        "budget_scope": "aggregate",
                        **variant,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_load_spec_accepts_immutable_text_source_without_inline_text(tmp_path: Path):
    spec = load_spec(write_spec(tmp_path / "spec.json", {"text_source": SOURCE}))
    assert spec["variants"][0]["text_source"] == SOURCE
    assert "text" not in spec["variants"][0]


def test_load_spec_rejects_both_inline_text_and_text_source(tmp_path: Path):
    path = write_spec(tmp_path / "spec.json", {"text": "inline", "text_source": SOURCE})
    with pytest.raises(ValueError, match="exactly one"):
        load_spec(path)


def test_load_spec_rejects_neither_inline_text_nor_text_source(tmp_path: Path):
    path = write_spec(tmp_path / "spec.json", {})
    with pytest.raises(ValueError, match="exactly one"):
        load_spec(path)


@pytest.mark.parametrize(
    "patch",
    [
        {"repository": "bad repository"},
        {"blob_sha": "A" * 40},
        {"blob_sha": "0" * 39},
        {"text_sha256": "0" * 63},
        {"kind": "url"},
    ],
)
def test_validate_text_source_rejects_malformed_identity(patch: dict[str, str]):
    source = dict(SOURCE)
    source.update(patch)
    with pytest.raises(TextSourceError):
        validate_text_source(source)


def test_resolve_text_sources_verifies_sha_and_preserves_registered_spec_identity(tmp_path: Path):
    registered = load_spec(write_spec(tmp_path / "spec.json", {"text_source": SOURCE}))
    before = spec_sha256(registered)
    seen: list[dict[str, str]] = []

    def fake_fetcher(source):
        seen.append(source)
        return SOURCE_TEXT

    resolved = resolve_text_sources(registered, fetcher=fake_fetcher)
    assert seen == [SOURCE]
    assert resolved["variants"][0]["text"] == SOURCE_TEXT
    assert resolved["variants"][0]["text_source"] == SOURCE
    assert "text" not in registered["variants"][0]
    assert spec_sha256(resolved) == before


def test_resolve_text_sources_rejects_resolved_sha_mismatch(tmp_path: Path):
    registered = load_spec(write_spec(tmp_path / "spec.json", {"text_source": SOURCE}))
    with pytest.raises(TextSourceError, match="SHA-256 mismatch"):
        resolve_text_sources(registered, fetcher=lambda source: "different text")


def test_run_batch_rejects_unresolved_text_source(tmp_path: Path):
    registered = load_spec(write_spec(tmp_path / "spec.json", {"text_source": SOURCE}))
    with pytest.raises(ValueError, match="not resolved"):
        run_batch(
            registered,
            client=FakeClient(),
            cache=object(),
            output_path=tmp_path / "out.json",
        )


def test_run_batch_uses_resolved_exact_text_and_records_source(tmp_path: Path):
    registered = load_spec(write_spec(tmp_path / "spec.json", {"text_source": SOURCE}))
    resolved = resolve_text_sources(registered, fetcher=lambda source: SOURCE_TEXT)
    client = FakeClient()
    result = run_batch(
        resolved,
        client=client,
        cache=object(),
        output_path=tmp_path / "out.json",
    )
    assert client.calls == [(SOURCE_TEXT, "blob-source-exp_A")]
    row = result["results"][0]
    assert row["text_sha256"] == SOURCE_SHA
    assert row["text_source"] == SOURCE
    assert result["spec_sha256"] == spec_sha256(registered)


def test_inline_spec_fingerprint_is_unchanged_by_text_source_identity_logic():
    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "inline",
        "audit_id": "audit",
        "variants": [
            {
                "id": "A",
                "section_id": "aggregate",
                "budget_scope": "aggregate",
                "text": "inline text",
            }
        ],
    }
    expected = hashlib.sha256(
        json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert spec_sha256(spec) == expected


def test_paid_dispatch_validation_accepts_text_source_without_network(tmp_path: Path):
    (tmp_path / "experiments").mkdir()
    write_spec(tmp_path / "experiments" / "blob-source-exp.json", {"text_source": SOURCE})
    result = validate_dispatch(
        tmp_path,
        spec_raw="experiments/blob-source-exp.json",
        output_raw="",
        confirmation="RUN_PAID_PANGRAM_FIXED_BATCH",
    )
    assert result["experiment_id"] == "blob-source-exp"
    assert result["variant_count"] == 1
