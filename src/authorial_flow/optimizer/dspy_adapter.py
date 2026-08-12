from __future__ import annotations

from typing import Any

from ..artifacts import ArtifactStore
from ..models.common import ModelCall
from ..process_runner import ProcessRunner


class ClaudeCodexLM:
    """Thin optimizer-only bridge to the runtime's observable CLI adapters.

    This intentionally does not subclass a DSPy LM class.  The stable contract here is our
    provider bridge; DSPy-specific construction remains lazy in :func:`load_dspy_optimizer` so
    normal article runs do not import or require DSPy.
    """

    def __init__(
        self,
        *,
        claude: Any | None,
        codex: Any | None,
        runner: ProcessRunner,
        store: ArtifactStore,
        provider: str = "claude",
    ) -> None:
        if provider not in {"claude", "codex"}:
            raise ValueError("provider must be 'claude' or 'codex'")
        adapter = claude if provider == "claude" else codex
        if adapter is None:
            raise ValueError(f"{provider} adapter is required")
        self._provider = provider
        self._adapter = adapter
        self._runner = runner
        self._store = store

    def __repr__(self) -> str:
        return f"ClaudeCodexLM(provider={self._provider!r})"

    def __call__(self, prompt: str, **_: Any) -> str:
        call = ModelCall(prompt=str(prompt), schema=None, role="dspy_optimizer")
        result = self._adapter.call(call, self._runner, self._store)
        return result.text


def load_dspy_optimizer(*, metric: Any, auto: str = "medium") -> Any:
    """Construct GEPA only when the optional optimizer dependency is explicitly installed."""
    try:
        import dspy  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "DSPy optimizer support is optional. Install it with: "
            "pip install 'authorial-flow-graph[optimizer]'"
        ) from exc
    return dspy.GEPA(metric=metric, auto=auto)
