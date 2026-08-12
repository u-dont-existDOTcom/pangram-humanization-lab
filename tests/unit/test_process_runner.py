import os, sys
from pathlib import Path
import pytest
from authorial_flow.pause import OperationContext
from authorial_flow.process_runner import ProcessRunner, ProcessSpec
from authorial_flow.secrets import child_env, redact_argv


def test_child_env_strips_pangram_secret():
    env = {"PATH": os.environ["PATH"], "PANGRAM_API_KEY": "secret", "KEEP": "x"}
    got = child_env(env, {"PANGRAM_API_KEY"})
    assert "PANGRAM_API_KEY" not in got
    assert got["KEEP"] == "x"


def test_redact_argv_hides_inline_credentials():
    got = redact_argv(["cmd", "--token=abc", "key=xyz", "safe"])
    assert got == ["cmd", "***", "***", "safe"]


def test_silent_child_emits_heartbeats():
    beats = []
    runner = ProcessRunner(heartbeat_seconds=0.1, on_heartbeat=beats.append)
    result = runner.run(ProcessSpec(
        argv=[sys.executable, "tests/fixtures/silent_child.py", "0.35"],
        cwd=Path.cwd(), timeout_seconds=2,
    ))
    assert result.returncode == 0
    assert len(beats) >= 2
    assert result.stdout.endswith("finished\n")
    assert result.termination_reason == "exit"


def test_heartbeat_includes_safe_operation_context():
    beats = []
    runner = ProcessRunner(heartbeat_seconds=0.05, on_heartbeat=beats.append)
    runner.run(ProcessSpec(
        argv=[sys.executable, "tests/fixtures/silent_child.py", "0.12"],
        cwd=Path.cwd(),
        timeout_seconds=2,
        operation=OperationContext(
            node="generation",
            operation="model_call",
            provider="codex",
            model="gpt-5.6-sol",
            role="writer",
            cancelable=True,
        ),
    ))

    assert beats
    assert beats[0]["node"] == "generation"
    assert beats[0]["operation"] == "model_call"
    assert beats[0]["provider"] == "codex"
    assert beats[0]["model"] == "gpt-5.6-sol"
    assert beats[0]["role"] == "writer"


def test_timeout_terminates_child():
    runner = ProcessRunner(heartbeat_seconds=0.05)
    result = runner.run(ProcessSpec(
        argv=[sys.executable, "tests/fixtures/silent_child.py", "5"],
        cwd=Path.cwd(), timeout_seconds=0.15,
    ))
    assert result.termination_reason == "timeout"
    assert result.duration_seconds < 2


def test_runner_sends_stdin_to_child(tmp_path):
    child = tmp_path / "echo_stdin.py"
    child.write_text("import sys; print(sys.stdin.read())")
    runner = ProcessRunner(heartbeat_seconds=0.1)
    result = runner.run(ProcessSpec(
        argv=[sys.executable, str(child)], cwd=Path.cwd(), timeout_seconds=2,
        input_text="hello stdin",
    ))
    assert result.returncode == 0
    assert result.stdout == "hello stdin\n"
