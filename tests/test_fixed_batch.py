from pathlib import Path
import json
import pytest

from pangram_lab.fixed_batch import load_spec, run_batch


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


class FakeClient:
    def __init__(self):
        self.calls = []

    def detect_cached(self, text, cache, measurement_key="base"):
        self.calls.append((text, measurement_key))
        return {
            "stage": "STAGE_SUCCESS",
            "version": "4.0",
            "headline": "Human Written",
            "prediction_short": "Human",
            "fraction_ai": 0.0,
            "fraction_ai_assisted": 0.0,
            "fraction_human": 1.0,
        }


def test_run_batch_preserves_order_keys_and_writes_sha256(tmp_path: Path):
    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "exp",
        "variants": [
            {"id": "A", "text": "first  text"},
            {"id": "B", "text": "second"},
        ],
    }
    out = tmp_path / "results.json"
    client = FakeClient()
    result = run_batch(spec, client=client, cache=object(), output_path=out)
    assert client.calls == [
        ("first  text", "exp_A"),
        ("second", "exp_B"),
    ]
    assert [row["id"] for row in result["results"]] == ["A", "B"]
    assert result["results"][0]["text_sha256"] == "e18caa2c4fdd7105982b375c2f7efc0b778ef9dc2437e941edd8af5c0f8eb244"
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved == result
