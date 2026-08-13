# Pangram result-path durability incident — 2026-08-13

## Problem

A task-specific fixed-batch workflow reused one output pathname across several different `experiment_id` values. Each completed run replaced the prior result file. Git history still retained the older evidence, but review-inbox entries named the moving evidence branch plus the reused pathname, so later closeout could no longer verify the older registered hashes at that mutable ref.

## Repair

Fixed-batch result durability is now enforced in the runner rather than left to individual workflows:

- the canonical result path is derived from `experiment_id` as `state/experiments/<experiment_id>-results.json`;
- a workflow-supplied output path is accepted only if it is exactly that canonical path, and a mismatch fails before credentials or detector submission;
- each new result envelope records a deterministic SHA-256 fingerprint of the exact batch spec;
- reusing an `experiment_id` with a changed spec fails closed and requires a new experiment ID;
- an already-completed identical experiment can be reused without a detector call;
- the exact completed result is committed before lesson-review registration, and the inbox records that immutable result commit rather than a moving branch name.

## Verification

Focused result-path tests cover safe experiment IDs, canonical path derivation, mismatch rejection, spec fingerprint stability, changed-spec rejection, legacy fail-closed behavior, and identical completed-result reuse. The merged code-only GitHub Actions run passed the fixed-batch regression suite and skipped the paid detector job.

## Durable lesson

Evidence identity must be derived from experiment identity and bound to immutable bytes before semantic review is registered. A mutable branch plus a reusable result pathname is not durable provenance. Enforce uniqueness/fingerprinting before detector access rather than relying on workflow authors to remember naming conventions.
