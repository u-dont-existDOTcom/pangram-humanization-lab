import pytest

from pangram_lab.cache import PangramCache
from pangram_lab.call_budget import PangramCallLedger, SectionCallCapReached
from pangram_lab.pangram4 import PangramClient


class Transport:
    def __init__(self):
        self.calls = []

    def request(self, method, url, headers=None, body=None):
        self.calls.append((method, url, body))
        if method == "POST":
            return {"status": 200, "json": {"task_id": "t1"}}
        return {"status": 200, "json": {"stage": "STAGE_SUCCESS", "version": "4.0", "headline": "Human Written", "prediction_short": "Human", "fraction_ai": 0.0, "fraction_ai_assisted": 0.0, "fraction_human": 1.0, "text": "abc"}}


def make_client(transport, synced=None):
    synced = synced if synced is not None else []
    return PangramClient("secret", transport=transport, sleep=lambda _: None, sync=lambda reason: synced.append(reason))


def test_new_post_counts_once_then_cache_hit_is_free(tmp_path):
    t = Transport(); cache = PangramCache(tmp_path); ledger = PangramCallLedger(tmp_path, "audit")
    client = make_client(t)
    client.detect_cached("abc", cache, "base", call_ledger=ledger, section_id="section")
    client.detect_cached("abc", cache, "base", call_ledger=ledger, section_id="section")
    summary = ledger.section_summary("section", "pangram-4", "4.0")
    assert summary["paid_api_calls"] == 1
    assert summary["cache_hits"] == 1
    assert [x[0] for x in t.calls] == ["POST", "GET"]


def test_pending_resume_is_free(tmp_path):
    t = Transport(); cache = PangramCache(tmp_path); ledger = PangramCallLedger(tmp_path, "audit")
    cache.save_pending("pangram-4", "4.0", "abc", "base", "existing", submitted_model="pangram-4")
    make_client(t).detect_cached("abc", cache, "base", call_ledger=ledger, section_id="section")
    summary = ledger.section_summary("section", "pangram-4", "4.0")
    assert summary["paid_api_calls"] == 0
    assert summary["pending_resumes"] == 1
    assert [x[0] for x in t.calls] == ["GET"]


class AmbiguousTransport:
    def __init__(self):
        self.calls = 0
    def request(self, method, url, headers=None, body=None):
        self.calls += 1
        raise OSError("connection lost")


def test_ambiguous_post_still_consumes_one_call(tmp_path):
    t = AmbiguousTransport(); cache = PangramCache(tmp_path); ledger = PangramCallLedger(tmp_path, "audit")
    with pytest.raises(Exception):
        make_client(t).detect_cached("abc", cache, "base", call_ledger=ledger, section_id="section")
    assert ledger.section_summary("section", "pangram-4", "4.0")["paid_api_calls"] == 1


def test_cap_blocks_post_before_transport(tmp_path):
    t = Transport(); cache = PangramCache(tmp_path); ledger = PangramCallLedger(tmp_path, "audit")
    for i in range(6):
        ledger.reserve_paid_call(section_id="section", model="pangram-4", version="4.0", measurement_key=f"old{i}", text_sha256=str(i) * 64, word_count=20)
    with pytest.raises(SectionCallCapReached):
        make_client(t).detect_cached("new text", cache, "new", call_ledger=ledger, section_id="section")
    assert t.calls == []


def test_reservation_is_synced_before_post(tmp_path):
    events = []
    ledger = PangramCallLedger(tmp_path, "audit")

    class CheckingTransport(Transport):
        def request(self, method, url, headers=None, body=None):
            if method == "POST":
                events.append(("post", ledger.section_summary("section", "pangram-4", "4.0")["paid_api_calls"]))
            return super().request(method, url, headers=headers, body=body)

    t = CheckingTransport(); cache = PangramCache(tmp_path); synced = []
    make_client(t, synced).detect_cached("abc", cache, "base", call_ledger=ledger, section_id="section")
    assert events[0] == ("post", 1)
    assert any("call reservation" in reason for reason in synced)
