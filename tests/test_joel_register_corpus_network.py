import json
from pathlib import Path

from pangram_lab import joel_register_corpus_network as network


def test_paced_acquirer_sleeps_between_requests_across_inventory_calls(tmp_path):
    calls = []
    sleeps = []

    def base_acquire(
        inventory_path,
        *,
        out_dir,
        manifest_out,
        sample_ids,
        timeout=30,
    ):
        assert len(sample_ids) == 1
        sample_id = next(iter(sample_ids))
        calls.append((Path(inventory_path).name, sample_id, timeout))
        out_dir.mkdir(parents=True, exist_ok=True)
        text_path = out_dir / f"{sample_id}.txt"
        text_path.write_text("owner text\n", encoding="utf-8")
        result = {
            "sample_id": sample_id,
            "source_group": sample_id,
            "site_group": "test",
            "provenance": "natural-owner-confirmed",
            "modality": "written",
            "canonical_sha256": sample_id.ljust(64, "0")[:64],
            "source_html_sha256": "a" * 64,
            "word_count": 2,
            "quality_flags": [],
            "local_text_path": str(text_path),
        }
        runtime = {"results": [result], "errors": []}
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        manifest_out.write_text(json.dumps(runtime), encoding="utf-8")
        return runtime

    acquirer = network.PacedInventoryAcquirer(
        spacing_seconds=65,
        base_acquire_fn=base_acquire,
        sleep_fn=sleeps.append,
    )
    first = acquirer(
        Path("first.json"),
        out_dir=tmp_path / "first",
        manifest_out=tmp_path / "first-manifest.json",
        sample_ids={"b", "a"},
        timeout=17,
    )
    second = acquirer(
        Path("second.json"),
        out_dir=tmp_path / "second",
        manifest_out=tmp_path / "second-manifest.json",
        sample_ids={"c"},
        timeout=17,
    )

    assert calls == [
        ("first.json", "a", 17),
        ("first.json", "b", 17),
        ("second.json", "c", 17),
    ]
    assert sleeps == [65.0, 65.0]
    assert len(first["results"]) == 2
    assert len(second["results"]) == 1
    assert acquirer.metadata() == {
        "strategy": "one-sample-at-a-time-global-spacing",
        "spacing_seconds": 65.0,
        "request_count": 3,
        "sleep_count": 2,
    }


def test_paced_acquirer_preserves_errors_without_urls_or_prose(tmp_path):
    def base_acquire(
        inventory_path,
        *,
        out_dir,
        manifest_out,
        sample_ids,
        timeout=30,
    ):
        del inventory_path, out_dir, timeout
        sample_id = next(iter(sample_ids))
        runtime = {
            "results": [],
            "errors": [
                {
                    "sample_id": sample_id,
                    "url": "https://example.invalid/source",
                    "error": "HTTP Error 429: Too Many Requests",
                }
            ],
        }
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        manifest_out.write_text(json.dumps(runtime), encoding="utf-8")
        return runtime

    acquirer = network.PacedInventoryAcquirer(
        spacing_seconds=0,
        base_acquire_fn=base_acquire,
        sleep_fn=lambda _: None,
    )
    result = acquirer(
        Path("inventory.json"),
        out_dir=tmp_path / "out",
        manifest_out=tmp_path / "manifest.json",
        sample_ids={"sample-a"},
    )

    assert result["errors"][0]["sample_id"] == "sample-a"
    assert result["errors"][0]["error"].startswith("HTTP Error 429")
    assert result["network_strategy"] == "one-sample-at-a-time-global-spacing"
