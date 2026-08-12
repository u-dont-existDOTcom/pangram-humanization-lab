from pathlib import Path
import json
import pytest

from pangram_lab.fixed_batch import load_spec


def test_load_spec_preserves_exact_order_and_text(tmp_path: Path):
    p = tmp_path / "batch.json"
    p.write_text(json.dumps({
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "x",
        "variants": [
            {"id": "A", "text": "first  text"},
            {"id": "B", "text": "second"},
        ],
    }), encoding="utf-8")
    spec = load_spec(p)
    assert [v["id"] for v in spec["variants"]] == ["A", "B"]
    assert spec["variants"][0]["text"] == "first  text"


def test_load_spec_rejects_duplicate_ids(tmp_path: Path):
    p = tmp_path / "batch.json"
    p.write_text(json.dumps({
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "x",
        "variants": [
            {"id": "A", "text": "one"},
            {"id": "A", "text": "two"},
        ],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_spec(p)
