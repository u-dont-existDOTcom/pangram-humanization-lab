from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_TIMESTAMP_KEY_MARKERS = (
    "created_at",
    "createdat",
    "created",
    "creation",
    "timestamp",
    "submitted_at",
    "submittedat",
    "submitted",
)


@dataclass(frozen=True)
class HistoryListCandidate:
    uuid: str
    created_at_utc: datetime
    timestamp_key: str
    field_path: tuple[str, ...]

    def distance_seconds(self, target: datetime) -> float:
        return abs((self.created_at_utc - _as_utc(target)).total_seconds())

    def public_proof(self, target: datetime) -> dict[str, object]:
        return {
            "created_at_utc": self.created_at_utc.isoformat().replace("+00:00", "Z"),
            "seconds_from_paid_reservation": round(self.distance_seconds(target), 3),
            "timestamp_key": self.timestamp_key,
            "record_field_path": list(self.field_path),
        }


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if number > 10_000_000_000:  # milliseconds
            number /= 1000.0
        try:
            return datetime.fromtimestamp(number, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw.isdigit():
        return parse_timestamp(int(raw))
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return _as_utc(parsed)


def _iter_containers(
    value: Any,
    *,
    ancestry: tuple[str, ...] = (),
    depth: int = 0,
) -> Iterable[tuple[tuple[str, ...], dict[str, Any]]]:
    if depth > 10:
        return
    if isinstance(value, dict):
        yield ancestry, value
        for key, child in value.items():
            yield from _iter_containers(
                child,
                ancestry=(*ancestry, str(key)),
                depth=depth + 1,
            )
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _iter_containers(
                child,
                ancestry=(*ancestry, f"[{index}]"),
                depth=depth + 1,
            )


def _uuid_from_dict(item: dict[str, Any]) -> str | None:
    preferred = ("uuid", "history_uuid", "result_uuid", "scan_uuid", "id")
    for key in preferred:
        value = item.get(key)
        candidate = str(value or "").strip().lower()
        if _UUID_RE.fullmatch(candidate):
            return candidate
    for key, value in item.items():
        if "uuid" not in str(key).casefold():
            continue
        candidate = str(value or "").strip().lower()
        if _UUID_RE.fullmatch(candidate):
            return candidate
    return None


def _timestamp_from_dict(item: dict[str, Any]) -> tuple[str, datetime] | None:
    ranked: list[tuple[int, str, datetime]] = []
    for key, value in item.items():
        folded = str(key).replace("-", "_").casefold()
        parsed = parse_timestamp(value)
        if parsed is None:
            continue
        rank = 100
        for index, marker in enumerate(_TIMESTAMP_KEY_MARKERS):
            if folded == marker or marker in folded:
                rank = index
                break
        if rank < 100:
            ranked.append((rank, str(key), parsed))
    if not ranked:
        return None
    ranked.sort(key=lambda row: (row[0], row[1]))
    _, key, parsed = ranked[0]
    return key, parsed


def extract_history_list_candidates(payload: Any) -> tuple[HistoryListCandidate, ...]:
    candidates: list[HistoryListCandidate] = []
    seen: set[tuple[str, datetime]] = set()
    for field_path, item in _iter_containers(payload):
        uuid = _uuid_from_dict(item)
        stamped = _timestamp_from_dict(item)
        if uuid is None or stamped is None:
            continue
        timestamp_key, created_at = stamped
        identity = (uuid, created_at)
        if identity in seen:
            continue
        seen.add(identity)
        candidates.append(
            HistoryListCandidate(
                uuid=uuid,
                created_at_utc=created_at,
                timestamp_key=timestamp_key,
                field_path=field_path,
            )
        )
    candidates.sort(key=lambda item: item.created_at_utc, reverse=True)
    return tuple(candidates)


def rank_by_target_time(
    candidates: Iterable[HistoryListCandidate],
    target: datetime,
) -> tuple[HistoryListCandidate, ...]:
    target_utc = _as_utc(target)
    return tuple(
        sorted(
            candidates,
            key=lambda item: (item.distance_seconds(target_utc), -item.created_at_utc.timestamp()),
        )
    )


def paid_reservation_time_from_ledger(
    ledger_path: Path | str,
    *,
    measurement_key: str,
) -> datetime:
    path = Path(ledger_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    sections = payload.get("sections") or {}
    matches: list[datetime] = []
    for section in sections.values():
        for event in section.get("events") or []:
            if event.get("type") != "paid_post_reserved":
                continue
            if str(event.get("measurement_key")) != measurement_key:
                continue
            parsed = parse_timestamp(event.get("recorded_at_utc"))
            if parsed is not None:
                matches.append(parsed)
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one paid reservation for {measurement_key!r}; found {len(matches)}"
        )
    return matches[0]
