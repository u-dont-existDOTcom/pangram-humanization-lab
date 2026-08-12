from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import time


@dataclass(frozen=True)
class ArtifactRef:
    sha256: str
    path: Path
    metadata_path: Path

    def as_state_ref(self) -> str:
        return self.sha256


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root

    def put_bytes(self, data: bytes, ext: str, metadata: dict) -> ArtifactRef:
        digest = sha256(data).hexdigest()
        bucket = self.root / digest[:2]
        bucket.mkdir(parents=True, exist_ok=True)
        suffix = ext.lstrip(".") or "bin"
        path = bucket / f"{digest}.{suffix}"
        meta = bucket / f"{digest}.meta.json"
        if not path.exists():
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, path)
        if not meta.exists():
            payload = {"sha256": digest, "created_at": time.time(), **metadata}
            tmp = meta.with_suffix(meta.suffix + ".tmp")
            tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            os.replace(tmp, meta)
        return ArtifactRef(digest, path, meta)

    def put_text(self, text: str, ext: str = "txt", metadata: dict | None = None) -> ArtifactRef:
        return self.put_bytes(text.encode("utf-8"), ext, metadata or {})

    def find(self, digest: str) -> ArtifactRef | None:
        bucket = self.root / digest[:2]
        if not bucket.exists():
            return None
        data_files = [p for p in bucket.glob(f"{digest}.*") if not p.name.endswith(".meta.json")]
        meta = bucket / f"{digest}.meta.json"
        if len(data_files) != 1 or not meta.exists():
            return None
        return ArtifactRef(digest, data_files[0], meta)
