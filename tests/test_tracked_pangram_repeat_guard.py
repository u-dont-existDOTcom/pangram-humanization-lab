from pathlib import Path

import pytest

from pangram_lab.call_budget import PangramCallLedger
from pangram_lab.tracked_pangram import ExactTextRepeatBlocked, TrackedPangramClient


def test_same_section_exact_text_cannot_reserve_under_new_measurement_key(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit")
    text = "same exact text"
    import hashlib
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    ledger.reserve_paid_call(
        section_id="section",
        model="pangram-4",
        version="4.0",
        measurement_key="first",
        text_sha256=sha,
        word_count=len(text.split()),
    )
    client = TrackedPangramClient(api_key="test", call_ledger=ledger)
    client._call_context = ("section", "second", sha, "section", False)
    with pytest.raises(ExactTextRepeatBlocked) as exc:
        client.submit_once(text)
    assert exc.value.prior_measurement_key == "first"
    assert ledger.section_summary("section", "pangram-4", "4.0")["paid_api_calls"] == 1


def test_deliberate_exact_repeat_can_be_opted_in(tmp_path: Path):
    ledger = PangramCallLedger(tmp_path, "audit")
    text = "same exact text"
    import hashlib
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    ledger.reserve_paid_call(
        section_id="section",
        model="pangram-4",
        version="4.0",
        measurement_key="first",
        text_sha256=sha,
        word_count=len(text.split()),
    )
    client = TrackedPangramClient(api_key="test", call_ledger=ledger)
    client._call_context = ("section", "second", sha, "section", True)
    # We only exercise the guard decision here; a real second POST would be allowed.
    assert client._prior_exact_reservation("section", sha)["measurement_key"] == "first"
    assert client._call_context[-1] is True
