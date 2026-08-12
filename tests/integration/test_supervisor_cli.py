from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.cli import _continue_with_supervision, _invoke_with_pause_signal
from authorial_flow.models.common import ModelResult
from authorial_flow.runtime import RuntimeServices
from authorial_flow.supervisor import SupervisorSessionStore, SupervisorSnapshot


class SupervisorAdapter:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def call(self, call, runner, store):
        self.calls.append(call)
        response = next(self.responses)
        if isinstance(response, BaseException):
            raise response
        return ModelResult(
            provider="codex",
            role=call.role,
            request_id="supervisor-request",
            model="fake-codex",
            cli_version="fake",
            parsed=response,
            text=json.dumps(response),
            stdout_ref="",
            stderr_ref="",
        )


def _reply(kind="NONE", **overrides):
    action = {
        "kind": kind,
        "reason": "",
        "instruction": "",
        "scope": "NONE",
        "restart_depth": "CURRENT_STAGE",
        "rollback_count": 0,
        "proposal_ref": "",
        "proposal_sha256": "",
        **overrides,
    }
    return {
        "answer": "The writer is retrying after a fidelity failure.",
        "inferences": [],
        "uncertainties": [],
        "proposed_action": action,
    }


def _fixture(tmp_path: Path, responses):
    store = ArtifactStore(tmp_path / ".state" / "artifacts")
    codex = SupervisorAdapter(responses)
    services = RuntimeServices.for_tests(
        claude=object(),
        codex=codex,
        pangram=None,
        artifact_store=store,
    )
    snapshot = SupervisorSnapshot(
        thread_id="thread-1",
        interrupted_node="generation",
        resume_node="generation",
        phase="generation",
        status="supervisor_pause_requested",
        accepted_moves=["Kept move."],
        current_passage="Kept move.",
    )
    sessions = SupervisorSessionStore(store.root.parent / "supervisor")
    session_ref = sessions.create("thread-1", "pause-1")
    paused = {
        "status": "supervisor_pause_requested",
        "__interrupt__": [SimpleNamespace(value={
            "kind": "SUPERVISOR",
            "snapshot_ref": "snapshot-ref",
            "session_ref": session_ref,
            "snapshot": snapshot.model_dump(mode="json"),
            "validation_error": "",
        })],
    }
    return services, codex, sessions, session_ref, paused


class FakeApp:
    def __init__(self, results):
        self.results = iter(results)
        self.calls = []

    def invoke(self, initial, graph_config):
        self.calls.append(SimpleNamespace(initial=initial, graph_config=graph_config))
        return next(self.results)


def test_question_does_not_resume_graph_until_action_is_confirmed(tmp_path, monkeypatch):
    services, _codex, sessions, session_ref, paused = _fixture(tmp_path, [
        _reply(),
        _reply(
            "REDIRECT",
            reason="Follow the owner's correction.",
            instruction="Develop the concrete contradiction.",
            scope="CURRENT_ARTICLE",
            restart_depth="GENERATION_FROM_PREFIX",
        ),
    ])
    answers = iter([
        "Why is it rewriting this paragraph?",
        "Redirect it toward the contradiction.",
        "y",
    ])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    app = FakeApp([paused, {"status": "continue_generation", "accepted_moves": ["Kept move."]}])

    result = _continue_with_supervision(
        app,
        {"configurable": {"thread_id": "thread-1"}},
        None,
        services,
        interactive=True,
    )

    assert result["status"] == "continue_generation"
    assert len(app.calls) == 2
    assert app.calls[0].initial is None
    assert app.calls[1].initial.resume["kind"] == "REDIRECT"
    assert app.calls[1].initial.resume["instruction"] == "Develop the concrete contradiction."
    assert [row["role"] for row in sessions.read(session_ref)] == [
        "user", "assistant", "user", "assistant",
    ]


def test_leave_keeps_interrupt_pending_and_reopen_loads_same_session(tmp_path, monkeypatch, capsys):
    services, _codex, sessions, session_ref, paused = _fixture(tmp_path, [])
    sessions.append(session_ref, "user", "Earlier question")
    sessions.append(session_ref, "assistant", "Earlier answer")
    monkeypatch.setattr("builtins.input", lambda _prompt="": "leave")
    app = FakeApp([paused])

    result = _continue_with_supervision(
        app,
        {"configurable": {"thread_id": "thread-1"}},
        None,
        services,
        interactive=True,
    )

    assert result is paused
    assert len(app.calls) == 1
    assert [row["text"] for row in sessions.read(session_ref)] == ["Earlier question", "Earlier answer"]
    assert "remains paused" in capsys.readouterr().out.lower()


def test_ctrl_c_during_supervisor_answer_keeps_graph_paused(tmp_path, monkeypatch, capsys):
    services, _codex, _sessions, _session_ref, paused = _fixture(tmp_path, [KeyboardInterrupt()])
    answers = iter(["What is happening?", "leave"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    app = FakeApp([paused])

    result = _continue_with_supervision(
        app,
        {"configurable": {"thread_id": "thread-1"}},
        None,
        services,
        interactive=True,
    )

    assert result is paused
    assert len(app.calls) == 1
    assert "still paused" in capsys.readouterr().err.lower()


def test_noninteractive_supervisor_interrupt_never_invents_an_action(tmp_path, capsys):
    services, _codex, _sessions, _session_ref, paused = _fixture(tmp_path, [])
    app = FakeApp([paused])

    result = _continue_with_supervision(
        app,
        {"configurable": {"thread_id": "thread-1"}},
        None,
        services,
        interactive=False,
    )

    assert result is paused
    assert len(app.calls) == 1
    assert "remains paused" in capsys.readouterr().out.lower()


def test_machine_invocation_installs_pause_handler_only_around_app_invoke(tmp_path, monkeypatch):
    services, _codex, _sessions, _session_ref, _paused = _fixture(tmp_path, [])
    entered = []

    class Context:
        def __enter__(self):
            entered.append("enter")

        def __exit__(self, *_args):
            entered.append("exit")

    monkeypatch.setattr("authorial_flow.cli.temporary_sigint_pause", lambda controller, callback: Context())
    app = FakeApp([{"status": "ok"}])

    result = _invoke_with_pause_signal(
        app,
        None,
        {"configurable": {"thread_id": "thread-1"}},
        services,
    )

    assert result == {"status": "ok"}
    assert entered == ["enter", "exit"]
