from __future__ import annotations

import json

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.events import EventJournal
from authorial_flow.models.common import ModelResult
from authorial_flow.runtime import RuntimeServices
from authorial_flow.supervisor import (
    SupervisorSessionStore,
    ask_owner_supervisor,
    build_supervisor_snapshot,
    persist_supervisor_snapshot,
)


class CapturingSupervisor:
    def __init__(self):
        self.calls = []

    def call(self, call, runner, store):
        self.calls.append(call)
        parsed = {
            "answer": "The visible proposal is waiting for an owner decision.",
            "inferences": [],
            "uncertainties": [],
            "proposed_action": {
                "kind": "NONE",
                "reason": "",
                "instruction": "",
                "scope": "NONE",
                "restart_depth": "CURRENT_STAGE",
                "rollback_count": 0,
                "proposal_ref": "",
                "proposal_sha256": "",
            },
        }
        return ModelResult(
            provider="codex", role="owner_supervisor", request_id="safe-request",
            model="fake", cli_version="fake", parsed=parsed, text=json.dumps(parsed),
            stdout_ref="raw-stdout-ref", stderr_ref="raw-stderr-ref",
        )


def test_secret_fixture_and_raw_operational_material_never_reach_supervisor_surfaces(tmp_path, monkeypatch):
    secret = "PANGRAM-SECRET-FIXTURE-4927"
    article = "Complete article proposal the owner must still be able to judge."
    hidden_prompt = f"hidden prompt {secret}"
    partial_output = f"partial output {secret}"
    raw_stderr = f"provider error {secret}"
    monkeypatch.setenv("PANGRAM_API_KEY", secret)

    store = ArtifactStore(tmp_path / ".state" / "artifacts")
    journal = EventJournal(tmp_path / ".state" / "events.jsonl")
    terminal_lines = []
    codex = CapturingSupervisor()
    services = RuntimeServices.for_tests(
        claude=object(), codex=codex, pangram=None, artifact_store=store,
    )
    services.journal = journal
    services.work_feed.journal = journal
    services.work_feed.renderer = terminal_lines.append
    services.work_feed.secret_values = lambda: [secret]

    proposal_ref = store.put_text(article, "md", {"kind": "writer-proposal"}).sha256
    services.work_feed.emit("proposal.complete", {
        "node": "generation",
        "proposal_ref": proposal_ref,
        "proposal_sha256": proposal_ref,
        "text": article,
        "raw_prompt": hidden_prompt,
        "raw_stdout": partial_output,
        "raw_stderr": raw_stderr,
    })
    services.work_feed.emit("guard.result", {
        "node": "generation",
        "gate": "fidelity",
        "verdict": "FAIL",
        "reason": f"credential fixture {secret}",
        "proposal_ref": proposal_ref,
        "raw_prompt": hidden_prompt,
        "raw_stdout": partial_output,
        "raw_stderr": raw_stderr,
    })

    snapshot = build_supervisor_snapshot({
        "thread_id": "security-thread",
        "status": "supervisor_pause_requested",
        "supervisor_interrupted_node": "generation",
        "supervisor_resume_node": "generation",
        "raw_prompt": hidden_prompt,
        "raw_stdout": partial_output,
        "raw_stderr": raw_stderr,
        "PANGRAM_API_KEY": secret,
    }, journal=journal, store=store)
    snapshot_ref = persist_supervisor_snapshot(snapshot, store)

    sessions = SupervisorSessionStore(store.root.parent / "supervisor")
    session_ref = sessions.create("security-thread", "pause-1")
    sessions.append(session_ref, "user", "Why did the fidelity guard reject it?")
    reply = ask_owner_supervisor(snapshot, sessions.read(session_ref), services)
    sessions.append(session_ref, "assistant", reply.answer)

    terminal_text = "\n".join(terminal_lines)
    events_text = journal.path.read_text(encoding="utf-8")
    snapshot_text = store.find(snapshot_ref).path.read_text(encoding="utf-8")
    supervisor_prompt = codex.calls[-1].prompt
    session_path = sessions._resolve(session_ref)
    session_text = session_path.read_text(encoding="utf-8")

    for blob in (
        terminal_text, events_text, snapshot_text, supervisor_prompt, session_text,
    ):
        assert secret not in blob
        assert "hidden prompt" not in blob
        assert "partial output" not in blob
        assert "provider error" not in blob
    assert "[REDACTED]" in events_text or "[REDACTED]" in terminal_text
    for blob in (terminal_text, events_text, snapshot_text, supervisor_prompt):
        assert article in blob
