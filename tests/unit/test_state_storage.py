import json
from pathlib import Path
from authorial_flow.artifacts import ArtifactStore
from authorial_flow.events import EventJournal
from authorial_flow.config import RuntimeConfig


def test_artifact_store_is_content_addressed(tmp_path: Path):
    store = ArtifactStore(tmp_path / "artifacts")
    a = store.put_bytes(b"same", "txt", {"producer": "test"})
    b = store.put_bytes(b"same", "txt", {"producer": "test"})
    assert a.sha256 == b.sha256
    assert a.path == b.path
    assert a.path.read_bytes() == b"same"


def test_event_sequence_is_append_only(tmp_path: Path):
    journal = EventJournal(tmp_path / "events.jsonl")
    assert journal.append("node.start", {"node": "bootstrap"}) == 1
    assert journal.append("node.end", {"node": "bootstrap"}) == 2
    rows = [json.loads(x) for x in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert [r["sequence"] for r in rows] == [1, 2]


def test_runtime_config_uses_state_below_root(tmp_path: Path):
    cfg = RuntimeConfig.from_root(tmp_path)
    assert cfg.state_dir == tmp_path / ".state"
    assert cfg.heartbeat_seconds == 10
