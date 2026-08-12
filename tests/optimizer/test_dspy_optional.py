from __future__ import annotations

import importlib.util
import sys
import tomllib
from pathlib import Path

import pytest

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.models.common import ModelResult
from authorial_flow.optimizer.dspy_adapter import ClaudeCodexLM, load_dspy_optimizer
from authorial_flow.process_runner import ProcessRunner


class FakeCLI:
    def __init__(self, provider: str = "claude") -> None:
        self.provider = provider
        self.calls = []

    def call(self, call, runner, store):
        self.calls.append(call)
        return ModelResult(
            provider=self.provider,
            role=call.role,
            request_id=call.request_id or "req",
            model="fake-model",
            cli_version="fake",
            parsed="answer",
            text="answer",
            stdout_ref="",
            stderr_ref="",
        )


def test_optimizer_extra_is_pinned_without_becoming_hot_path_dependency():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["optional-dependencies"]["optimizer"] == ["dspy==3.2.1"]
    assert "dspy" not in " ".join(data["project"]["dependencies"])


def test_normal_package_import_does_not_import_dspy():
    sys.modules.pop("dspy", None)
    import authorial_flow

    assert authorial_flow.GRAPH_VERSION
    assert "dspy" not in sys.modules


def test_missing_dspy_extra_has_targeted_install_message():
    if importlib.util.find_spec("dspy") is not None:
        pytest.skip("DSPy optimizer extra is installed in this environment")
    with pytest.raises(RuntimeError, match=r"pip install .*\[optimizer\]"):
        load_dspy_optimizer(metric=lambda *_: 1.0)


def test_claude_codex_lm_delegates_to_core_adapter_without_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("PANGRAM_API_KEY", "super-secret-detector-key")
    fake = FakeCLI("claude")
    runner = ProcessRunner(heartbeat_seconds=1)
    store = ArtifactStore(tmp_path / "artifacts")
    lm = ClaudeCodexLM(claude=fake, codex=None, runner=runner, store=store, provider="claude")

    out = lm("Explain the live pressure in one sentence.")

    assert out == "answer"
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call.role == "dspy_optimizer"
    assert call.prompt == "Explain the live pressure in one sentence."
    assert "super-secret-detector-key" not in repr(lm)
    assert "super-secret-detector-key" not in call.prompt


def test_claude_codex_lm_can_select_codex(tmp_path):
    fake = FakeCLI("codex")
    lm = ClaudeCodexLM(
        claude=None,
        codex=fake,
        runner=ProcessRunner(heartbeat_seconds=1),
        store=ArtifactStore(tmp_path / "artifacts"),
        provider="codex",
    )

    assert lm("Return a compact evaluator proposal.") == "answer"
    assert fake.calls[0].role == "dspy_optimizer"
