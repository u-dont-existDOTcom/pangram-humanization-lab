# Current state

## Baseline

- Canonical branch: `main`
- Evidence branch: `automation/pangram-fixed-batch`
- Lesson entry point: `state/LESSON-INDEX.md`
- Complete test gate: `python -m pytest -q`

## Current checkpoint

The active governance change adds the exact agent map, immutable Action pins, bounded jobs, serialized workflow runs, and metadata processing on the originating pull-request branch.

Workflow run 31757140867 completed successfully: `process-requests` and `change-gate` both passed on the final PR head.

## Next action

Merge the verified PR, then configure the validated checks for canonical-branch changes.
