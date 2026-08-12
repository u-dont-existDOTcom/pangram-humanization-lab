from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    root: Path
    state_dir: Path
    heartbeat_seconds: float = 10
    model_timeout_seconds: int = 1800
    pangram_timeout_seconds: int = 900
    writer_attempts: int = 4
    max_moves: int = 30
    max_rollbacks: int = 8
    repair_rounds: int = 5
    plan_revisions: int = 2
    implementation_fix_attempts: int = 1
    optimizer_rounds: int = 6

    @classmethod
    def from_root(cls, root: Path) -> "RuntimeConfig":
        root = root.resolve()
        return cls(root=root, state_dir=root / ".state")

    @property
    def artifact_dir(self) -> Path:
        return self.state_dir / "artifacts"

    @property
    def event_path(self) -> Path:
        return self.state_dir / "events.jsonl"

    @property
    def checkpoint_db(self) -> Path:
        return self.state_dir / "checkpoints.sqlite"
