# Pangram access through GitHub Actions

This is the operational authority for deciding whether Pangram access exists in this repository.

The repository secret `PANGRAM_API_KEY` is not a value a worker should retrieve. It is a credential that trusted GitHub Actions code may receive through a step-level environment variable. A missing local environment variable, a rejected local key, or a signed-out Pangram dashboard does **not** establish that detector access is unavailable.

The currently proven repository-secret route lives on the `automation/pangram-fixed-batch` branch. Its fixed-batch workflow has successfully verified the secret and run Pangram 4 batches. Until an equivalent route is promoted to `main` and tested, use that branch as the implementation base. Its `workflow_dispatch` declaration is not, by itself, evidence that manual dispatch is the proven route; the proven executions are push-triggered.

## Blocking access-resolution gate

Before calling any candidate a `pre-Pangram candidate`:

1. Freeze the exact candidate and the exact boundary to be measured.
2. Record the artifact revision, boundary label, and UTF-8 SHA-256 of the literal submitted text. Do not trim, rewrap, normalize whitespace, or change newline style before hashing.
3. Check the direct/local API route. If `PANGRAM_API_KEY` is missing or rejected, continue to the repository-secret Actions route. A dashboard login is irrelevant to this API route.
4. Inspect current repository state and active Actions runs. Do not launch a competing or duplicate paid batch.
5. Use the repository-secret Actions route described below.
6. Only if both routes are unusable may the candidate be labeled `pre-Pangram candidate`. Record the exact blocker: repository permission, Actions disabled, secret check or authentication failure, exhausted credits, transport ambiguity, workflow failure, or another concrete cause.

An unmeasured candidate is not detector-complete.

## Prepare a task-specific fixed batch

Start from the current head of `automation/pangram-fixed-batch`. Create a unique task branch and unique paths; do not overwrite another worker's experiment, workflow, spec, result, or cache state. Before changing anything, check open pull requests, recent workflow runs, and active branches for overlapping Pangram work.

Use:

- a unique `experiment_id`;
- stable, unique variant IDs;
- a unique spec path and result path;
- a narrow task workflow or a coordinated change to the existing branch; and
- `on.push.branches` set to the exact unique task branch; and
- path filters limited to task-specific inputs such as that workflow, spec, and task-specific builder file.

Copying the workflow onto a new branch is not enough: the inherited workflow filters on `automation/pangram-fixed-batch` and will not run until its branch filter names the new task branch. Run the shared runner and tests inside the job, but do not normally include shared runner or test paths in every historical task workflow's push filters. A later edit to a shared path could otherwise wake multiple old paid workflows. Never include cache or result paths as triggers.

The current proven trigger is a push to the repository branch that contains the trusted workflow. Do not describe `workflow_dispatch` as canonical until a manual-dispatch path has been promoted and successfully tested.

Do not run secret-bearing workflow code from a fork pull request or from unreviewed third-party code.

## Workflow contract

The task workflow must preserve these properties of `.github/workflows/pangram-fixed-batch.yml`:

- `permissions: contents: write`, so checkpoint and result commits can be recorded;
- checkout with `fetch-depth: 0`;
- Python 3.11;
- installation of `.[test]`;
- tests for `tests/test_fixed_batch.py`, `tests/test_pangram.py`, `tests/test_cache.py`, and `tests/test_git_sync.py` before the paid batch;
- a configured checkpoint Git identity;
- `PANGRAM_API_KEY: ${{ secrets.PANGRAM_API_KEY }}` supplied only through step-level `env` blocks for the non-billable secret/authentication check and the detector run—never at workflow or job scope, and never in a command, file, output, or artifact;
- a separate non-empty-secret check such as `test -n "$PANGRAM_API_KEY"` that never echoes the value;
- `python scripts/run_fixed_batch.py SPEC --out RESULT`; and
- trigger exclusions for `cache/**` and `state/experiments/**`, so evidence/checkpoint commits cannot recursively trigger paid detector calls.

Keep the workflow narrow. Do not add debugging that enumerates the environment or shell tracing around the secret-bearing step.

## Spec contract

The spec file is JSON. Use the fixed-batch v1 format:

```json
{
  "format": "pangram-fixed-batch-v1",
  "experiment_id": "unique-task-id",
  "variants": [
    {
      "id": "stable-variant-id",
      "text": "First exact paragraph.\n\nSecond exact paragraph."
    }
  ]
}
```

The runner accepts at most eight variants unless the limit is consciously changed and reviewed. The `text` field is the literal detector input. Do not silently substitute a paragraph for a document, merge boundaries, remove a heading, normalize whitespace, or change link/native-marker text.

## Credential and billing safety

Never:

- retrieve, reveal, print, paste, download, or commit the repository secret;
- ask Joel or another worker to paste the secret into chat or a file;
- use `set -x`, `printenv`, secret-bearing debug dumps, or artifact uploads that could expose the environment;
- execute the secret-bearing workflow from a fork or untrusted branch code;
- automatically retry an ambiguous POST; or
- start overlapping fixed-batch workflows that can race on results, cache, or Git pushes.

The fixed-batch runner performs a non-billable authentication probe first. It uses content-addressed caching and recorded task IDs to resume safely. Let that logic control reuse and recovery; do not improvise retries that could spend credits twice.

## Validate the measurement, not merely the workflow

A green workflow is necessary but not sufficient. Inspect the committed result JSON and verify:

- its `experiment_id` matches the intended batch;
- the stored `text` is the exact submitted text;
- `text_sha256` matches the independently recorded UTF-8 SHA-256;
- `detector.stage` is `STAGE_SUCCESS`;
- `detector.version` is `4.0`;
- for a requested Joel humanization completion, `detector.fraction_human == 1.0`, `detector.fraction_ai == 0.0`, and `detector.fraction_ai_assisted == 0.0`;
- the result belongs to the intended document/paragraph boundary; and
- the result path, result commit, workflow run URL, and workflow head SHA are recorded in the editorial report or experiment note.

Pangram 4 is requested explicitly by the repository client. A result from another detector version does not satisfy this gate.

## Acceptance and unresolved-author handoff

For Joel's requested Pangram-humanization work, a successful detector request or `Human` classification is not enough. The exact intended delivery boundary must be 100% Human under the fraction checks above. Results such as 93% or 99% are progress only.

Continue faithful, coherence-preserving repair and exact-boundary retesting until the 100% criterion is met. If the worker genuinely does not know another faithful and coherent repair, stop as an unresolved authorial handoff and record:

- the exact failing span and measured boundary;
- the exact result path, text hash, score, and detector version;
- the faithful approaches already attempted and their measured results;
- the claims, memories, tone, rhetorical functions, links, and native objects that cannot be sacrificed;
- why no further faithful repair is known; and
- the narrow question, lived detail, natural wording, or other raw author input needed from Joel.

Do not call that state complete or passing. A section/API-call cap is a spending and escalation boundary, not an acceptance threshold. If it pauses paid calls, state whether a known faithful next repair remains.

## Exact-text and staleness rule

A result applies only to the exact text hash and boundary that were tested. Any later change to wording, whitespace, newlines, order, paragraph boundaries, headings, link anchors, or native-object markers makes that result inapplicable to the changed boundary.

If the exact text hash, boundary, model, and detector version are unchanged, a valid content-addressed cache hit should be reused; age alone does not make it stale. A successful older workflow run is not evidence for a different candidate.

## How to report unavailable access

Do not write “Pangram was unavailable” without completing the access-resolution gate. Report which route was tried and the exact blocker. If the local route failed but the Actions route succeeded, record the Actions result normally; do not describe the candidate as pre-Pangram.
