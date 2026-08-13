import json
import subprocess
from pathlib import Path

import pytest

from pangram_lab.lesson_closeout import audit_ref
from pangram_lab.review_state import ReviewState, ReviewStateMismatch


def meta():
    return {"experiment_id": "exp-1", "audit_id": "audit-1", "sections": ["opening"], "variants": [{"id": "A", "section_id": "opening", "prediction_short": "Mixed", "fraction_human": 0.8}]}


def test_exact_hash_registers_once(tmp_path: Path):
    queue = ReviewState(tmp_path)
    first = queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    second = queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    assert first["id"] == second["id"]
    assert len(queue.pending()) == 1


def test_changed_hash_creates_new_review_item(tmp_path: Path):
    queue = ReviewState(tmp_path)
    first = queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    second = queue.register("state/experiments/result.json", "branch", "b" * 64, meta())
    assert first["id"] != second["id"]
    assert len(queue.pending()) == 2


def test_queue_contains_metadata_not_source_body(tmp_path: Path):
    queue = ReviewState(tmp_path)
    queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    raw = queue.path.read_text(encoding="utf-8")
    assert "source_text" not in raw
    entry = json.loads(raw)["entries"][0]
    assert entry["experiment_id"] == "exp-1"
    assert entry["sections"] == ["opening"]
    assert entry["variants"][0]["prediction_short"] == "Mixed"


def test_resolve_requires_exact_source_identity(tmp_path: Path):
    queue = ReviewState(tmp_path)
    entry = queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    resolved = queue.resolve("state/experiments/result.json", "branch", "a" * 64, ledger_entry_ids=["L-1"])
    assert resolved["id"] == entry["id"]
    assert resolved["status"] == "resolved"
    assert queue.pending() == []


def test_resolve_rejects_changed_hash(tmp_path: Path):
    queue = ReviewState(tmp_path)
    queue.register("state/experiments/result.json", "branch", "a" * 64, meta())
    with pytest.raises(ReviewStateMismatch):
        queue.resolve("state/experiments/result.json", "branch", "b" * 64, ledger_entry_ids=["L-1"])


def _git(root: Path, *args: str):
    return subprocess.run(args, cwd=root, text=True, capture_output=True, check=True)


def _cross_ref_repo(root: Path):
    _git(root, "git", "init", "-b", "main")
    _git(root, "git", "config", "user.email", "test@example.com")
    _git(root, "git", "config", "user.name", "Test")
    (root / "state").mkdir()
    (root / "state" / "lesson-closeout-config.json").write_text(json.dumps({"enforcement_started_at_utc": "2099-01-01T00:00:00Z", "tracked_globs": []}), encoding="utf-8")
    (root / "state" / "LESSON-LEDGER.json").write_text('{"schema_version": 1, "entries": []}\n', encoding="utf-8")
    _git(root, "git", "add", ".")
    _git(root, "git", "commit", "-m", "base")
    _git(root, "git", "switch", "-c", "evidence")
    ReviewState(root).register("state/experiments/e.json", "evidence", "a" * 64, {})
    _git(root, "git", "add", ".")
    _git(root, "git", "commit", "-m", "queue")
    _git(root, "git", "switch", "main")


def test_audit_reports_cross_ref_queue_item_without_main_disposition(tmp_path: Path):
    _cross_ref_repo(tmp_path)
    report = audit_ref(tmp_path, "evidence")
    assert report["ok"] is False
    assert len(report["pending_review"]) == 1


def test_audit_treats_matching_main_ledger_entry_as_reviewed(tmp_path: Path):
    _cross_ref_repo(tmp_path)
    ledger = {"schema_version": 1, "entries": [{"id": "L-1", "source_path": "state/experiments/e.json", "source_sha256": "a" * 64, "finding": "Reviewed result.", "disposition": "article-specific", "reason": "Local finding.", "promoted_to": [], "recorded_at_utc": "2026-08-13T00:00:00+00:00", "source_ref": "evidence"}]}
    (tmp_path / "state" / "LESSON-LEDGER.json").write_text(json.dumps(ledger) + "\n", encoding="utf-8")
    report = audit_ref(tmp_path, "evidence")
    assert report["pending_review"] == []
    assert report["ok"] is True
