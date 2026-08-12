from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class PolicySnapshot:
    path: Path
    files: dict[str, str]
    manifest_hash: str

    @staticmethod
    def write_manifest(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        files = {
            p.relative_to(path).as_posix(): file_sha(p)
            for p in sorted(path.rglob("*"))
            if p.is_file() and p.name != "MANIFEST.json"
        }
        payload = {"format": "authorial-flow-policy-snapshot-v1", "files": files}
        manifest = path / "MANIFEST.json"
        manifest.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return manifest

    @classmethod
    def load(cls, path: Path) -> "PolicySnapshot":
        path = path.resolve()
        manifest = path / "MANIFEST.json"
        if not manifest.exists():
            raise FileNotFoundError(manifest)
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        expected = payload.get("files", {})
        actual = {
            p.relative_to(path).as_posix(): file_sha(p)
            for p in sorted(path.rglob("*"))
            if p.is_file() and p.name != "MANIFEST.json"
        }
        if expected != actual:
            raise ValueError("policy manifest/hash mismatch")
        return cls(path, actual, file_sha(manifest))
