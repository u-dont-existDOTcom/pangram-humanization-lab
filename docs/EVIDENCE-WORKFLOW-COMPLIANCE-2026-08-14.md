# Evidence-workflow compliance record — 2026-08-14

## Baseline and concurrency check

- Repository: `u-dont-existDOTcom/pangram-humanization-lab`
- Original migration baseline: `a413d6d872d31a7f39c2c0ec5b13f270c105cef2`
- No-click restoration base: `52ca9808e01ad3809b3ae41598f00981270fa437`
- Active, queued, or pending evidence-branch Actions at restoration branch time: none
- Paid Pangram calls made by either workflow-governance change: `0`

The restoration base includes the independently completed r29 result and lesson-review commits. Neither governance change altered detector results, cache, call ledgers, or task checkpoints.

## Original finding

Fourteen workflow files were executable on the long-lived branch. Historic task-specific workflows used floating Action tags, broad or missing lifecycle controls, and paid detector jobs reachable from ordinary push-path changes. The general runner also retained push/commit-message routing.

The first remediation consolidated those files and temporarily made paid work manual-only. The owner subsequently rejected button-driven dispatch because the operating requirement is automation. PR #23 therefore supersedes only that manual entry method while preserving the consolidation and security boundaries.

## Current remediation

- Preserve all 14 historic workflow blobs under the non-executable archive with their original Git identities.
- Keep one evidence implementation at `.github/workflows/pangram-paid-dispatch.yml`. The default-branch file remains an inert, snapshot-locked refusal stub and is not an execution route.
- Run the complete deterministic suite and repository audit on pushes and pull requests with read-only permissions.
- Remove `workflow_dispatch` from the evidence implementation.
- Permit the detector only on a push to the exact `automation/pangram-fixed-batch` ref when preflight returns `paid_request=true`.
- Define one immutable request per experiment at `requests/pangram/<experiment-id>.json`.
- Require a paid push to add exactly the request and its referenced new spec, with no bundled third change.
- Bind the request to the exact spec bytes by SHA-256 and to the same request filename/fixed-batch experiment identity.
- Require the exact `RUN_PAID_PANGRAM_FIXED_BATCH` confirmation, canonical result path, non-empty `audit_id`, and a `section_id` for every variant.
- Reject request modification/deletion, duplicate or surplus request keys, control characters, malformed paths, symlink components, digest mismatches, stale specs, and identity mismatches before secret access.
- Emit only the boolean gate plus validated spec/result paths across `$GITHUB_OUTPUT`.
- Serialize runs, bound jobs with timeouts, and pin all remote Actions to full SHAs.
- Keep `contents: write`, persisted write credentials, and `PANGRAM_API_KEY` out of verification and available only at the final detector boundary.
- Leave runner resumption, cache, task checkpoints, Git synchronization, result registration, and six-call section accounting unchanged.

This restores the old user experience—stage the candidate and let automation take over—without restoring task-specific workflow files or commit-message paid triggers.

## Verification contract

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python scripts/audit_codex_github.py --root . --fail-on error
python scripts/validate_paid_push.py --base <before-sha> --head <after-sha>
```

For a code/documentation push, verification must succeed, preflight must return `paid_request=false`, and detector must skip. For an authorized two-file request/spec push, the same deterministic gate must succeed before the exact-ref-bound detector becomes eligible. Result/checkpoint commits do not touch the immutable request, so they cannot retrigger paid work.

## Exact restoration receipts

- Test-first head: `66b432048d87e2897e53fd3ca9d3191bda63b415`.
- Expected RED run: `31842241705`, verify job `94901405998`; collection failed exactly because `scripts.validate_paid_push` did not exist, and detector skipped.
- First implementation head/run: `53d9bb0d0fadc8c89373a9e2b32959e7d695e04a` / `31842514170`; 87 tests and the audit passed, then direct CLI execution exposed the package-import boundary in preflight, and detector skipped.
- Code-bearing green head: `5d97cc65ccf7834c50a9de73f852cd4eaf72ab0b`.
- Green run/job: `31842586682` / `94902449059`; 87 tests passed, the audit reported 0 errors and 5 declared warnings, preflight returned `paid_request=false`, and detector skipped.
- Secret boundary: the exact secret expression occurs only in the final runner step; the detector alone receives `contents: write`.
- Trigger boundary: the evidence workflow contains no `workflow_dispatch`, task-specific path trigger, or commit-message routing.
- Paid Pangram calls made by restoration: `0`.

Documentation/state descendants do not alter executable code. Before merge, the exact latest PR head must still pass with `paid_request=false` and detector skipped. This forward-stable receipt binds the code-bearing head without creating an infinite report-edit verification chain.

## Preserved original migration receipts

- Validator RED run: `31776789465`.
- Initial security-remediation head/run: `e140e164828cf3128e1d8f6139fd5d1cd393d487` / `31778048629`.
- Default registration PR #22 reviewed head: `092367b72a819b524575fadd6118513cc7bf7c3c`, runs `31778554058` and `31778554047`, merged to `main` as `81b5cd017e3be088c0638e527ce25f5df6a2f4e8`.
- Workflow lifecycle: 0 of the 14 historic paths remain executable; all 14 archive copies match their documented source blobs.
- Manual dispatches and paid calls made during the original migration: `0`.

## Exceptions

Hosted evidence-branch protection, secret scanning, push protection, Actions defaults, and vulnerability alerts remain unverified; code scanning is recorded disabled. Main issue #17 owns those settings/plan limits. Until hosted protection is verified, collaborators able to write the exact evidence ref are part of the paid-secret trust boundary.

## Lesson disposition

- Project detector/editorial ledger: `no-new-lesson`. This is workflow governance, not a detector or prose finding.
- Cross-project: retain the transferable rules for immutable paid-request identity, exact-ref eligibility, non-secret preflight, delayed credentials, recursion-free evidence commits, and owner-transparent automation.
