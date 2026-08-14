# Current state

## Goal

Keep Pangram experiments resumable, nonduplicative, semantically faithful, and mechanically closed out into durable project and universal lessons.

## Baseline

- Canonical branch: `main`
- Long-lived evidence branch: `automation/pangram-fixed-batch`
- Lesson entry point: `state/LESSON-INDEX.md`
- Complete deterministic gate: `python -m pytest -q`

## Current checkpoint

The lesson ledger, changed-range gate, weekly orphan audit, cache, and task-ID checkpointing are operational. The active governance change adds an exact agent map and prepares CI for immutable pins and bounded jobs.

## Blocker

The `process-requests` job currently commits generated lesson state directly to `main`. Normal protection of `main` must not be enabled until processing is moved to a pull-request branch or another explicitly reviewed path.

## Next safe action

Harden the existing workflow without losing metadata processing, then verify the PR and redesign the direct-write path before enabling branch protection.
