# GUI score-time evidence capture rule — 2026-08-24

Status: durable workflow lesson from Romance r23 Part 2.

## Incident

The exact Romance r23 Part 2 GUI measurement completed successfully and stored Pangram 4.0 aggregate fractions showing Human `0.9965084195`, AI `0.0034915956`, with the rendered report stating there was one AI-generated segment. The paid GUI session already had the exact stored report open, but the runner persisted only the aggregate result, body text, and PDF before closing the browser.

Later attempts to recover the highlighted segment through authenticated History required separate self-hosted workflow jobs and hit the known exact-History-binding reliability problem tracked in issue #110. A subsequent standalone DOM inspector also spent queue time merely to reopen an already-paid report. None of these recovery attempts made another detector submission, but the latency and tooling complexity were avoidable.

## Durable rule

Evidence required to interpret a paid GUI result must be captured during the original GUI execution whenever practical, before the executor releases the scarce self-hosted runner.

For a completed exact GUI result with nonzero AI or AI-assisted fraction:

1. preserve the exact aggregate result first so auxiliary inspection cannot ambiguate paid-score authority;
2. while still in the same executor job, inspect the already-known stored report read-only and persist localization/highlight evidence needed for the next editorial decision;
3. push that evidence to the same content-addressed evidence branch before releasing the runner;
4. treat post-hoc authenticated History recovery as a fallback for interrupted/legacy runs, not the normal production path;
5. an auxiliary localization failure must never authorize or trigger a duplicate paid detector submission.

Exact-green results do not need this extra localization step unless another task specifically requires visual evidence.

## Implementation status

`u-dont-existDOTcom/pangram-private-executor` PR #25 changed the Romance long-GUI executor so non-green results receive immediate free report-DOM post-processing in the original self-hosted job before runner release. The auxiliary step is non-authoritative and cannot invalidate a completed paid score.

The current DOM heuristic itself still requires calibration against Pangram's live rendering: the first legacy inspector run classified Pangram's orange Overview/Details tab styling rather than the actual residual segment. That false positive is diagnostic evidence, not localization authority. The score-time capture architecture is correct; the highlight parser must fail closed until it can distinguish article-segment styling from navigation/theme styling.

## Generalization

This is not Romance-specific. Any GUI detector workflow that will need local evidence after a non-green score should capture that evidence at score time instead of discarding the live report state and later reconstructing it through a second queued browser job.
