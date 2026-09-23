# Claude Opus 5.5 reasoning-effort sweep — global tell ledger

Date: 2026-09-23
Status: BOUNDED PROJECT EVIDENCE / SAME FROZEN SIX-CASE BENCHMARK / NO PANGRAM CALLS

## Parent decision

Determine whether Claude Opus 5.5 must run at `reasoning.effort=max` for the full tell-ledger sweep, or whether a lower reasoning level is sufficient for routine production use.

The tell definitions, six cases, 12 owner/editorially grounded scored cells, temperature, model, and 48,000-token completion ceiling were held constant. Only `reasoning.effort` changed.

## Results

| Effort | Exact | Wrong polarity | UNCERTAIN | Reported cost / six-case run | Notes |
|---|---:|---:|---:|---:|---|
| max | **11/12** | **0** | 1 | **$2.99572** | strongest resolution; only seat-belt cadence control remained uncertain |
| high | 8/12 | **1** | 3 | $0.31792 | non-monotonic degradation; falsely called readiness cadence ABSENT |
| medium run 1 | 9/12 | **0** | 3 | $0.30736 | no confident polarity errors |
| medium run 2 | 9/12 | **0** | 3 | $0.29074 | no confident polarity errors |
| low | 7/12 | **0** | 5 | $0.15488 | safe directionally but too indecisive for efficient routine use |

Medium repeatability:
- combined: **18/24 exact**;
- **0 wrong-polarity calls**;
- 6 UNCERTAIN;
- same status on **10/12** cells across repeats;
- two-run cost: **$0.59810**.

## Interpretation

Reasoning quality is **not monotonic** in the OpenRouter effort labels on this task. Explicit `high` was worse than `medium` and worse in polarity safety than prior adaptive/default Opus runs.

Therefore do not infer that `high` sits neatly between medium and max in realized behavior.

The practical production tradeoff is:

- `max` resolves more of the ledger, but costs about **10x medium** on this benchmark;
- `medium` was repeatably conservative: no wrong-polarity calls in 24 scored cells across two runs;
- `low` was also directionally safe in its single run but left 5/12 grounded cells unresolved.

## Current routing recommendation

For this Joel/Pangram full tell-ledger task:

1. **Routine fresh global sweep: Opus 5.5 medium.**
2. Any `PRESENT` remains a blocking repair candidate.
3. Any `UNCERTAIN` remains unresolved and routes to:
   - a calibrated narrow auditor for that tell when available; or
   - Opus max on the disputed span/tell when a narrow auditor is unavailable or the decision is consequential.
4. Use **Opus max** for especially high-consequence final sweeps or when unresolved tells remain after medium/narrow review.
5. Do not use explicit `high` as the default merely because its label sounds stronger than medium; this benchmark does not support that ordering.
6. `low` may be useful for cheap exploratory triage, but current evidence does not justify it as the routine clearing sweep.

This routing is project-specific and provisional on broader tell-level calibration.

## Relation to tell-list quality

These results further weaken the hypothesis that the current tell definitions broadly need rewriting. Max reached 11/12 without changing the tells, while medium remained polarity-safe across two runs.

The next method bottleneck remains **tell-level calibration coverage**, not wholesale definition rewrite:
- T02 is strongly two-sided calibrated;
- T03–T09 are positive-only;
- T01 and T10–T12 are unscored.

Expand positive/negative controls before changing definitions.

No Pangram calls were used.
