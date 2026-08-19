# Private Pangram executor architecture

Status: implementation bootstrap, 2026-08-19

## Independent conception snapshot

Problem: Pangram 4 succeeds from Joel's Zorin machine but `POST https://text.external-api.pangram.com/task` returns HTTP 401 `Invalid API key` from GitHub-hosted Azure runners. The same GitHub Actions secret is accepted by Pangram's documented V3 endpoint, so the failure is origin/endpoint specific rather than a missing secret.

Candidate mechanism: keep `pangram-humanization-lab` public and canonical, but move only paid Pangram execution to a private repository with a self-hosted runner on the Zorin machine whose network origin is already known to work.

Constraints:
- never attach a self-hosted runner to the public lab;
- do not duplicate the humanization or Pangram safety logic;
- preserve the existing fixed-batch spec, validator, call ledger, cache, checkpoint, result-path, and no-automatic-POST-retry behavior;
- no arbitrary public pull-request code may run on the Zorin host;
- private trigger inputs must be path- and hash-bound;
- the public lab remains the durable evidence store;
- one local setup step is acceptable; routine Pangram calls should thereafter be triggerable through GitHub.

## Existing-work scan and decision

GitHub explicitly recommends using self-hosted runners only with private repositories because public-repository pull requests can execute hostile workflow code on a persistent self-hosted machine. GitHub supports repository-level self-hosted runners, custom labels, and running the runner as a service on Linux. Self-hosted Actions execution is not billed as GitHub-hosted runner minutes.

The public lab already implements the hard parts of paid-call safety:
- `scripts/validate_paid_dispatch.py` validates fixed-batch specs and the explicit paid confirmation;
- `PangramClient` sends exactly one non-retried POST and checkpoints task IDs before polling;
- `TrackedPangramClient` reserves calls in the section ledger before submission and durably syncs that state;
- `PangramCache` resumes pending tasks and refuses automatic resubmission after ambiguous submits;
- `run_fixed_batch.py` writes canonical results and pushes durable state.

Decision: **compose/reuse** GitHub's private self-hosted runner model with the existing public-lab runner. Do not create a second detector client, queue, cache, call ledger, or result schema.

Primary references:
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners
- https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application
- https://docs.github.com/en/billing/concepts/product-billing/github-actions

## Trust boundaries

### Public repository: `u-dont-existDOTcom/pangram-humanization-lab`

Canonical and public. Stores specs, detector implementation, call ledgers, cache/checkpoints, results, and research evidence. It must **not** own a self-hosted runner.

The private executor checks out only the owner-controlled `automation/pangram-fixed-batch` branch. Public pull-request refs are never checked out or executed.

### Private repository: `u-dont-existDOTcom/pangram-private-executor`

Trusted execution envelope only. It contains:
- one workflow that runs exclusively on a repository-level self-hosted runner labelled `pangram`;
- a strict validator for newly-added `requests/*.json` trigger envelopes;
- no Pangram research logic and no public-facing prose corpus.

It stores the `PANGRAM_API_KEY` as an Actions secret. The workflow never runs for pull requests.

### Zorin self-hosted runner

Runs under Joel's normal Linux user as a system service. A dedicated repository deploy key with write access to `pangram-humanization-lab` is stored only on this machine. The private key is never uploaded to GitHub Actions secrets.

GitHub's documented Ed25519 host key is pinned in a dedicated `known_hosts` file, rather than accepting an unverified `ssh-keyscan` result at job time.

## Trigger contract

A routine paid run is triggered by adding exactly one new file:

`requests/<request-id>.json`

with exactly these keys:

```json
{
  "format": "pangram-private-executor-request-v1",
  "request_id": "example-id",
  "public_repo": "u-dont-existDOTcom/pangram-humanization-lab",
  "public_branch": "automation/pangram-fixed-batch",
  "spec_path": "experiments/example-id.json",
  "spec_sha256": "<64 lowercase hex>",
  "confirmation": "RUN_PAID_PANGRAM_FIXED_BATCH"
}
```

The validator fails closed unless:
- the push changes exactly one file;
- the file is newly added directly under `requests/`;
- the filename stem equals `request_id`;
- repository and branch equal the two fixed canonical values above;
- the spec stays under `experiments/` and is a `.json` file;
- `spec_sha256` is exact lowercase SHA-256;
- the paid confirmation is exact.

The executor then clones the current canonical evidence branch, verifies the exact spec bytes against `spec_sha256`, runs the existing public validator, and invokes `scripts/run_fixed_batch.py` with `PYTHONPATH=src` and the private repo's `PANGRAM_API_KEY` secret.

## Replay and billing safety

The executor deliberately relies on the public lab's existing durable state rather than keeping a second state machine.

On every run it clones the **latest** `automation/pangram-fixed-batch` branch, so reruns see any existing result, pending task checkpoint, ambiguous-submit guard, cache record, and section call ledger.

Existing behavior remains authoritative:
- complete result: reuse, no POST;
- pending task ID: resume GET polling, no POST;
- ambiguous submit: refuse automatic POST;
- fresh variant: one POST, never automatically retried;
- section call cap: fail closed and write handoff state.

An abrupt machine/power failure in the narrow interval after Pangram accepts a POST but before a task ID or ambiguous-failure state can be durably recorded remains an unavoidable residual risk unless Pangram adds an idempotency key. The private executor does not pretend to solve that server-side limitation.

## Routine orchestration after bootstrap

1. Add/update the fixed-batch spec on `automation/pangram-fixed-batch` without a public paid-request trigger.
2. Compute its SHA-256.
3. Add one trigger envelope to the private executor's `requests/` directory.
4. GitHub routes the job to the private repository's self-hosted `pangram` runner.
5. The runner executes the public lab code from the canonical branch, using the local network origin known to work with Pangram 4.
6. Existing `GitSync` pushes reservation/checkpoint/result evidence back to `automation/pangram-fixed-batch` through the local deploy key.

## Bootstrap boundary

The bootstrap script in this directory performs the parts ChatGPT's GitHub connector cannot perform directly:
- create the new private repository if absent;
- install its workflow and validator templates;
- copy the already-exported `PANGRAM_API_KEY` into that private repo's Actions secrets without printing it;
- create/register a dedicated write deploy key for the public lab;
- download and register GitHub's repository-level self-hosted runner;
- install/start it as a service.

After that bootstrap, routine execution should not require terminal copy/paste.
