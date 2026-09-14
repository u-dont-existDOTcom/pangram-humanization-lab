from pathlib import Path
import json

import pytest

from pangram_lab.call_budget import PangramCallLedger, SectionCallCapReached


def reserve(ledger, section_id="s1", measurement_key="m", words=100, budget_scope="section"):
    return ledger.reserve_paid_call(
        section_id=section_id,
        model="pangram-4",
        version="4.0",
        measurement_key=measurement_key,
        text_sha256=(measurement_key.encode().hex() + "0" * 64)[:64],
        word_count=words,
        budget_scope=budget_scope,
    )


def test_six_calls_allowed_and_next_call_blocked_for_section_scope(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit-1")
    for i in range(6):
        row = reserve(ledger, measurement_key=f"m{i}")
        assert row["paid_api_calls"] == i + 1
        assert row["hard_cap_applies"] is True
        assert row["cap"] == 6
        assert row["review_threshold"] == 6
        assert row["owner_override_active"] is False
    with pytest.raises(SectionCallCapReached) as exc:
        reserve(ledger, measurement_key="m6")
    assert exc.value.audit_id == "audit-1"
    assert exc.value.section_id == "s1"
    assert ledger.section_summary("s1", "pangram-4", "4.0")["paid_api_calls"] == 6


def test_owner_override_reason_required_above_review_threshold(tmp_path: Path):
    with pytest.raises(ValueError, match="owner override reason"):
        PangramCallLedger(tmp_path, "audit-1", cap=10)


def test_owner_authorized_extension_keeps_same_audit_and_allows_four_more(tmp_path: Path):
    first = PangramCallLedger(tmp_path, "audit-1")
    for i in range(6):
        reserve(first, measurement_key=f"m{i}")

    reason = "Owner authorized four more discriminating R1/R2 calls after reviewing the first six."
    extended = PangramCallLedger(tmp_path, "audit-1", cap=10, override_reason=reason)
    for i in range(6, 10):
        row = reserve(extended, measurement_key=f"m{i}")
    assert row["paid_api_calls"] == 10
    assert row["review_threshold"] == 6
    assert row["cap"] == 10
    assert row["owner_override_active"] is True
    assert row["owner_override_reason"] == reason
    with pytest.raises(SectionCallCapReached):
        reserve(extended, measurement_key="m10")

    # Reopening the same audit with default arguments must not reset the durable
    # owner-authorized ceiling back to six.
    reopened = PangramCallLedger(tmp_path, "audit-1")
    summary = reopened.section_summary("s1", "pangram-4", "4.0")
    assert summary["paid_api_calls"] == 10
    assert summary["cap"] == 10
    assert summary["owner_override_active"] is True
    assert summary["owner_override_reason"] == reason

    state = json.loads((tmp_path / "state" / "pangram-call-ledgers" / "audit-1.json").read_text(encoding="utf-8"))
    assert state["section_call_review_threshold"] == 6
    assert state["section_call_cap"] == 10
    assert state["cap_overrides"][-1]["from_cap"] == 6
    assert state["cap_overrides"][-1]["to_cap"] == 10
    assert state["cap_overrides"][-1]["reason"] == reason


def test_aggregate_scope_is_accounted_but_not_section_capped(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit-1")
    for i in range(8):
        row = reserve(
            ledger,
            section_id="full-article-certification",
            measurement_key=f"doc{i}",
            budget_scope="aggregate",
        )
    assert row["paid_api_calls"] == 8
    assert row["budget_scope"] == "aggregate"
    assert row["hard_cap_applies"] is False
    assert row["cap"] is None


def test_cap_is_independent_per_section(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit-1")
    for i in range(6):
        reserve(ledger, section_id="a", measurement_key=f"a{i}")
    assert reserve(ledger, section_id="b", measurement_key="b0")["paid_api_calls"] == 1


def test_scope_cannot_be_changed_for_same_accounting_key(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit-1")
    reserve(ledger, section_id="a", measurement_key="a0", budget_scope="section")
    with pytest.raises(ValueError, match="budget_scope mismatch"):
        reserve(ledger, section_id="a", measurement_key="a1", budget_scope="aggregate")


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
        "s1",
        "pangram-4",
        "4.0",
        completed_results=[{"id": "v0", "detector": {"prediction_short": "Mixed"}}],
    )
    assert path == tmp_path / "state" / "handoffs" / "pangram" / "audit-1-s1.json"

    obj = json.loads(path.read_text(encoding="utf-8"))
    assert obj["reason"] == "section_call_cap_reached"
    assert obj["section"]["paid_api_calls"] == 1
    assert obj["completed_results"][0]["id"] == "v0"


def test_handoff_rejected_for_aggregate_scope(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit-1")
    reserve(
        ledger,
        section_id="article",
        measurement_key="doc0",
        budget_scope="aggregate",
    )
    with pytest.raises(ValueError, match="only valid for section-scoped"):
        ledger.write_handoff("article", "pangram-4", "4.0", completed_results=[])
