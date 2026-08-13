from pathlib import Path

import pytest

from pangram_lab.call_budget import PangramCallLedger, SectionCallCapReached


def reserve(ledger, section_id="s1", measurement_key="m", words=100):
    return ledger.reserve_paid_call(
        section_id=section_id,
        model="pangram-4",
        version="4.0",
        measurement_key=measurement_key,
        text_sha256=(measurement_key.encode().hex() + "0" * 64)[:64],
        word_count=words,
    )


def test_six_calls_allowed_and_next_call_blocked(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit-1")
    for i in range(6):
        row = reserve(ledger, measurement_key=f"m{i}")
        assert row["paid_api_calls"] == i + 1
    with pytest.raises(SectionCallCapReached) as exc:
        reserve(ledger, measurement_key="m6")
    assert exc.value.audit_id == "audit-1"
    assert exc.value.section_id == "s1"
    assert ledger.section_summary("s1", "pangram-4", "4.0")["paid_api_calls"] == 6


def test_cap_is_independent_per_section(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit-1")
    for i in range(6):
        reserve(ledger, section_id="a", measurement_key=f"a{i}")
    assert reserve(ledger, section_id="b", measurement_key="b0")["paid_api_calls"] == 1


def test_call_count_persists_across_instances(tmp_path: Path):
    first = PangramCallLedger(tmp_path, "audit-1")
    reserve(first, measurement_key="m0")
    second = PangramCallLedger(tmp_path, "audit-1")
    assert second.section_summary("s1", "pangram-4", "4.0")["paid_api_calls"] == 1
    assert reserve(second, measurement_key="m1")["paid_api_calls"] == 2


def test_cache_resume_and_credit_estimates_are_recorded(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit-1")
    reserve(ledger, measurement_key="small", words=999)
    reserve(ledger, measurement_key="large", words=1001)
    ledger.record_cache_hit("s1", "pangram-4", "4.0", "cached", "a" * 64)
    ledger.record_pending_resume("s1", "pangram-4", "4.0", "pending", "b" * 64)
    summary = ledger.section_summary("s1", "pangram-4", "4.0")
    assert summary["paid_api_calls"] == 2
    assert summary["cache_hits"] == 1
    assert summary["pending_resumes"] == 1
    assert summary["estimated_credits"] == 3
    assert summary["estimated_cost_usd"] == pytest.approx(0.15)


def test_handoff_records_cap_reason_and_completed_results(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit-1")
    reserve(ledger, measurement_key="m0")
    path = ledger.write_handoff(
        "s1", "pangram-4", "4.0",
        completed_results=[{"id": "v0", "detector": {"prediction_short": "Mixed"}}],
    )
    assert path == tmp_path / "state" / "handoffs" / "pangram" / "audit-1-s1.json"
    import json
    obj = json.loads(path.read_text(encoding="utf-8"))
    assert obj["reason"] == "section_call_cap_reached"
    assert obj["section"]["paid_api_calls"] == 1
    assert obj["completed_results"][0]["id"] == "v0"
