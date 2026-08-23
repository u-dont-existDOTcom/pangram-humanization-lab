import pytest

from pangram_lab.cache import PangramCache
from pangram_lab.pangram4 import PangramClient, PangramError


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.next_task = 1

    def request(self, method, url, headers=None, body=None):
        self.calls.append((method, url, body))
        if method == "POST":
            task_id = f"task-{self.next_task}"
            self.next_task += 1
            return {"status": 200, "json": {"task_id": task_id}}
        return {
            "status": 200,
            "json": {
                "stage": "STAGE_SUCCESS",
                "version": "4.0",
                "headline": "Human Written",
                "prediction_short": "Human",
                "fraction_ai": 0.0,
                "fraction_ai_assisted": 0.0,
                "fraction_human": 1.0,
                "text": "same text",
            },
        }


def _client(transport):
    return PangramClient(
        "secret",
        transport=transport,
        sleep=lambda _: None,
        sync=lambda _: None,
    )


def test_completed_same_text_is_reused_across_measurement_keys_without_post(tmp_path):
    transport = FakeTransport()
    cache = PangramCache(tmp_path)
    client = _client(transport)

    first = client.detect_cached("same text", cache, "experiment-A")
    assert first["prediction_short"] == "Human"
    assert [call[0] for call in transport.calls] == ["POST", "GET"]

    transport.calls.clear()
    second = client.detect_cached("same text", cache, "experiment-B")
    assert second == first
    assert transport.calls == []

    alias = cache.lookup("pangram-4", "4.0", "same text", "experiment-B")
    assert alias["status"] == "success"
    assert alias["task_id"] == "task-1"
    assert alias["source"] == "cross-key-cache:experiment-A"


def test_pending_same_text_under_other_key_blocks_new_paid_post(tmp_path):
    transport = FakeTransport()
    cache = PangramCache(tmp_path)
    cache.save_pending(
        "pangram-4",
        "4.0",
        "same text",
        "experiment-A",
        "existing-task",
        submitted_model="pangram-4",
    )
    client = _client(transport)

    with pytest.raises(PangramError, match="already pending"):
        client.detect_cached("same text", cache, "experiment-B")
    assert transport.calls == []


def test_ambiguous_same_text_under_other_key_blocks_new_paid_post(tmp_path):
    transport = FakeTransport()
    cache = PangramCache(tmp_path)
    cache.save_submit_ambiguous(
        "pangram-4",
        "4.0",
        "same text",
        "experiment-A",
        error="connection vanished after write",
    )
    client = _client(transport)

    with pytest.raises(PangramError, match="ambiguous prior submit"):
        client.detect_cached("same text", cache, "experiment-B")
    assert transport.calls == []


def test_explicit_research_repeat_can_bypass_cross_key_success(tmp_path):
    transport = FakeTransport()
    cache = PangramCache(tmp_path)
    client = _client(transport)

    client.detect_cached("same text", cache, "experiment-A")
    transport.calls.clear()

    result = client.detect_cached(
        "same text",
        cache,
        "experiment-repeat-1",
        allow_paid_repeat=True,
    )
    assert result["prediction_short"] == "Human"
    assert [call[0] for call in transport.calls] == ["POST", "GET"]
    repeat = cache.lookup("pangram-4", "4.0", "same text", "experiment-repeat-1")
    assert repeat["status"] == "success"
    assert repeat["task_id"] == "task-2"


def test_records_for_text_crosses_measurement_keys_but_not_text_hashes(tmp_path):
    cache = PangramCache(tmp_path)
    result = {
        "stage": "STAGE_SUCCESS",
        "version": "4.0",
        "headline": "Human Written",
        "prediction_short": "Human",
        "fraction_ai": 0.0,
        "fraction_ai_assisted": 0.0,
        "fraction_human": 1.0,
        "text": "same text",
    }
    cache.save_success("pangram-4", "4.0", "same text", "A", "t1", result)
    cache.save_success("pangram-4", "4.0", "same text", "B", "t2", result)
    cache.save_success("pangram-4", "4.0", "different text", "C", "t3", {**result, "text": "different text"})

    records = cache.records_for_text("pangram-4", "4.0", "same text")
    assert {record["measurement_key"] for record in records} == {"A", "B"}
