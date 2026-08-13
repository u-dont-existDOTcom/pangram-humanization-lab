import json
from pathlib import Path

import pytest

from pangram_lab.call_budget import PangramCallLedger, SectionCallCapReached
from pangram_lab.fixed_batch import load_spec, run_batch


HUMAN = {"stage": "STAGE_SUCCESS", "version": "4.0", "headline": "Human Written", "prediction_short": "Human", "fraction_ai": 0.0, "fraction_ai_assisted": 0.0, "fraction_human": 1.0}


class AccountedClient:
    model = "pangram-4"
    expected_version = "4.0"

    def __init__(self, ledger):
        self.ledger = ledger
        self.calls = []

    def detect_cached(self, text, cache, measurement_key="base", *, section_id=None):
        self.calls.append((text, measurement_key, section_id))
        self.ledger.reserve_paid_call(section_id=section_id, model=self.model, version=self.expected_version, measurement_key=measurement_key, text_sha256=(measurement_key.encode().hex() + "0" * 64)[:64], word_count=len(text.split()))
        return dict(HUMAN)


class LegacyClient:
    def __init__(self): self.calls = []
    def detect_cached(self, text, cache, measurement_key="base"):
        self.calls.append((text, measurement_key)); return dict(HUMAN)


def test_load_spec_accepts_audit_and_requires_section_ids_for_new_audits(tmp_path: Path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps({"format": "pangram-fixed-batch-v1", "experiment_id": "exp", "audit_id": "audit", "variants": [{"id": "A", "section_id": "opening", "text": "one"}]}), encoding="utf-8")
    assert load_spec(good)["audit_id"] == "audit"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"format": "pangram-fixed-batch-v1", "experiment_id": "exp", "audit_id": "audit", "variants": [{"id": "A", "text": "one"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="section_id"):
        load_spec(bad)


def test_same_section_accumulates_and_result_contains_call_summary(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit")
    client = AccountedClient(ledger)
    spec = {"format": "pangram-fixed-batch-v1", "experiment_id": "exp", "audit_id": "audit", "variants": [{"id": "A", "section_id": "opening", "text": "first"}, {"id": "B", "section_id": "opening", "text": "second"}]}
    result = run_batch(spec, client=client, cache=object(), output_path=tmp_path / "out.json", call_ledger=ledger)
    assert [c[2] for c in client.calls] == ["opening", "opening"]
    assert result["results"][0]["section_id"] == "opening"
    section = result["call_accounting"]["sections"][0]
    assert section["paid_api_calls"] == 2
    assert section["paid_calls_to_human"] == 1
    assert section["estimated_credits_to_human"] == 1


def test_different_sections_have_independent_counts(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit"); client = AccountedClient(ledger)
    spec = {"format": "pangram-fixed-batch-v1", "experiment_id": "exp", "audit_id": "audit", "variants": [{"id": "A", "section_id": "a", "text": "first"}, {"id": "B", "section_id": "b", "text": "second"}]}
    result = run_batch(spec, client=client, cache=object(), output_path=tmp_path / "out.json", call_ledger=ledger)
    by_id = {x["section_id"]: x for x in result["call_accounting"]["sections"]}
    assert by_id["a"]["paid_api_calls"] == 1
    assert by_id["b"]["paid_api_calls"] == 1


def test_legacy_spec_and_client_keep_old_call_signature(tmp_path: Path):
    client = LegacyClient()
    spec = {"format": "pangram-fixed-batch-v1", "experiment_id": "exp", "variants": [{"id": "A", "text": "first"}]}
    result = run_batch(spec, client=client, cache=object(), output_path=tmp_path / "out.json")
    assert client.calls == [("first", "exp_A")]
    assert "section_id" not in result["results"][0]
    assert "call_accounting" not in result


def test_cap_failure_writes_handoff_before_propagating(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit")
    for i in range(6):
        ledger.reserve_paid_call(section_id="opening", model="pangram-4", version="4.0", measurement_key=f"old{i}", text_sha256=str(i) * 64, word_count=10)
    client = AccountedClient(ledger)
    spec = {"format": "pangram-fixed-batch-v1", "experiment_id": "exp", "audit_id": "audit", "variants": [{"id": "A", "section_id": "opening", "text": "next"}]}
    out = tmp_path / "out.json"
    with pytest.raises(SectionCallCapReached):
        run_batch(spec, client=client, cache=object(), output_path=out, call_ledger=ledger)
    handoff = tmp_path / "state" / "handoffs" / "pangram" / "audit-opening.json"
    assert handoff.exists()
    obj = json.loads(handoff.read_text(encoding="utf-8"))
    assert obj["reason"] == "section_call_cap_reached"
    assert obj["section"]["paid_api_calls"] == 6
