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

## First automatic execution receipt

- PR #23 merged as `34621f38d702b5739e59cb8f81831604f01e5a52`; post-merge run `31842902465` succeeded with `paid_request=false` and detector skipped.
- r30 was staged as the sole allowed pair in commit `48272f766ecebfe016d69f25faa6d7601ac48c85`: one new immutable request and one new spec, with candidate SHA-256 `9648136e210e593429c1b1a44b1cbd210ef9bbee1950c10776f8fa8a5ae49b57` and request-bound spec SHA-256 `d093fa64e2b214508c2fe9da433e47e4a8aee7978e7e1774ee13e948909e96f3`.
- Automatic run `31843059275` required no owner click. Verify job `94903844058` passed 87 tests, 0 audit errors, and returned `paid_request=true`; detector job `94903911646` succeeded.
- Task `5de8788f-2c80-497d-ba02-6299e03f04b0` was checkpointed before polling. Result commit/ref is `2f7ced014e0071dc8a15b199f57166c984b088b4`; lesson-review head is `c69a250538d2e7260ea31314907a3d0963645001`.
- Exact r30 result: Human `0.6168841123580933`, AI `0.38311588764190674`, AI-assisted `0.0`. r30 added one paid POST reservation estimated at 2 credits; the section ledger totals 3 paid posts, 5 estimated credits, and 0 pending resumes.
- Result/checkpoint pushes did not contain a request change and did not recursively authorize detector work.
- r30 was not installed. Because r29 and r30 are two fidelity-complete, meaningfully different failures, further autonomous variants are stopped pending narrow author evidence.

## Second automatic execution receipt and fidelity disposition

- r31 was staged as the sole allowed pair in commit `7a641df49ce3b0caa9f00c9222a018f444fa9f97`, with candidate SHA-256 `bceb849c4a593efcedb43c650ad08597f93a25a8d5cd4b3fcab617997dd9a34f` and request-bound spec SHA-256 `3351fc3bcfa56ba3efb3ea42ad3b832779fd70405fb458c64324b39c97d14470`.
- Automatic run `31844683111` required no owner click. Verify job `94908589238` and detector job `94908650800` succeeded; task `0049130b-470d-4576-a0a7-f3a95328bb1b` was checkpointed.
- Result commit `925673bfff808daf63fdca560190267f6d701d4f` records Human `0.7607057094573975`, AI `0.23929430544376373`, and AI-assisted `0.0`; lesson-review head is `2114c0544ae2b994677f1217edc2cc3b192ad2a6`.
- r31 added one paid POST reservation estimated at 2 credits. The audit ledger totals 4 paid posts, 7 estimated credits, and 0 pending resumes.
- Result/checkpoint pushes did not alter the immutable request and could not recursively authorize paid work.
- The owner then corrected quotation provenance: the direct quote is “Sex is what you do when you are older and you find a friend you want to have children with.” The readiness/child-rearing formulation used in r31 is a paraphrase, not direct speech.
- r31 is therefore fidelity-invalid regardless of detector score and was not installed. Exact detector evidence remains immutable; the correction is recorded separately rather than rewriting the tested text.

## Exceptions

Hosted evidence-branch protection, secret scanning, push protection, Actions defaults, and vulnerability alerts remain unverified; code scanning is recorded disabled. Main issue #17 owns those settings/plan limits. Until hosted protection is verified, collaborators able to write the exact evidence ref are part of the paid-secret trust boundary.

## Lesson disposition

- Project detector/editorial ledger: `no-new-lesson`. This is workflow governance, not a detector or prose finding.
- Cross-project: retain the transferable rules for immutable paid-request identity, exact-ref eligibility, non-secret preflight, delayed credentials, recursion-free evidence commits, and owner-transparent automation.
