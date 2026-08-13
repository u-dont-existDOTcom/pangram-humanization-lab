import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from pangram_lab.closeout_request import CloseoutRequestError, process_request


def run(repo: Path, *args: str):
    return subprocess.run(args, cwd=repo, text=True, capture_output=True, check=True)


def setup_repo(root: Path):
    run(root, "git", "init", "-b", "main")
    run(root, "git", "config", "user.email", "test@example.com")
    run(root, "git", "config", "user.name", "Test")
    (root / "state").mkdir()
    (root / "state" / "lesson-closeout-config.json").write_text(json.dumps({"lesson_index": "state/LESSON-INDEX.md", "lesson_summary_globs": ["state/WORKING-LESSONS*.md"]}), encoding="utf-8")
    (root / "state" / "LESSON-LEDGER.json").write_text('{"schema_version": 1, "entries": []}\n', encoding="utf-8")
    (root / "state" / "LESSON-INDEX.md").write_text("# Index\n", encoding="utf-8")
    (root / "state" / "WORKING-LESSONS.md").write_text("# Lessons\n", encoding="utf-8")
    run(root, "git", "add", ".")
    run(root, "git", "commit", "-m", "base")
    run(root, "git", "switch", "-c", "evidence")
    p = root / "state" / "experiments" / "e.json"
    p.parent.mkdir(parents=True)
    p.write_text('{"result": "mixed"}\n', encoding="utf-8")
    run(root, "git", "add", ".")
    run(root, "git", "commit", "-m", "evidence")
    source_sha = hashlib.sha256(p.read_bytes()).hexdigest()
    run(root, "git", "switch", "main")
    return source_sha


def write_request(root: Path, source_sha: str, **changes):
    obj = {"schema_version": 1, "request_id": "R1", "source_path": "state/experiments/e.json", "source_ref": "evidence", "source_sha256": source_sha, "finding": "This result needs local interpretation.", "disposition": "article-specific", "reason": "Bound to this experiment.", "promoted_to": []}
    obj.update(changes)
    p = root / "state" / "lesson-closeout-requests" / "R1.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    return p


def test_non_promoted_request_records_ledger_and_receipt(tmp_path: Path):
    sha = setup_repo(tmp_path)
    request = write_request(tmp_path, sha)
    result = process_request(tmp_path, request)
    ledger = json.loads((tmp_path / "state" / "LESSON-LEDGER.json").read_text())
    assert len(ledger["entries"]) == 1
    assert ledger["entries"][0]["source_sha256"] == sha
    assert ledger["entries"][0]["source_ref"] == "evidence"
    receipt = json.loads(request.read_text())
    assert receipt["status"] == "processed"
    assert receipt["ledger_entry_ids"] == [result["id"]]


def test_request_hash_must_match_named_ref(tmp_path: Path):
    setup_repo(tmp_path)
    request = write_request(tmp_path, "0" * 64)
    with pytest.raises(CloseoutRequestError, match="hash"):
        process_request(tmp_path, request)
    ledger = json.loads((tmp_path / "state" / "LESSON-LEDGER.json").read_text())
    assert ledger["entries"] == []


def test_promoted_request_appends_explicit_blocks_once(tmp_path: Path):
    sha = setup_repo(tmp_path)
    request = write_request(tmp_path, sha, disposition="promoted", reason="", promoted_to=["state/LESSON-INDEX.md", "state/WORKING-LESSONS.md"], summary_target="state/WORKING-LESSONS.md", lesson_block="## New lesson\nKeep the tested function separate from its wording.\n", index_block="- See New lesson in WORKING-LESSONS.md\n")
    first = process_request(tmp_path, request)
    second = process_request(tmp_path, request)
    assert first["id"] == second["id"]
    assert (tmp_path / "state" / "WORKING-LESSONS.md").read_text().count("## New lesson") == 1
    assert (tmp_path / "state" / "LESSON-INDEX.md").read_text().count("See New lesson") == 1
    ledger = json.loads((tmp_path / "state" / "LESSON-LEDGER.json").read_text())
    assert len(ledger["entries"]) == 1
