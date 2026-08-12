from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from authorial_flow.runtime import _reconcile_move_coverage
from authorial_flow.supervisor import CoverageReconciliationBlocked


def test_coverage_reconciliation_uses_independent_mapping_and_check_calls(tmp_path):
    from test_runtime_dependencies import _fake_services

    root = Path(__file__).resolve().parents[2]
    services = _fake_services(tmp_path)
    move = "One preserved move."
    unit = {
        "id": "u1",
        "text": "One represented obligation.",
        "authority": "OWNER_GROUNDED",
        "exact_lock": False,
        "disposition": "unresolved",
        "reason": "owner",
    }
    unit_ref = services.artifact_store.put_text(json.dumps(unit), "json", {"kind": "authority-unit"}).sha256
    services.codex.responses["coverage_reconciliation"] = {
        "moves": [{
            "index": 0,
            "move_sha256": sha256(move.encode("utf-8")).hexdigest(),
            "covered_unit_ids": ["u1"],
        }],
    }
    services.codex.responses["coverage_reconciliation_check"] = {
        "verdict": "PASS",
        "reason": "The mapping is exact.",
    }

    rows = _reconcile_move_coverage(
        {"source_ref": services.artifact_store.put_text("source", "md", {}).sha256,
         "atom_refs": [unit_ref], "atom_coverage": {"u1": True}, "accepted_moves": [move]},
        services,
        root,
    )

    assert rows["moves"][0]["covered_unit_ids"] == ["u1"]
    assert [call.role for call in services.codex.calls[-2:]] == [
        "coverage_reconciliation", "coverage_reconciliation_check",
    ]


def test_coverage_reconciliation_fails_closed_before_check_on_bad_hash(tmp_path):
    from test_runtime_dependencies import _fake_services

    root = Path(__file__).resolve().parents[2]
    services = _fake_services(tmp_path)
    services.codex.responses["coverage_reconciliation"] = {
        "moves": [{"index": 0, "move_sha256": "0" * 64, "covered_unit_ids": []}],
    }

    with pytest.raises(CoverageReconciliationBlocked):
        _reconcile_move_coverage(
            {"source_ref": services.artifact_store.put_text("source", "md", {}).sha256,
             "atom_refs": [], "atom_coverage": {}, "accepted_moves": ["move"]},
            services,
            root,
        )

    assert [call.role for call in services.codex.calls].count("coverage_reconciliation_check") == 0
