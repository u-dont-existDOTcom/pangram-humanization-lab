# Pangram Private Executor

Private, trusted execution envelope for `u-dont-existDOTcom/pangram-humanization-lab`.

This repository intentionally contains **no humanization research logic**. It exists only to route approved fixed-batch Pangram 4 jobs to Joel's repository-level self-hosted runner, whose network origin is known to work with Pangram's async API.

## Security boundary

- Keep this repository private.
- Do not attach the self-hosted runner to the public Pangram lab.
- Do not add `pull_request` workflow triggers.
- Do not run code from public PR refs or arbitrary repositories.
- `PANGRAM_API_KEY` is an Actions secret here.
- Write access to the public lab uses a dedicated deploy key whose private half stays only on the self-hosted machine.
- GitHub's host key is pinned locally; jobs use `StrictHostKeyChecking=yes`.

## Triggering a paid run

Add exactly one new `requests/<request-id>.json` file to `main`:

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

The workflow rejects modified/replayed request files, multi-file trigger commits, path escapes, other repositories/branches, digest mismatches, and missing paid confirmation.

The actual Pangram client, cache, task checkpointing, call ledger, section cap, result schema, and Git synchronization all come from the canonical public lab branch at execution time.

## Replay behavior

Every execution clones the latest `automation/pangram-fixed-batch` state before invoking the existing runner. Therefore completed results are reused, pending task IDs are resumed without another POST, and ambiguous submissions remain fail-closed according to the public lab's existing logic.

## Runner

The bootstrap installs the GitHub runner as a Linux service with the additional label `pangram`. Routine jobs use:

`runs-on: [self-hosted, linux, x64, pangram]`

Self-hosted runner compute does not consume GitHub-hosted Actions minutes; the machine itself remains the operator's responsibility.
