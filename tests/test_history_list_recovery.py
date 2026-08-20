from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from pangram_lab.history_list_recovery import (
    extract_history_list_candidates,
    paid_reservation_time_from_ledger,
    parse_timestamp,
    rank_by_target_time,
)


def test_extracts_nested_uuid_timestamp_records_and_ranks_by_target() -> None:
    payload = {
        "results": [
            {
                "uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
                "created_at": "2026-08-18T17:42:40Z",
                "title": "older",
            },
            {
                "id": "cccccccc-4444-5555-6666-dddddddddddd",
                "createdAt": "2026-08-18T17:43:04+00:00",
                "title": "nearest",
            },
        ]
    }
    candidates = extract_history_list_candidates(payload)
    assert len(candidates) == 2
    ranked = rank_by_target_time(
        candidates,
        datetime(2026, 8, 18, 17, 43, 0, tzinfo=timezone.utc),
    )
    assert ranked[0].uuid == "cccccccc-4444-5555-6666-dddddddddddd"
    proof = ranked[0].public_proof(
        datetime(2026, 8, 18, 17, 43, 0, tzinfo=timezone.utc)
    )
    assert proof["seconds_from_paid_reservation"] == 4.0
    assert "uuid" not in str(proof).casefold()


def test_parses_unix_seconds_and_milliseconds() -> None:
    seconds = 1_777_999_380
    assert parse_timestamp(seconds) == parse_timestamp(seconds * 1000)


def test_paid_reservation_time_requires_one_matching_event(tmp_path) -> None:
    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps(
            {
                "sections": {
                    "x": {
                        "events": [
                            {
                                "type": "paid_post_reserved",
                                "measurement_key": "gui:abc",
                                "recorded_at_utc": "2026-08-18T17:43:00.595741+00:00",
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    value = paid_reservation_time_from_ledger(ledger, measurement_key="gui:abc")
    assert value.isoformat() == "2026-08-18T17:43:00.595741+00:00"
    with pytest.raises(RuntimeError, match="exactly one paid reservation"):
        paid_reservation_time_from_ledger(ledger, measurement_key="gui:missing")
