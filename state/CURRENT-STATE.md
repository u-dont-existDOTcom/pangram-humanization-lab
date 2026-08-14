# Pangram fixed-batch evidence branch current state

Updated: 2026-08-14

## Goal

Preserve exact detector evidence while replacing historic accidental paid triggers with one manual, validated, serialized fixed-batch workflow.

## Authority / baseline

- Evidence branch: `automation/pangram-fixed-batch`
- Audited idle baseline: `a413d6d872d31a7f39c2c0ec5b13f270c105cef2`
- Latest baseline work includes the independently completed r29 result and lesson-review commits.
- Canonical code/governance and semantic lesson disposition remain on `main`.

## Completed

- All 14 baseline workflow blobs are preserved byte-for-byte outside `.github/workflows`.
- One executable workflow handles read-only push/PR verification and explicitly confirmed manual paid dispatch.
- Paid inputs are validated without detector access: exact confirmation, repository-relative spec, canonical output, audit ID, and section IDs.
- Remote Actions are SHA-pinned; jobs have explicit permissions, concurrency, and timeouts.
- The existing cache, task checkpoints, result identity, Git sync, and six-call section ledger remain unchanged.

## Current checkpoint

- PR #19 contains the evidence-workflow migration.
- Test-first red run `31776789465` failed exactly because `scripts.validate_paid_dispatch` did not yet exist.
- The migration itself makes no Pangram call; its push event is verification-only.

## Remaining

- Require the latest PR #19 push run to pass the full suite and repository audit with the detector job skipped.
- Review the archived-blob map and final workflow permissions.
- Merge PR #19 into `automation/pangram-fixed-batch`, then verify the evidence-branch push run also skips the detector.
- Promote transferable workflow-lifecycle and audit-parser lessons to `universal-dev-architecture`.

## Blockers / unresolved

- Evidence-branch protection and hosted secret controls remain unverified; main issue #17 tracks owner/settings follow-up.
- The repository plan does not provide a ruleset for this private repository.
- Never run or edit the manual workflow while another detector task or branch writer is active.

## Evidence / artifacts

- Compliance report: `docs/EVIDENCE-WORKFLOW-COMPLIANCE-2026-08-14.md`
- Archive map: `docs/workflow-archive/automation-pangram-fixed-batch/README.md`
- Executable workflow: `.github/workflows/pangram-fixed-batch.yml`
- Preflight implementation/tests: `scripts/validate_paid_dispatch.py`, `tests/test_paid_dispatch.py`
- Hosted-control follow-up: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/issues/17

## Next safe action

If PR #19 is open, confirm its latest push run has green verification and a skipped detector job, then merge. If it is merged, confirm the evidence-branch push run is green with the detector skipped; then return to `main` for universal lesson promotion and project sequencing.

## Recovery rule

Before any paid dispatch, fetch the current evidence head and active Actions runs. Recover exact task/cache/ledger state from Git; never infer it from chat and never repeat an ambiguous or already-paid POST.
