import json

import pytest

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.config import RuntimeConfig
from authorial_flow.events import EventJournal, EventJournalCorruptTail
from authorial_flow.runtime import RuntimeServices
from authorial_flow.work_feed import WorkFeed


def test_work_feed_is_allowlisted_redacted_and_chronological(tmp_path):
    rendered = []
    journal = EventJournal(tmp_path / "events.jsonl")
    feed = WorkFeed(
        journal=journal,
        renderer=rendered.append,
        secret_values=lambda: ["SECRET-FIXTURE"],
        silent_seconds=10,
    )
    feed.emit("proposal.complete", {
        "node": "generation",
        "proposal_ref": "p1",
        "proposal_sha256": "a" * 64,
        "text": "candidate SECRET-FIXTURE",
        "prompt": "must disappear",
    })
    feed.emit("guard.result", {
        "node": "generation",
        "gate": "fidelity",
        "verdict": "FAIL",
        "reason": "reason SECRET-FIXTURE",
        "raw_stdout": "must disappear",
    })

    read = journal.read_since(0)
    assert [row["kind"] for row in read.events] == [
        "proposal.complete",
        "guard.result",
    ]
    assert [row["sequence"] for row in read.events] == [1, 2]
    blob = json.dumps(read.events) + "\n".join(rendered)
    assert "SECRET-FIXTURE" not in blob
    assert "prompt" not in blob
    assert "raw_stdout" not in blob
    assert "[REDACTED]" in blob


def test_substantive_event_restarts_heartbeat_quiet_period(tmp_path):
    now = [0.0]
    journal = EventJournal(tmp_path / "events.jsonl")
    feed = WorkFeed(
        journal=journal,
        renderer=lambda _line: None,
        clock=lambda: now[0],
        silent_seconds=10,
    )
    feed.emit("model.start", {
        "provider": "claude",
        "model": "opus",
        "role": "writer",
        "pid": 7,
    })
    now[0] = 9.9
    assert feed.heartbeat({
        "provider": "claude",
        "model": "opus",
        "role": "writer",
        "pid": 7,
        "elapsed_seconds": 9.9,
    }) is None
    now[0] = 10.0
    assert feed.heartbeat({
        "provider": "claude",
        "model": "opus",
        "role": "writer",
        "pid": 7,
        "elapsed_seconds": 10,
    }) is not None
    feed.emit("guard.result", {
        "gate": "fidelity",
        "verdict": "PASS",
        "reason": "ok",
    })
    now[0] = 19.0
    assert feed.heartbeat({
        "provider": "claude",
        "model": "opus",
        "role": "writer",
        "pid": 7,
        "elapsed_seconds": 19,
    }) is None


def test_journal_stops_at_corrupt_tail_and_refuses_to_append_after_it(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text('{"sequence":1,"kind":"flow.phase"}\n{"sequence":2')
    journal = EventJournal(path)

    read = journal.read_since(0)
    assert [row["sequence"] for row in read.events] == [1]
    assert read.corrupt_line == 2
    assert read.corrupt_tail == '{"sequence":2'
    assert journal.latest() == {"sequence": 1, "kind": "flow.phase"}

    before = path.read_bytes()
    with pytest.raises(EventJournalCorruptTail):
        journal.append("flow.phase", {"node": "generation"})
    assert path.read_bytes() == before


def test_work_feed_rejects_unknown_event_kind(tmp_path):
    feed = WorkFeed(
        journal=EventJournal(tmp_path / "events.jsonl"),
        renderer=lambda _line: None,
    )
    with pytest.raises(ValueError, match="unknown work event"):
        feed.emit("provider.transcript", {"text": "must not persist"})


def test_supervisor_action_preserves_event_kind_and_action_kind(tmp_path):
    journal = EventJournal(tmp_path / "events.jsonl")
    feed = WorkFeed(journal=journal, renderer=lambda _line: None)

    feed.emit("supervisor.action", {
        "thread_id": "thread-1",
        "action_kind": "REDIRECT",
        "scope": "CURRENT_ARTICLE",
        "restart_depth": "GENERATION_FROM_PREFIX",
        "resume_node": "generation",
        "reason": "Follow the concrete contradiction.",
    })

    row = journal.latest()
    assert row["kind"] == "supervisor.action"
    assert row["action_kind"] == "REDIRECT"


def test_decision_trace_event_is_allowlisted_and_renders_controller_decision(tmp_path):
    rendered=[]
    journal=EventJournal(tmp_path/'events.jsonl')
    feed=WorkFeed(journal=journal,renderer=rendered.append,secret_values=lambda:['TRACE-SECRET'])

    feed.emit('decision.trace',{
        'boundary_id':'b'*64,
        'decision_boundary_id':'b'*64,
        'accepted_move_count':3,
        'uncovered_required_count':6,
        'committed_pressure':{'state':'NATURAL_STOP','confidence':0.9,'boundary_id':'b'*64},
        'edge':{'verdict':'STOP_BEFORE_CANDIDATE','confidence':0.96,'boundary_id':'b'*64},
        'candidate_sha256':'c'*64,
        'rejection_class':'STOP_BEFORE_CANDIDATE',
        'budgets':{'retry_count':4,'rollback_count':0},
        'raw_candidate':'must disappear TRACE-SECRET',
    })

    row=journal.latest()
    assert row['kind']=='decision.trace'
    assert row['uncovered_required_count']==6
    assert 'raw_candidate' not in row
    assert 'STOP_BEFORE_CANDIDATE' in rendered[-1]
    assert 'must disappear' not in rendered[-1]


def test_runtime_services_wire_one_pause_controller_and_work_feed(tmp_path, monkeypatch):
    monkeypatch.delenv("PANGRAM_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    services = RuntimeServices.from_config(RuntimeConfig.from_root(tmp_path))

    assert services.runner.pause_controller is services.pause_controller
    assert services.work_feed.journal is services.journal

    fake = RuntimeServices.for_tests(
        claude=object(),
        codex=object(),
        pangram=None,
        artifact_store=ArtifactStore(tmp_path / "test-artifacts"),
    )
    assert fake.runner.pause_controller is fake.pause_controller
    assert fake.work_feed.journal is None
