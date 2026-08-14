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
- Exactly one executable workflow handles read-only push/PR verification and explicitly confirmed manual paid dispatch.
- Paid inputs are validated without detector access: exact confirmation, repository-relative spec, canonical output, audit ID, and section IDs.
- Remote Actions are SHA-pinned; jobs have explicit permissions, concurrency, and timeouts.
- The existing cache, task checkpoints, result identity, Git sync, and six-call section ledger remain unchanged.
- Test-first RED run `31776789465` failed exactly because `scripts.validate_paid_dispatch` did not yet exist.
- Code-bearing remediation head `41411b1ec4eb7fb0b2c8fa1c2db416162df30905` passed run `31777325504`: 74 tests passed, the audit reported 0 errors and 5 warnings, and the detector job was skipped.
- The migration authorized and made 0 paid Pangram calls.

## Current checkpoint

- Draft PR #19 contains the evidence-workflow migration.
- Compliance-report binding commit: `6bd49c35532e668f999d65dcf3fab2d822dde899`.
- Report/current-state binding descendants are documentation-only; their exact latest PR head still requires a green verification run with the detector skipped before review.

## Remaining

- Verify the exact latest PR #19 head: full suite green, repository audit green, detector skipped.
- Independently review the archived-blob map, final workflow permissions, validator, tests, and durable handoff.
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

Confirm the exact PR #19 head has a successful verification run and a skipped detector job, then request independent review. After review findings are resolved and the exact reviewed head is green, merge. If already merged, confirm the evidence-branch push run is green with the detector skipped; then return to `main` for universal lesson promotion and project sequencing.

## Recovery rule

Before any paid dispatch, fetch the current evidence head and active Actions runs. Recover exact task/cache/ledger state from Git; never infer it from chat and never repeat an ambiguous or already-paid POST.
