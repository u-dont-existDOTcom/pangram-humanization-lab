# Pangram Codex + GitHub compliance implementation plan

Date: 2026-08-14  
Approved design: the owner's universal-baseline mandate plus Pangram-specific safety constraints.

## Goal

Make the repository recoverable from Git alone, enforce the portable repository-visible baseline in CI, remove excessive workflow privilege, and eliminate accidental paid-detector triggers on the long-lived evidence branch without changing detector behavior or spending credits.

## Workstream A — canonical `main`

1. Capture a test-first red run for the missing universal audit.
2. Vendor the canonical standard-library audit from `universal-dev-architecture` and add repository regression coverage.
3. Correct the workflow-policy false positive, pin the checkout dependency, add concurrency/timeout, and run the audit as the policy implementation.
4. Record exact bootstrap/test/audit commands; consolidate recovery into `state/CURRENT-STATE.md`.
5. Tighten lesson-workflow top-level permissions while retaining job-scoped writes.
6. Record hosted-setting observations and declared exceptions without guessing.
7. Run the full deterministic suite, repository audit, lesson range check, and lesson current-ref audit in GitHub Actions.
8. Make PR #16 review-ready and merge only after green evidence.

## Workstream B — `automation/pangram-fixed-batch`

1. Branch from the exact evidence head `88d225f36d6da8de9b8cbff8fa11b999d01d749a`.
2. Archive historic task-specific workflows outside `.github/workflows` without rewriting experiment evidence.
3. Replace them with one SHA-pinned, dispatch-only runner requiring an explicit paid-run confirmation and validated repository-relative spec/result paths.
4. Keep the detector secret scoped only to the paid step; add timeouts, concurrency, tests, and a no-paid-call default path.
5. Verify that the hardening push itself starts no paid detector job.
6. Merge through a PR targeting the evidence branch.

## Workstream C — transferable lesson

Promote the branch-lifecycle finding to `universal-dev-architecture` with source repository, immutable commit/path/hash, validation evidence, and limits. Record a `no-new-lesson` disposition in the Pangram detector-specific closeout system because the reusable governance lesson lives in the universal architecture repository.

## Safety invariants

- No Pangram API call is authorized by this compliance plan.
- Never retrieve, echo, or broaden access to the Pangram secret.
- Never discard exact evidence, task IDs, call ledgers, or branch provenance.
- Do not mix default-branch and evidence-branch histories in one PR.
- Do not claim a hosted control is enabled when the integration cannot verify it.
