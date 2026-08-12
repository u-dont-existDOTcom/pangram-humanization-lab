from authorial_flow.acceptance import ACCEPTANCE_CRITERIA, acceptance_summary


def test_acceptance_matrix_covers_every_approved_spec_criterion_once():
    assert [row.id for row in ACCEPTANCE_CRITERIA] == [f"AC-{i:02d}" for i in range(1, 17)]
    assert all(row.criterion.strip() and row.evidence.strip() for row in ACCEPTANCE_CRITERIA)
    assert {row.plane for row in ACCEPTANCE_CRITERIA} <= {"deterministic", "live", "owner"}


def test_acceptance_summary_does_not_claim_pending_live_or_owner_planes():
    summary = acceptance_summary()
    assert summary["total"] == 16
    assert summary["mapped"] == 16
    assert summary["live_or_owner_pending"] >= 1
from pathlib import Path
import re


def test_deterministic_acceptance_evidence_paths_exist():
    root = Path(__file__).resolve().parents[2]
    missing=[]
    for row in ACCEPTANCE_CRITERIA:
        if row.plane != 'deterministic':
            continue
        for token in re.findall(r'(tests/[A-Za-z0-9_./-]+\.py)', row.evidence):
            if not (root/token).is_file():
                missing.append((row.id, token))
    assert missing == []


def test_acceptance_documents_and_readme_are_release_ready():
    root = Path(__file__).resolve().parents[2]
    acceptance = root / "docs" / "acceptance-matrix.md"
    cutover = root / "docs" / "migration-cutover.md"
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert acceptance.is_file()
    assert cutover.is_file()
    acceptance_text = acceptance.read_text(encoding="utf-8")
    cutover_text = cutover.read_text(encoding="utf-8")
    for i in range(1, 17):
        assert f"AC-{i:02d}" in acceptance_text
    assert "legacy supervisor" in cutover_text.lower()
    assert "read-only" in cutover_text.lower()
    assert "deterministic" in readme.lower()
    assert "live" in readme.lower()
    assert "owner" in readme.lower()
