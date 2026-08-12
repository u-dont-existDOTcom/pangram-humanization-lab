from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from .policy import PolicySnapshot, file_sha


REQUIRED_PROJECT_FILES = (
    "INPUT.md", "REQUIREMENTS.md", "AUTHOR_CONTEXT.md",
    "HUMAN-FLOW-GOLD.json", "SEMANTIC-RELATION-GOLD.json",
    "SOURCE-FLOW-POSITIVE.json", "PANGRAM-SOURCE-BASELINE.json",
)


@dataclass(frozen=True)
class ProjectInputs:
    path: Path
    hashes: dict[str, str]
    manifest_hash: str

    @staticmethod
    def write_manifest(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        missing = [name for name in REQUIRED_PROJECT_FILES if not (path / name).is_file()]
        if missing:
            raise FileNotFoundError("missing project files: " + ", ".join(missing))
        files = {
            p.relative_to(path).as_posix(): file_sha(p)
            for p in sorted(path.iterdir())
            if p.is_file() and p.name != "MANIFEST.json"
        }
        payload = {"format":"authorial-flow-project-inputs-v1", "files": files}
        manifest = path / "MANIFEST.json"
        manifest.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return manifest

    @classmethod
    def load(cls, path: Path) -> "ProjectInputs":
        path = path.resolve()
        manifest = path / "MANIFEST.json"
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        expected = payload.get("files", {})
        actual = {
            p.relative_to(path).as_posix(): file_sha(p)
            for p in sorted(path.iterdir())
            if p.is_file() and p.name != "MANIFEST.json"
        }
        if expected != actual:
            raise ValueError("project manifest/hash mismatch")
        missing = [name for name in REQUIRED_PROJECT_FILES if name not in actual]
        if missing:
            raise ValueError("project manifest missing required files: " + ", ".join(missing))
        return cls(path, actual, file_sha(manifest))

    def read(self, name: str) -> str:
        return (self.path / name).read_text(encoding="utf-8")


def compute_thread_id(
    inputs: ProjectInputs,
    policy: PolicySnapshot,
    graph_version: str,
    learning_version: str,
) -> str:
    # Diagnostic positives are intentionally excluded from authoritative lineage identity.
    authoritative_names = [
        "INPUT.md", "REQUIREMENTS.md", "AUTHOR_CONTEXT.md",
        "HUMAN-FLOW-GOLD.json", "SEMANTIC-RELATION-GOLD.json",
        "PANGRAM-SOURCE-BASELINE.json",
    ]
    if "SOURCE_METADATA.json" in inputs.hashes:
        authoritative_names.append("SOURCE_METADATA.json")
    payload = {
        "protected_inputs": {name: inputs.hashes[name] for name in authoritative_names},
        "policy_manifest": policy.manifest_hash,
        "graph_version": graph_version,
        "learning_version": learning_version,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode()).hexdigest()
