from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AcceptanceCriterion:
    id: str
    criterion: str
    plane: str
    evidence: str
    status: str = "mapped"


ACCEPTANCE_CRITERIA: tuple[AcceptanceCriterion, ...] = (
    AcceptanceCriterion("AC-01", "One command installs or updates the environment and resumes the correct thread.", "live", "INSTALL-AND-RUN.sh + clean-ZIP target-machine smoke", "target-machine-pending"),
    AcceptanceCriterion("AC-02", "Ctrl+C and process death resume from the last successful checkpoint.", "live", "tests/integration/test_graph_resume.py + target-machine interruption smoke", "dependency/live-pending"),
    AcceptanceCriterion("AC-03", "A silent child call produces a heartbeat at least every 10 seconds.", "deterministic", "tests/unit/test_process_runner.py; tests/live/test_live_smoke_unit.py"),
    AcceptanceCriterion("AC-04", "No stale regression evidence can cross-contaminate suites.", "deterministic", "tests/regression/test_regression_provenance.py"),
    AcceptanceCriterion("AC-05", "Repair agents cannot mutate protected source/owner files.", "deterministic", "tests/repair/test_worktree_protection.py; tests/integration/test_repair_resume.py"),
    AcceptanceCriterion("AC-06", "Owner regression examples are never visible to the writer.", "deterministic", "tests/regression/test_learning_isolation.py; tests/integration/test_runtime_dependencies.py"),
    AcceptanceCriterion("AC-07", "Source-order positive probes are diagnostic only.", "deterministic", "tests/regression/test_regression_provenance.py; tests/integration/test_runtime_dependencies.py"),
    AcceptanceCriterion("AC-08", "Pangram is skipped when hard local gates fail.", "deterministic", "tests/integration/test_detector_downstream.py"),
    AcceptanceCriterion("AC-09", "Pangram task IDs are checkpointed before polling and not duplicated on resume.", "live", "tests/unit/test_pangram.py + LangGraph target-machine resume smoke", "live-resume-pending"),
    AcceptanceCriterion("AC-10", "The first Pangram-Human candidate is frozen.", "deterministic", "tests/integration/test_detector_downstream.py; candidate lineage tests"),
    AcceptanceCriterion("AC-11", "Machine failures capture dereferenceable evidence, use isolated regression-first Codex repair, controller verification with at most one correction, verified promotion, and same-thread restart rather than user log collection.", "deterministic", "tests/repair/test_repair_pipeline.py; tests/repair/test_worktree_protection.py; tests/integration/test_repair_resume.py; tests/integration/test_cli.py"),
    AcceptanceCriterion("AC-12", "The only routine human interrupt is an authorial decision or credential action.", "owner", "failure taxonomy tests + first target-machine owner interrupt", "owner/live-pending"),
    AcceptanceCriterion("AC-13", "A bad-edge owner label is persisted and execution resumes automatically.", "owner", "tests/integration/test_owner_learning_resume.py + live owner interrupt/resume", "owner/live-pending"),
    AcceptanceCriterion("AC-14", "Internal artifacts are archived, not printed as nonexistent user upload paths.", "deterministic", "evidence-package tests; new runtime has no internal UPLOAD-this-file path"),
    AcceptanceCriterion("AC-15", "Final completion produces accepted text plus one reproducible evidence package.", "owner", "release/evidence package tests + first owner-accepted live thread", "owner/live-pending"),
    AcceptanceCriterion("AC-16", "All migrated known failure cases have explicit passing regression coverage, including Claude structured-role schema plumbing and autonomous repair restart semantics.", "deterministic", "tests/unit/test_model_adapters.py; owner-flow, semantic-relation, stale-provenance, provider-fallback, atomicity, repair, and packaging test suites"),
)


def acceptance_summary() -> dict[str, int]:
    pending = sum(1 for row in ACCEPTANCE_CRITERIA if row.status != "mapped")
    return {
        "total": len(ACCEPTANCE_CRITERIA),
        "mapped": len(ACCEPTANCE_CRITERIA),
        "live_or_owner_pending": pending,
    }
