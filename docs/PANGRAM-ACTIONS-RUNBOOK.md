# Pangram access through GitHub Actions — legacy/optional transport

## Current status

This document no longer decides whether Pangram access exists. Current transport authority is `../state/CURRENT-STATE.md`.

As of 2026-08-20 the supported routing order is:

1. use the owner's self-hosted Pangram API path for normal programmatic detector work;
2. use the local headed Brave/Chromium + Playwright transport (`pangram-local`) when authenticated History recovery, visual evidence, or GUI resilience is useful;
3. use GitHub-hosted Actions only when a task specifically requires hosted detector execution and the current endpoint/origin policy has been verified.

A 2026-08-19 live compatibility test showed that a valid `PANGRAM_API_KEY` could succeed locally and authenticate against another documented Pangram endpoint while `POST https://text.external-api.pangram.com/task` returned HTTP 401 from GitHub-hosted runners before any task ID was issued. That issue is tracked in GitHub issue #95.

Therefore:

- a failed or unavailable GitHub-hosted Actions call does **not** establish that Pangram is unavailable;
- do not route automatically from a working self-hosted API or local GUI path into Actions;
- do not retry paid work merely to test whether the hosted-runner origin problem still exists;
- keep this runbook for the fixed-batch evidence/accounting machinery and for future tasks that intentionally choose the Actions transport.

The repository secret `PANGRAM_API_KEY` is never a value a worker should retrieve, reveal, print, download, or commit. Trusted GitHub Actions code may receive it only through a narrowly scoped environment variable.

## Current access-resolution gate

Before calling a candidate unmeasured or detector-blocked:

1. Freeze the exact candidate and exact reader-visible boundary to be measured. Record its UTF-8 SHA-256 before any paid action.
2. Check current content-addressed cache, task/checkpoint state, GUI submission reservations, authenticated History recovery state, and the relevant call ledger. Never repeat already-paid or ambiguous work automatically.
3. Use the current self-hosted API route when a programmatic result is sufficient.
4. If authenticated GUI/History inspection or visual evidence is needed, use `pangram-local` and `docs/PANGRAM-LOCAL-PLAYWRIGHT.md`.
5. Only when a task specifically calls for GitHub-hosted execution should this Actions route be considered. Before doing so, verify that issue #95's hosted-origin/API compatibility problem has been resolved or that the chosen endpoint is known to work from the hosted runner.
6. If all currently supported routes are genuinely unusable, record the exact blocker. Do not collapse distinct states such as credentials unavailable, exhausted credits, transport ambiguity, origin-specific 401, workflow permission failure, or missing GUI authentication into a generic “Pangram unavailable.”

An unmeasured candidate is not detector-complete.

## Reader-visible representation gate

Before freezing a certification boundary, derive the **reader-visible** text Pangram will actually evaluate. For Markdown article work, raw Markdown is diagnostic only: strip source-only markup and link destinations and certify the resulting visible plaintext. For Substack, use the rendered reader-visible text, including any embed/card text Pangram actually surfaces.

Hash and record the exact reader-visible certification text after this representation step. A result applies only to the exact text hash, representation, boundary, model, and detector version that were tested.

## When the Actions route is deliberately used

The historical fixed-batch implementation lives on `automation/pangram-fixed-batch`. Before changing or dispatching it:

- inspect current branch/workflow/result/cache/call-ledger state;
- verify that the current hosted endpoint can actually authenticate from GitHub's runner origin;
- use a unique `experiment_id`;
- use one stable `audit_id` for the audit session;
- use a stable `section_id` for each independently measured boundary;
- use stable variant IDs and unique spec/result paths;
- reuse the shared audited fixed-batch runner rather than creating another paid workflow;
- ensure no overlapping workflow can race on the same paid budget or evidence state.

The paid budget identity is `audit_id + section_id + detector model + expected version`. Changing batch, branch, workflow, chat, or retry labels does not reset the count.

Historical task-specific workflows must not wake up on shared code changes. Code-only CI is non-billable; paid detector execution requires an intentional experiment input or explicit dispatch. Never include cache, ledger, inbox, handoff, or result paths as triggers for paid work.

Do not run secret-bearing workflow code from a fork pull request or unreviewed third-party code.

## Fixed-batch workflow contract

The proven fixed-batch design separates non-billable verification from paid execution:

- a read-only test job runs fixed-batch/Pangram/cache/GitSync/call-accounting regressions;
- the detector job receives `contents: write` only when intentional detector execution is required;
- checkout uses full history when evidence commits require it;
- `PANGRAM_API_KEY` is supplied only through a step-level secret environment variable for the narrow auth/detector steps;
- no workflow/job-level secret environment, shell tracing, environment dumps, or artifact upload may expose the credential;
- audited work runs through the shared fixed-batch runner;
- evidence/checkpoint commits cannot recursively trigger paid detector work.

The existence of this workflow is not evidence that the current Pangram async endpoint accepts GitHub-hosted runner traffic.

## Spec contract

Historical/new fixed-batch specs use stable experiment/audit/section identity. Example:

```json
{
  "format": "pangram-fixed-batch-v1",
  "experiment_id": "unique-task-id",
  "audit_id": "article-audit-2026-08-13",
  "variants": [
    {
      "id": "stable-variant-id",
      "section_id": "opening",
      "text": "First exact paragraph.\n\nSecond exact paragraph."
    }
  ]
}
```

The `text` field is the literal detector input. Do not silently substitute another boundary, normalize whitespace, remove a heading, or change visible link/native-object text after the certification representation has been frozen.

## Credential, billing, and call-budget safety

Never:

- retrieve, reveal, print, paste, download, or commit the repository secret;
- ask Joel or another worker to paste the secret into chat or a file;
- use `set -x`, `printenv`, secret-bearing debug dumps, or artifact uploads around the credential;
- execute the secret-bearing workflow from a fork or untrusted branch code;
- automatically retry an ambiguous POST;
- start overlapping paid workflows that can race on results, cache, call ledgers, or Git pushes;
- invent a new audit identity merely to buy more detector attempts.

A paid-call reservation/checkpoint must become durable **before** the irreversible POST/click whenever the selected transport supports that model. If a transport failure occurs after the action may have reached Pangram, treat it as potentially paid and recover before repeat.

Exact cache hits and resumption/recovery of an already-paid task are not new paid submissions.

## Validate the measurement, not merely the workflow

A green workflow is necessary but not sufficient. Verify the committed detector result against the intended boundary:

- exact audit/section/variant identity;
- exact stored reader-visible text and SHA-256;
- Pangram terminal stage and detector version;
- explicit structured result fractions rather than guessed probability semantics;
- exact paid-call accounting;
- result path/commit and transport provenance;
- correct document/section boundary and representation.

A result from another detector version does not certify Pangram 4 work.

## Acceptance and authorial handoff

Detector output is evidence, not editorial authority. Coherence, meaning, source/owner fidelity, article function, and protected rhetorical functions remain blocking even when a detector says Human.

When a task explicitly requires a Pangram threshold, apply that threshold only to the exact intended delivery boundary and exact tested representation. Section/window measurements do not aggregate automatically into a whole-article pass.

If the paid-call cap or another operational safety gate stops further testing, record the exact failing boundary/hash, detector result, attempts, call count, preserved editorial constraints, and the narrow authorial input needed. Do not call an unresolved state complete.

## Staleness rule

Any later change to reader-visible wording, whitespace, newlines, order, paragraph boundaries, headings, link anchors, visible card/embed text, or other certified content invalidates the old result for the changed boundary.

If the exact text hash, representation, boundary, model, and detector version are unchanged, reuse a valid content-addressed result; age alone does not make it stale.

## Reporting route failures

Do not write “Pangram was unavailable” merely because GitHub-hosted Actions failed. Report the route attempted and exact blocker. In particular, preserve `GitHub-hosted async endpoint returned 401 before task creation` as a distinct compatibility state while issue #95 remains unresolved.

For ordinary new detector work, return to `../state/CURRENT-STATE.md`: self-hosted API first, local Playwright GUI when GUI/History evidence is useful.
