# Pangram fixed-batch evidence branch current state

Updated: 2026-08-15

## Goal

Preserve exact detector evidence and the owner's no-click operating model with one reusable, budget-aware automatic runner. Ordinary changes remain free; paid work begins only from a new immutable request that byte-binds one new fixed-batch spec on the exact evidence ref.

## Authority / baseline

- Evidence branch: `automation/pangram-fixed-batch`
- Automatic-run code/governance merge: `34621f38d702b5739e59cb8f81831604f01e5a52` (PR #23)
- Latest completed detector/lesson-review head: `2114c0544ae2b994677f1217edc2cc3b192ad2a6`
- That head contains the exact r31 request, spec, call reservation, task checkpoint, detector result, fixed-batch result, and lesson review.
- Canonical article prose remains outside this evidence branch. r31 was not installed and is fidelity-invalid after the owner's quotation correction.

## Completed

- All 14 historic task workflows remain non-executable archived provenance.
- The evidence workflow has no `workflow_dispatch`, task-specific paid workflow, broad path-only paid trigger, or commit-message paid trigger.
- Pull requests and ordinary pushes run the deterministic suite/audit only.
- Paid eligibility requires a push to the exact evidence ref adding exactly one immutable `requests/pangram/<experiment-id>.json` request plus its byte-hash-bound new spec, with no third change.
- The request/spec gate rejects modified/deleted requests, stale specs, symlink components, duplicate/surplus keys, unsafe identities, control characters, noncanonical results, digest mismatches, and experiment/request mismatches before detector or secret access.
- Only `paid_request`, validated `spec_path`, and canonical `result_path` cross the job-output boundary.
- The detector alone receives `contents: write`; persisted write credentials and `PANGRAM_API_KEY` remain at the final runner boundary.
- PR #23 exact final head `4b3b042b921dba4631dc5eb6f56bc0eb78a882ba` passed push run `31842769049` and PR run `31842772778`, with detector skipped.
- Merge `34621f38d702b5739e59cb8f81831604f01e5a52` passed post-merge run `31842902465`, job `94903386396`; preflight returned `paid_request=false`, detector skipped.
- Restoring automation itself made 0 paid Pangram calls.

## r30 automatic execution

- Request/spec commit: `48272f766ecebfe016d69f25faa6d7601ac48c85`
- Exact candidate SHA-256: `9648136e210e593429c1b1a44b1cbd210ef9bbee1950c10776f8fa8a5ae49b57`
- Request-bound spec SHA-256: `d093fa64e2b214508c2fe9da433e47e4a8aee7978e7e1774ee13e948909e96f3`
- Automatic run: `31843059275`
- Verify job: `94903844058` — 87 tests, 0 audit errors, exact preflight `paid_request=true`
- Detector job: `94903911646` — success without manual dispatch
- Pangram task: `5de8788f-2c80-497d-ba02-6299e03f04b0`
- Result commit/ref: `2f7ced014e0071dc8a15b199f57166c984b088b4`
- Lesson-review head: `c69a250538d2e7260ea31314907a3d0963645001`
- Exact result: Human `0.6168841123580933`, AI `0.38311588764190674`, AI-assisted `0.0`; headline `AI Detected`
- Segmentation: first 164 words Human; one 459-word AI window begins at `I still think it's the best advice...`, covers the rest of Talk, and includes Slow's first paragraph; final 544 words Human.
- Accounting: r30 added one paid POST reservation estimated at 2 credits. The section ledger now records 3 paid posts total, 5 estimated credits total, 0 pending resumes, against the six-post cap.
- r30 was not installed.

## r31 automatic execution and fidelity correction

- Request/spec commit: `7a641df49ce3b0caa9f00c9222a018f444fa9f97`
- Exact candidate SHA-256: `bceb849c4a593efcedb43c650ad08597f93a25a8d5cd4b3fcab617997dd9a34f`
- Request-bound spec SHA-256: `3351fc3bcfa56ba3efb3ea42ad3b832779fd70405fb458c64324b39c97d14470`
- Automatic run: `31844683111`
- Verify job: `94908589238` — success; exact preflight authorized the immutable two-file request
- Detector job: `94908650800` — success without manual dispatch
- Pangram task: `0049130b-470d-4576-a0a7-f3a95328bb1b`
- Result commit: `925673bfff808daf63fdca560190267f6d701d4f`
- Lesson-review head: `2114c0544ae2b994677f1217edc2cc3b192ad2a6`
- Exact result: Human `0.7607057094573975`, AI `0.23929430544376373`, AI-assisted `0.0`; headline `AI Detected`
- Segmentation: first 238 words Human; one 273-word AI window covers the assistant-built remainder of Talk; the complete 609-word Slow section is Human.
- Accounting: r31 added one paid POST reservation estimated at 2 credits. The section ledger records 4 paid posts, 7 estimated credits, 0 pending resumes, against the six-post cap.
- Owner fidelity correction: the direct quote is “Sex is what you do when you are older and you find a friend you want to have children with.” Joel heard it at about five and thought it made sense. “Before you do it, ask each other whether you would want to raise children together and whether you're ready” is a later paraphrase, not direct speech.
- Disposition: r31 falsely placed the paraphrase in quotation marks. It is fidelity-invalid regardless of score, was not installed, and must remain immutable detector evidence only.

## Current checkpoint

- No detector or evidence-branch writer is active.
- r31 completed automatically and failed both gates: it scored below 1.0/0/0 and the owner later invalidated its quotation provenance.
- r27 remains non-installable because it dropped protected C35–45 fields/functions.
- The exact direct quote belongs once in the article opening. Do not quote the readiness/child-rearing paraphrase as the father's words.
- Do not stage another paid paraphrase without new owner evidence that supplies the missing relation after the correct opening quote.

## Remaining

- Recover Joel's own later understanding of what his father's real sentence left out about sex and readiness.
- If that answer supplies the missing relation, rebuild only the failed Talk movement while preserving every C35–45 function and the exact Slow bytes.
- Install only an exact 1.0/0/0 fidelity-valid combined-boundary result, then audit both article joins and make the eventual fresh full-article certification call.

## Blockers / unresolved

- Talk/Slow is blocked on the missing authorial relation after the corrected direct quote, not detector access.
- Evidence-branch protection and hosted secret controls remain unverified; main issue #17 tracks owner/settings follow-up.
- Until hosted protections are verified, write-capable collaborators remain inside the repository-secret/workflow trust boundary.

## Evidence / artifacts

- Compliance report: `docs/EVIDENCE-WORKFLOW-COMPLIANCE-2026-08-14.md`
- Executable workflow: `.github/workflows/pangram-paid-dispatch.yml`
- Automatic preflight: `scripts/validate_paid_push.py`
- r31 request: `requests/pangram/romance-authorial-recovery-r31-childhood-memory-2026-08-14.json`
- r31 spec: `experiments/romance-authorial-recovery-r31-childhood-memory-2026-08-14.json`
- r31 result: `state/experiments/romance-authorial-recovery-r31-childhood-memory-2026-08-14-results.json`
- r31 fidelity correction: `state/ROMANCE-R31-FIDELITY-CORRECTION-2026-08-15.md`
- Call ledger: `state/pangram-call-ledgers/romance-authorial-recovery-2026-08-14.json`
- Automation PR: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/pull/23
- Hosted-control follow-up: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/issues/17

## Next safe action

Ask Joel one narrow question: when he got older, what did he himself think his father's real sentence left out about sex? Do not stage another paid request until the answer supplies a genuinely new route for the protected Talk fields.

## Recovery rule

Before any paid request, fetch the current evidence head and active Actions runs. Recover exact task IDs, cache, call ledger, result state, request identity, and spec digest from Git; never infer them from chat and never repeat an ambiguous or already-paid POST.
