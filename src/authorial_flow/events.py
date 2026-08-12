from __future__ import annotations

from dataclasses import dataclass
import fcntl
import json
from pathlib import Path
import time


@dataclass(frozen=True)
class JournalRead:
    events: tuple[dict, ...]
    corrupt_line: int = 0
    corrupt_tail: str = ""


class EventJournalCorruptTail(RuntimeError):
    def __init__(self, line_number: int, raw: str) -> None:
        self.line_number = line_number
        self.raw = raw
        super().__init__(f"event journal has unreadable data at line {line_number}")


class EventJournal:
    def __init__(self, path: Path):
        self.path = path

    def append(self, kind: str, payload: dict) -> int:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+", encoding="utf-8") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                fh.seek(0)
                raw_rows = [line for line in fh.read().splitlines() if line.strip()]
                rows = []
                for line_number, raw in enumerate(raw_rows, 1):
                    try:
                        row = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        raise EventJournalCorruptTail(line_number, raw) from exc
                    if not isinstance(row, dict) or not isinstance(row.get("sequence"), int):
                        raise EventJournalCorruptTail(line_number, raw)
                    rows.append(row)
                seq = (rows[-1]["sequence"] if rows else 0) + 1
                fh.seek(0, 2)
                row = {
                    **payload,
                    "sequence": seq,
                    "time": time.time(),
                    "kind": kind,
                }
                fh.write(json.dumps(row, sort_keys=True) + "\n")
                fh.flush()
                os_fsync = getattr(__import__('os'), 'fsync')
                os_fsync(fh.fileno())
                return seq
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

    def read_since(self, sequence: int = 0) -> JournalRead:
        if not self.path.exists():
            return JournalRead(())
        rows = []
        with self.path.open("r", encoding="utf-8") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_SH)
            try:
                raw_rows = fh.read().splitlines()
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        for line_number, raw in enumerate(raw_rows, 1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                return JournalRead(tuple(rows), line_number, raw)
            if not isinstance(row, dict) or not isinstance(row.get("sequence"), int):
                return JournalRead(tuple(rows), line_number, raw)
            if row["sequence"] > sequence:
                rows.append(row)
        return JournalRead(tuple(rows))

    def latest(self) -> dict | None:
        read = self.read_since(0)
        return read.events[-1] if read.events else None
