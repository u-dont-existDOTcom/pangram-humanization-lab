# Pangram repository-secret access-routing incident — 2026-08-13

## Status

Promoted operational lesson.

## Incident

A worker could reasonably read the existing editorial detector gate and conclude that Pangram was unavailable after finding no usable local `PANGRAM_API_KEY` and a signed-out Pangram dashboard. That conclusion was wrong: this repository already had a proven GitHub Actions route in which the repository secret is injected into trusted fixed-batch code without being exposed to the worker.

The instruction defect was not a missing detector-completion rule. It was a missing access-resolution gate.

## Controlled evidence

- Branch `automation/pangram-fixed-batch` contains `.github/workflows/pangram-fixed-batch.yml`.
- The workflow supplies `${{ secrets.PANGRAM_API_KEY }}` only through step-level environments for its non-billable secret check and detector run—never at workflow or job scope—and checks that it is non-empty without printing it before invoking `scripts/run_fixed_batch.py`.
- The runner performs the non-billable authentication probe, uses the Pangram 4 client, content-addressed cache, recorded task IDs, and Git checkpoints.
- The client explicitly requests Pangram 4, requires terminal detector version `4.0`, resumes known pending task IDs, and does not automatically retry ambiguous POST requests.
- GitHub Actions run `31661055171` completed both `Verify Pangram secret is configured` and `Run starting-scenarios batch` successfully.
- The proven executions inspected were push-triggered. The presence of `workflow_dispatch` on the feature branch is not treated as proof that manual dispatch is the current canonical route.

## Promoted rule

Missing or rejected local credentials and a signed-out dashboard do not establish Pangram unavailability. Before using the label `pre-Pangram candidate`, a worker must complete both the direct/local route and the repository-secret Actions route in `docs/PANGRAM-ACTIONS-RUNBOOK.md`, or record the concrete blocker that made each route unusable.

The repository secret must remain inside GitHub Actions. Workers must never retrieve, print, commit, or ask Joel to paste it.

## Scope

This is an operational access and provenance lesson. It does not change the editorial rule that coherence, fidelity, and semantic sanity precede detector testing, nor does it make a Pangram result editorial approval.
