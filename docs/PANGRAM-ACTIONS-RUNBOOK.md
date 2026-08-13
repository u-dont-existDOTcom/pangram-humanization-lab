# Pangram access through GitHub Actions

This is the operational authority for deciding whether Pangram access exists in this repository.

The repository secret `PANGRAM_API_KEY` is not a value a worker should retrieve. It is a credential that trusted GitHub Actions code may receive through a step-level environment variable. A missing local environment variable, a rejected local key, or a signed-out Pangram dashboard does **not** establish that detector access is unavailable.

The currently proven repository-secret route lives on the `automation/pangram-fixed-batch` branch. Its fixed-batch workflow has successfully verified the secret and run Pangram 4 batches. Until an equivalent route is promoted to `main` and tested, use that branch as the implementation base.

## Blocking access-resolution gate

Before calling any candidate a `pre-Pangram candidate`:

1. Freeze the exact candidate and exact boundary to be measured. For a paid humanization audit, assign a stable `audit_id` and `section_id` before the first submission.
2. Record the artifact revision, boundary label, and UTF-8 SHA-256 of the literal submitted text. Do not trim, rewrap, normalize whitespace, or change newline style before hashing.
3. Check the direct/local API route. If `PANGRAM_API_KEY` is missing or rejected, continue to the repository-secret Actions route. A dashboard login is irrelevant to this API route.
4. Inspect current repository state, call ledger, cache/pending state, and active Actions runs. Do not launch a duplicate paid batch or reset a section budget by changing workflow/batch names.
5. Use the repository-secret Actions route described below.
6. Only if both routes are unusable may the candidate be labeled `pre-Pangram candidate`. Record the exact blocker: repository permission, Actions disabled, secret check or authentication failure, exhausted credits, transport ambiguity, workflow failure, or another concrete cause.

An unmeasured candidate is not detector-complete.

## Prepare a task-specific fixed batch

Start from the current head of `automation/pangram-fixed-batch`. Before changing anything, check current branches, workflow runs, result state, cache state, and the section's persisted call ledger for overlapping Pangram work.

For new audited work use:

- a unique `experiment_id`;
- one stable `audit_id` for the audit session;
- a stable `section_id` for each independently tested boundary;
- stable variant IDs;
- a unique spec path and result path; and
- the shared audited fixed-batch runner rather than a new paid workflow whenever possible.

The budget key is `audit_id + section_id + detector model + expected version`. Moving the same section into a different batch, branch, workflow, chat, or retry does not reset its count. A full-article acceptance test is a separate boundary with its own `section_id`.

Historical task-specific workflows must not be allowed to wake up on shared code changes. Code-only CI is non-billable; paid detector execution must require an intentional experiment input or explicit dispatch. Never include cache, call-ledger, inbox, handoff, or result paths as paid-workflow triggers.

Do not run secret-bearing workflow code from a fork pull request or from unreviewed third-party code.

## Workflow contract

The proven `.github/workflows/pangram-fixed-batch.yml` separates regression verification from paid execution:

- a read-only **test** job runs the fixed-batch/Pangram/cache/GitSync/call-accounting regression suite;
- the **detector** job has `contents: write` only when intentional detector execution is required;
- checkout uses `fetch-depth: 0`;
- Python 3.11 and `.[test]` are installed;
- a checkpoint Git identity is configured before detector execution;
- `PANGRAM_API_KEY: ${{ secrets.PANGRAM_API_KEY }}` is supplied only through step-level `env` blocks for the non-billable secret/authentication check and detector run—never at workflow or job scope, and never in a command, file, output, or artifact;
- a separate non-empty-secret check such as `test -n "$PANGRAM_API_KEY"` never echoes the value;
- audited work runs through `python scripts/run_fixed_batch.py SPEC --out RESULT`; and
- evidence/checkpoint commits cannot recursively trigger paid detector calls.

Keep the workflow narrow. Do not add debugging that enumerates the environment or shell tracing around the secret-bearing step. A code-only push must not spend Pangram.

## Spec contract

The spec file is JSON. New paid humanization audits use fixed-batch v1 plus audit/section identity:

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

If `audit_id` is supplied, every variant must have a non-empty `section_id`. Legacy historical specs without audit identity remain readable, but new humanization audits must use the accounted path.

The runner accepts at most eight variants unless that batch-size limit is consciously changed and reviewed. The paid section cap is stricter: **at most six new paid Pangram POSTs per section per audit**, accumulated across batches. The `text` field is the literal detector input. Do not silently substitute a paragraph for a document, merge boundaries, remove a heading, normalize whitespace, or change link/native-marker text.

## Credential, billing, and call-budget safety

Never:

- retrieve, reveal, print, paste, download, or commit the repository secret;
- ask Joel or another worker to paste the secret into chat or a file;
- use `set -x`, `printenv`, secret-bearing debug dumps, or artifact uploads that could expose the environment;
- execute the secret-bearing workflow from a fork or untrusted branch code;
- automatically retry an ambiguous POST;
- start overlapping fixed-batch workflows that can race on results, cache, call ledgers, or Git pushes;
- raise the six-call section cap; or
- invent a new `audit_id` solely to buy more attempts.

Count toward the six paid calls:

- every new detector POST;
- an ambiguous POST that may have reached Pangram;
- a corrective paid POST after a preserved wrong-version task.

Do not count:

- exact content-addressed cache hits;
- authentication probes;
- polling GETs;
- resuming an already-paid pending task.

The tracked client reserves and Git-syncs the paid call **before** the POST. This makes the section budget interruption-safe. Before a seventh paid POST for the same budget key, the runner fails closed and writes `state/handoffs/pangram/<audit_id>-<section_id>.json`; the worker then asks Joel for narrow help.

The runner records exact `paid_api_calls`, cache hits, pending resumes, submitted word counts, estimated credits/cost, and calls/estimated credits to the first Human result. When Pangram does not provide authoritative billing usage, credit figures must remain explicitly labeled estimates.

The fixed-batch runner performs a non-billable authentication probe first. It uses content-addressed caching and recorded task IDs to resume safely. Let that logic control reuse and recovery; do not improvise retries that could spend credits twice.

## Validate the measurement, not merely the workflow

A green workflow is necessary but not sufficient. Inspect the committed result JSON and verify:

- its `experiment_id` and `audit_id` match the intended audit;
- every measured row has the intended `section_id`;
- the stored `text` is the exact submitted text;
- `text_sha256` matches the independently recorded UTF-8 SHA-256;
- `detector.stage` is `STAGE_SUCCESS`;
- `detector.version` is `4.0`;
- for a requested Joel humanization completion, `detector.fraction_human == 1.0`, `detector.fraction_ai == 0.0`, and `detector.fraction_ai_assisted == 0.0`;
- `call_accounting` reports the section's exact paid-call count and estimated credit/cost fields;
- the result belongs to the intended document/paragraph boundary; and
- the result path, result commit, workflow run, workflow head SHA, paid-call count, and available credit/cost accounting are recorded in the editorial report or experiment note.

The current runner also registers completed result metadata for semantic lesson review in `state/LESSON-INBOX.json` without copying the tested passage into that queue.

Pangram 4 is requested explicitly by the repository client. A result from another detector version does not satisfy this gate.

## Acceptance and authorial handoff

Whenever Joel asks to humanize text, make it pass Pangram, or otherwise makes Pangram success a delivery requirement, this gate applies. A successful detector request or `Human` classification is not enough. The exact intended delivery boundary must satisfy `detector.stage == "STAGE_SUCCESS"`, `detector.version == "4.0"`, `detector.fraction_human == 1.0`, `detector.fraction_ai == 0.0`, and `detector.fraction_ai_assisted == 0.0`. A partial result such as 93% or 99% Human is progress only; it is not a detector pass.

Section/window measurements are diagnostic unless that unit is the complete requested deliverable. For a full article, the complete exact article boundary must itself satisfy the gate after every accepted edit; section-level 100% results do not aggregate into an article pass.

The normal editorial terminal states are: (1) the exact intended delivery boundary satisfies the 100% detector gate and all editorial/fidelity gates; or (2) the worker genuinely knows no further faithful and coherent repair and makes an unresolved authorial handoff. The six-paid-call section limit adds a mandatory operational suspension: even if another faithful repair may exist, stop before the seventh paid POST and request narrow help from Joel. This suspension is not completion or a detector pass.

Any unresolved handoff or paid-cap suspension must record:

- the exact failing span and measured boundary;
- exact `text_sha256`; `fraction_human`, `fraction_ai`, and `fraction_ai_assisted`; detector version; result path; and result commit;
- the faithful approaches already attempted and their measured results;
- paid API calls used for that section and available estimated/reported credit usage;
- the claims, memories, tone, rhetorical functions, links, and native objects that cannot be sacrificed; and
- the narrow question, lived detail, natural wording, or other raw author input needed from Joel.

Do not call an unresolved state complete or passing. After materially new authorial guidance, a genuinely new audit may begin with a fresh section budget. Never manufacture a fresh audit merely to bypass the cap. A 100% Human result with semantic, rhetorical, editorial, fidelity, or provenance loss also fails the gate.

## Exact-text and staleness rule

A result applies only to the exact text hash and boundary that were tested. Any later change to wording, whitespace, newlines, order, paragraph boundaries, headings, link anchors, or native-object markers makes that result inapplicable to the changed boundary.

If the exact text hash, boundary, model, and detector version are unchanged, a valid content-addressed cache hit should be reused; age alone does not make it stale. A successful older workflow run is not evidence for a different candidate.

## How to report unavailable access

Do not write “Pangram was unavailable” without completing the access-resolution gate. Report which route was tried and the exact blocker. If the local route failed but the Actions route succeeded, record the Actions result normally; do not describe the candidate as pre-Pangram.
