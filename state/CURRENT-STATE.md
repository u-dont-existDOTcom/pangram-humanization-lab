# Pangram fixed-batch evidence branch current state

Updated: 2026-08-14

## Goal

Preserve exact detector evidence while replacing historic accidental paid triggers with one default-registered, evidence-ref-bound, validated, serialized fixed-batch workflow.

## Authority / baseline

- Evidence branch: `automation/pangram-fixed-batch`
- Audited idle baseline: `a413d6d872d31a7f39c2c0ec5b13f270c105cef2`
- Latest baseline work includes the independently completed r29 result and lesson-review commits.
- Canonical code/governance and semantic lesson disposition remain on `main`.
- Default-branch registration merged to `main` as `81b5cd017e3be088c0638e527ce25f5df6a2f4e8`.

## Completed

- All 14 baseline workflow blobs are preserved byte-for-byte outside `.github/workflows`.
- Exactly one executable evidence workflow, `.github/workflows/pangram-paid-dispatch.yml`, handles read-only push/PR verification and explicitly confirmed manual paid dispatch.
- The same path exists on default branch as a snapshot-locked, no-permission, no-secret, no-checkout stub; this satisfies GitHub's default-branch registration rule without running paid work on `main`.
- The paid job is eligible only for `workflow_dispatch` on `refs/heads/automation/pangram-fixed-batch`.
- Paid inputs are validated without detector access: exact confirmation, repository-relative spec, canonical output, audit ID, and section IDs.
- Audit/section control characters are rejected; only validated spec/result paths are emitted to `$GITHUB_OUTPUT`.
- Read-only checkouts do not persist credentials. Write credentials are enabled immediately before the final runner step, and `PANGRAM_API_KEY` is scoped only to that step.
- Remote Actions are SHA-pinned; jobs have explicit permissions, concurrency, and timeouts.
- Existing cache, task checkpoints, result identity, Git sync, and six-call section ledger behavior remain unchanged.
- Original validator RED run `31776789465` failed exactly because the module did not exist.
- Security-review RED run `31777929822` failed exactly four new regressions while 74 unrelated tests passed; detector skipped.
- Security-remediation head `e140e164828cf3128e1d8f6139fd5d1cd393d487` passed run `31778048629`: 78 tests, 0 audit errors, 5 declared warnings, and detector skipped.
- Main registration reviewed head `092367b72a819b524575fadd6118513cc7bf7c3c` passed runs `31778554058` and `31778554047` before merge.
- Compliance work authorized and made 0 manual dispatches and 0 paid Pangram calls.

## Current checkpoint

- Review-ready PR #19 contains the evidence-workflow migration.
- The original independent review findings—unregistered non-default dispatch, output-file injection, and stale draft wording—are resolved in code and durable evidence.
- Compliance-report binding commit: `865b448c4cc51f7a0cebcb5b6400df803d748099`.
- Report/current-state binding descendants are documentation-only; the exact latest PR head requires a green verification run with paid preflight and detector skipped before focused re-review.

## Remaining

- Verify the exact latest PR #19 head: 78 tests, repository audit green, paid preflight skipped, detector skipped.
- Obtain focused independent re-review of the resolved findings and final durable handoff.
- Merge PR #19 into `automation/pangram-fixed-batch`, then verify the evidence-branch push run also skips the detector.
- Promote transferable workflow-lifecycle, default-registration, output-injection, credential-delay, and audit-parser lessons to `universal-dev-architecture`.

## Blockers / unresolved

- Evidence-branch protection and hosted secret controls remain unverified; main issue #17 tracks owner/settings follow-up.
- The repository plan does not provide a ruleset for this private repository.
- Until hosted protections are verified, write-capable collaborators remain part of the repository-secret/workflow trust boundary.
- Never run or edit the manual workflow while another detector task or branch writer is active.

## Evidence / artifacts

- Compliance report: `docs/EVIDENCE-WORKFLOW-COMPLIANCE-2026-08-14.md`
- Archive map: `docs/workflow-archive/automation-pangram-fixed-batch/README.md`
- Executable workflow: `.github/workflows/pangram-paid-dispatch.yml`
- Preflight implementation/tests: `scripts/validate_paid_dispatch.py`, `tests/test_paid_dispatch.py`, `tests/test_paid_workflow_security.py`
- Default registration PR: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/pull/22
- Hosted-control follow-up: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/issues/17

## Next safe action

Confirm the exact PR #19 head has a successful verification run with paid preflight and detector skipped, then obtain focused re-review. If review is clean and the evidence base remains `a413d6d872d31a7f39c2c0ec5b13f270c105cef2`, merge. If already merged, confirm the evidence-branch push run is green with detector skipped; then return to `main` for universal lesson promotion and the requested repository sequence.

## Recovery rule

Before any paid dispatch, fetch the current evidence head and active Actions runs. Recover exact task IDs, cache, call ledger, and result state from Git; never infer them from chat and never repeat an ambiguous or already-paid POST.
