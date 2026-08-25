from __future__ import annotations

from datetime import datetime, timezone

from pangram_lab.exact_history_recovery import candidate_window, find_exact_history_record


TARGET = datetime(2026, 8, 25, 14, 34, 16, tzinfo=timezone.utc)


def _history_list() -> dict[str, object]:
    return {
        "results": [
            {
                "uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
                "created_at": "2026-08-25T14:34:10Z",
            },
            {
                "uuid": "cccccccc-4444-5555-6666-dddddddddddd",
                "created_at": "2026-08-25T13:00:00Z",
            },
        ]
    }


def test_candidate_window_is_time_bounded_for_ambiguous_paid_recovery() -> None:
    candidates = candidate_window(_history_list(), target_time=TARGET)
    assert len(candidates) == 1
    assert candidates[0].distance_seconds(TARGET) == 6.0


def test_exact_recovery_accepts_only_the_time_bound_record_with_matching_text() -> None:
    exact_text = "one two three"
    payloads = {
        "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb": {
            "uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
            "prompt": exact_text,
            "model_id": "pangram-4",
        }
    }

    class Response:
        status = 200
        headers = {"content-type": "application/json"}

        def __init__(self, payload: object) -> None:
            self.payload = payload

        def json(self) -> object:
            return self.payload

    class Request:
        def get(self, url: str, *, timeout: int) -> Response:
            uuid = url.rstrip("/").rsplit("/", 1)[-1]
            return Response(payloads[uuid])

    class Context:
        request = Request()

    record, proof = find_exact_history_record(
        Context(),
        _history_list(),
        exact_text,
        target_time=TARGET,
    )
    assert record is not None
    assert record.input_sha256 == "6899ee404683a14e8c2a03149860df25d67d34d9cd4dae7350cbe91e4b3976be"
    assert proof["seconds_from_recovery_target"] == 6.0
    assert "uuid" not in str(proof).casefold()


def test_exact_recovery_does_not_accept_a_nearby_wrong_text_record() -> None:
    class Response:
        status = 200
        headers = {"content-type": "application/json"}

        def json(self) -> object:
            return {
                "uuid": "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb",
                "prompt": "different words entirely",
            }

    class Request:
        def get(self, url: str, *, timeout: int) -> Response:
            return Response()

    class Context:
        request = Request()

    record, proof = find_exact_history_record(
        Context(),
        _history_list(),
        "one two three",
        target_time=TARGET,
    )
    assert record is None
    assert proof["history_records_inspected"] == 1
