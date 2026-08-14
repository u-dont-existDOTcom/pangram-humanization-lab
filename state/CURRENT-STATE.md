# Pangram Humanization Lab current state

Updated: 2026-08-14

## Goal

Preserve the lab's exact detector evidence, editorial authority, and lesson-closeout architecture while making Codex/GitHub operation recoverable, least-privileged, and safe around paid detector work.

## Authority / current baselines

- Canonical branch: `main`; paid-route migration branch point `62495d48208136327c5e3da9bb8bc59e5f876d92`.
- Long-lived evidence branch: `automation/pangram-fixed-batch`; audited idle migration baseline `a413d6d872d31a7f39c2c0ec5b13f270c105cef2`.
- The main branch point includes the independently authorized Spiritual Bypassing r19-r29 lesson closeout; preserve it.
- Start lesson recovery at `state/LESSON-INDEX.md`; start repository documentation at `docs/INDEX.md`.
- Current owner instructions, exact repository evidence, and tests outrank historical chat.

## Completed

- Main compliance PR #16 merged as `8bf49ac0132c2fa55429d78d4ab79997081413a3`.
- Its post-merge repository-policy run `31776570388` and lesson-integrity run `31776570359` succeeded.
- Exact bootstrap, test, focused-test, repository-audit, lesson-audit, and interactive-run commands are recorded in `.github/codex-repository.json`.
- `state/CURRENT-STATE.md` is the single canonical recovery checkpoint.
- Workflow permissions are job-scoped where writes are required; remote Actions are pinned to full commit SHAs.
- Governance closeout receipts `L-6b3333a2c4-01`, `L-e96b341584-01`, and `L-a7e801f48a-01` are processed.
- Evidence PR #19 preserves all 14 historic workflow blobs byte-for-byte outside `.github/workflows` and replaces them with one evidence-ref-bound paid implementation.
- Evidence security head `e140e164828cf3128e1d8f6139fd5d1cd393d487` passed run `31778048629`: 78 tests, 0 audit errors, and the detector skipped.
- Evidence preflight rejects control-character identifiers, emits only validated path outputs, delays push credentials, and exposes the Pangram secret only to the final explicitly confirmed runner step.
- No manual dispatch or paid Pangram call was authorized or performed by compliance work.

## Current checkpoint

- Prerequisite PR #22 registers `.github/workflows/pangram-paid-dispatch.yml` on default branch `main`; GitHub otherwise cannot deliver `workflow_dispatch` to a non-default ref.
- Registration code head `928ea5ccf82360a80a20beac95d731d608ece5d6` passed lesson-integrity run `31778173435` with 62 tests and both lesson gates, plus repository-policy run `31778173455` with 0 errors and 5 warnings.
- The default-branch file has no secret, checkout, paid runner, push trigger, or pull-request trigger. It fails closed and tells the operator to select `automation/pangram-fixed-batch`.
- Documentation-binding commit `9060c6df0d3bff6af1c3365ef1d0139ee6361c0f` records the migration evidence.
- PR #19 remains open until #22 is reviewed and merged; this order avoids registering the historic unconfirmed evidence workflow path.

## Remaining

- Verify and independently review the exact final PR #22 head, then merge it to `main`.
- Update PR #19 durable paths/evidence, re-run its exact head, re-review the resolved findings, and merge it to `automation/pangram-fixed-batch`.
- Verify both post-merge branch runs without dispatching the paid route.
- Promote the transferable paid-workflow lifecycle, default-registration, output-file injection, and credential-delay lessons to `universal-dev-architecture`.
- Recheck hosted settings after repository-visible changes and update hardening-audit issue #17.

## Blockers / unresolved

- GitHub rulesets for this private repository returned a plan-limit error; `main` is verified unprotected.
- The connected integration could not read Actions default permissions, vulnerability alerts, secret scanning, push protection, or evidence-branch protection. These remain `unverified`.
- Code scanning is disabled.
- Until hosted protections are verified, write-capable collaborators remain part of the trust boundary for repository secrets and workflow changes.

## Evidence / artifacts

- Repository profile: `.github/codex-repository.json`
- Main compliance record: `docs/CODEX-GITHUB-COMPLIANCE-2026-08-14.md`
- Evidence compliance record in PR #19: `docs/EVIDENCE-WORKFLOW-COMPLIANCE-2026-08-14.md`
- Hosted-control follow-up: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/issues/17
- Main compliance PR: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/pull/16
- Dispatcher registration PR: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/pull/22
- Evidence workflow PR: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/pull/19

## Next safe action

If PR #22 is open, confirm its exact head has green lesson-integrity and repository-policy runs, obtain independent review, and merge it. Then refresh and re-review PR #19 before merging it. If both are merged, confirm the `main` and evidence-branch push runs are green and the evidence detector is skipped; then promote the universal lessons and continue the requested repository sequence.

## Recovery rule

Before any paid dispatch, fetch the current evidence head and active Actions runs. Recover exact task IDs, cache, call ledger, and result state from Git; never infer them from chat and never repeat an ambiguous or already-paid POST.
