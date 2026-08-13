import json
from pathlib import Path

import pytest

from pangram_lab.review_queue import ReviewQueue, ReviewQueueMismatch


def meta():
    return {"experiment_id": "exp-1", "audit_id": "audit-1", "sections": ["opening"], "variants": [{"id": "A", "section_id": "opening", "prediction_short": "Mixed", "fraction_human": 0.8}]}


def test_exact_hash_registers_once(tmp_path: Path):
    queue = ReviewQueue(tmp_path)
    first = queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    second = queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    assert first["id"] == second["id"]
    assert len(queue.pending()) == 1


def test_changed_hash_creates_new_review_item(tmp_path: Path):
    queue = ReviewQueue(tmp_path)
    first = queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    second = queue.register("state/experiments/result.json", "branch", "b" * 64, meta())
    assert first["id"] != second["id"]
    assert len(queue.pending()) == 2


def test_queue_contains_metadata_not_source_body(tmp_path: Path):
    queue = ReviewQueue(tmp_path)
    queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    raw = queue.path.read_text(encoding="utf-8")
    assert "source_text" not in raw
    entry = json.loads(raw)["entries"][0]
    assert entry["experiment_id"] == "exp-1"
    assert entry["sections"] == ["opening"]
    assert entry["variants"][0]["prediction_short"] == "Mixed"


def test_resolve_requires_exact_source_identity(tmp_path: Path):
    queue = ReviewQueue(tmp_path)
    entry = queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    resolved = queue.resolve("state/experiments/result.json", "branch", "a" * 64, ledger_entry_ids=["L-1"])
    assert resolved["id"] == entry["id"]
    assert resolved["status"] == "resolved"
    assert queue.pending() == []


def test_resolve_rejects_changed_hash(tmp_path: Path):
    queue = ReviewQueue(tmp_path)
    queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    with pytest.raises(ReviewQueueMismatch):
        queue.resolve("state/experiments/result.json", "branch", "b" * 64, ledger_entry_ids=["L-1"])
