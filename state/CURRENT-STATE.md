# Pangram fixed-batch evidence branch current state

Updated: 2026-08-14

## Goal

Preserve exact detector evidence and the owner's no-click operating model with one reusable, budget-aware automatic runner. Ordinary repository changes must remain free; one paid run may begin only from a new immutable request that byte-binds one new fixed-batch spec on the exact evidence ref.

## Authority / baseline

- Evidence branch: `automation/pangram-fixed-batch`
- Active change base: `52ca9808e01ad3809b3ae41598f00981270fa437`
- That base includes the completed r29 detector result and lesson-review evidence.
- Canonical code/governance and semantic lesson disposition remain on `main`.
- The fail-closed default-branch registration stub remains on `main` at merge `81b5cd017e3be088c0638e527ce25f5df6a2f4e8`; it cannot run paid work.

## Completed

- All 14 historic task workflow blobs remain byte-preserved outside `.github/workflows`.
- Exactly one evidence workflow, `.github/workflows/pangram-paid-dispatch.yml`, owns deterministic verification and the guarded automatic detector job.
- `workflow_dispatch`, task-specific workflows, broad path-only paid triggers, and commit-message paid triggers are absent from the evidence workflow.
- Pull requests and ordinary pushes run tests/audit only.
- A paid job is eligible only when a push to `refs/heads/automation/pangram-fixed-batch` adds exactly two files: one immutable `requests/pangram/<experiment-id>.json` request and its new referenced spec.
- The request binds the exact spec bytes by SHA-256, carries the exact paid confirmation, and must match the request filename and fixed-batch experiment identity.
- Modified/deleted requests, bundled third changes, stale/pre-existing specs, symlink components, malformed/duplicate JSON keys, noncanonical results, missing audit/section identities, and digest mismatches fail closed before detector or secret access.
- Only `paid_request`, validated `spec_path`, and canonical `result_path` cross the job-output boundary.
- Read-only checkouts do not persist credentials. `contents: write` exists only on the detector job; write credentials are enabled immediately before the runner; `PANGRAM_API_KEY` is scoped only to that runner step.
- Remote Actions remain SHA-pinned; jobs remain serialized and timeout-bounded. Existing cache, task checkpoints, result identity, Git sync, and six-call section-ledger behavior are unchanged.
- Expected RED head/run: `66b432048d87e2897e53fd3ca9d3191bda63b415` / `31842241705`; failure was exactly the missing automatic validator, and detector skipped.
- First implementation run `31842514170` passed 87 tests and the audit, then exposed only the direct-script import boundary in preflight; detector skipped.
- Code-bearing green head `5d97cc65ccf7834c50a9de73f852cd4eaf72ab0b`, run `31842586682`, job `94902449059`: 87 tests passed, audit reported 0 errors and 5 declared warnings, preflight returned `paid_request=false`, and detector skipped.
- Restoring automation made 0 paid Pangram calls.

## Current checkpoint

- Review-ready PR #23 targets `automation/pangram-fixed-batch` from `codex/restore-automatic-paid-runs-2026-08-14`.
- Its code-bearing baseline is the green head above.
- Documentation/state descendants are non-paid changes; the exact PR head must still have a green verification run with `paid_request=false` and detector skipped before merge.

## Remaining

- Verify the exact latest PR #23 head and review the final diff.
- If the evidence base is still `52ca9808e01ad3809b3ae41598f00981270fa437`, merge PR #23.
- Confirm the post-merge evidence-branch run is green, `paid_request=false`, and detector skipped.
- When no detector or branch writer is active, stage r30 as exactly one new fixed-batch spec plus its immutable hash-bound request. That two-file push should automatically run one accounted batch without owner interaction.
- Record the r30 result and reconcile the editorial ledger before any installation decision.

## Blockers / unresolved

- Evidence-branch protection and hosted secret controls remain unverified; main issue #17 tracks owner/settings follow-up.
- The private-repository plan does not provide a ruleset.
- Until hosted protections are verified, write-capable collaborators remain inside the repository-secret/workflow trust boundary.
- Never stage a request while another detector task or evidence-branch writer is active.

## Evidence / artifacts

- Compliance report: `docs/EVIDENCE-WORKFLOW-COMPLIANCE-2026-08-14.md`
- Archive map: `docs/workflow-archive/automation-pangram-fixed-batch/README.md`
- Executable workflow: `.github/workflows/pangram-paid-dispatch.yml`
- Request/spec preflight: `scripts/validate_paid_push.py`
- Shared spec validation: `scripts/validate_paid_dispatch.py`
- Regression coverage: `tests/test_paid_push.py`, `tests/test_paid_dispatch.py`, `tests/test_paid_workflow_security.py`
- Automation-restoration PR: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/pull/23
- Hosted-control follow-up: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/issues/17

## Next safe action

If PR #23 is open, verify its exact head and merge only from the unchanged evidence base. If it is already merged, verify the merge push returned `paid_request=false` with detector skipped. Then, after confirming no active evidence run or writer, add only the new r30 spec and its byte-hash-bound immutable request; the workflow will take over automatically.

## Recovery rule

Before any paid request, fetch the current evidence head and active Actions runs. Recover exact task IDs, cache, call ledger, result state, request identity, and spec digest from Git; never infer them from chat and never repeat an ambiguous or already-paid POST.
