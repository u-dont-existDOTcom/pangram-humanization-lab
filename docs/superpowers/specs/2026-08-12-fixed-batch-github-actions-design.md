# Fixed Pangram Batch via GitHub Actions — Design

## Goal
Run small, predeclared Pangram-4 minimal-pair batches from GitHub Actions using the repository secret `PANGRAM_API_KEY`, while preserving exact texts, cache reuse, task-id checkpointing, and durable evidence in the private repository.

## Scope
This feature adds one generic fixed-batch runner and one narrow workflow. It does not replace the adaptive Codex experiment engine, change detector interpretation rules, or make ordinary commits spend Pangram credits.

## Architecture
- A JSON experiment spec contains an experiment id and exact variant ids/texts.
- `pangram_lab.fixed_batch` validates the spec and runs each requested text through the existing `PangramClient.detect_cached` + `PangramCache` path.
- The runner uses `GitSync.sync` as the Pangram checkpoint callback, so a task id is committed and pushed before polling and a completed detector result is pushed before the next paid submission.
- A GitHub Actions workflow is path-filtered to the fixed-batch implementation/spec files. Its result/cache commits do not match those paths, preventing a recursive paid rerun.
- The first live experiment is the Romance oxytocin R1S0/R0S1/R1S1 batch already specified in `state/ROMANCE-OXYTOCIN-MINIMAL-PAIR-BATCH-2026-08-12.md`.

## Data flow
1. Push experiment/runner/workflow change on `automation/pangram-fixed-batch`.
2. GitHub Actions checks out with persisted credentials and `contents: write`.
3. Install package/tests and run full pytest gate.
4. Verify `PANGRAM_API_KEY` reaches Pangram's non-billable auth probe.
5. Run exact variants sequentially through the existing Pangram-4 cache/checkpoint path.
6. Write aggregate JSON under `state/experiments/` and commit/push it.
7. Inspect results before deciding whether second-batch C1/C2/C3 calls are justified.

## Safety and spend controls
- Explicit `model="pangram-4"`; terminal version must be `4.0` through the existing client.
- Existing content-addressed cache is always checked before POST.
- POST is never automatically retried after an ambiguous transport result.
- Every task id/result checkpoint pushes before another paid call.
- The experiment spec has an explicit maximum variant count; this first runner defaults to 8 and the current batch contains 3.
- The workflow runs only on its dedicated branch and selected paths; evidence-only commits do not retrigger it.

## Testing
TDD: first add a test that imports the not-yet-existing fixed-batch module and validates exact spec ordering/ids; observe the workflow fail. Then implement only enough parser/runner behavior to pass, rerun the full suite, and only then let the live detector step execute.

## Success criteria
- Unit test proves exact text/order preservation and rejects duplicate ids.
- Existing tests remain green.
- Workflow authenticates with the repository secret without revealing it.
- R1S0, R0S1, R1S1 complete or fail closed under the existing Pangram transport rules.
- Results and cache records are durable in GitHub with exact SHA-256s and Pangram version metadata.
