# Claude Opus 5.5 reasoning-effort ladder — global tell sweep

Date: 2026-09-23
Status: BOUNDED EFFORT-SELECTION EVIDENCE / NO PANGRAM CALLS

## Parent decision

Determine the **lowest Opus reasoning effort that preserves the safe full tell-ledger behavior** on the existing frozen six-case / twelve owner-grounded tell benchmark.

The tell definitions, cases, scoring cells, temperature, model ID, and output contract were unchanged.

## Results

| Effort | Exact | UNCERTAIN | Wrong polarity | Reported cost | Reasoning tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| low | 7/12 | 5 | 0 | $0.15488 | 0 reported |
| medium | 9/12 | 3 | 0 | $0.29074 | 4,530 |
| high | 8/12 | 4 | 0 | $0.32154 | 5,262 |
| xhigh run 1 | 11/12 | 1 | 0 | $0.44996 | 10,992 |
| xhigh run 2 | 10/12 | 2 | 0 | $0.48104 | 12,372 |
| max | 11/12 | 1 | 0 | $2.99572 | 136,240 |

The effort ladder is not perfectly monotonic on exact accuracy: medium exceeded high in this sample. That is another reason not to infer quality from effort labels alone.

## Decision

**Use `xhigh` as the default high-rigor Opus 5.5 full-ledger sweep.**

Evidence:
- xhigh entered the same fail-safe regime as max: zero wrong-polarity calls;
- two xhigh runs scored 11/12 and 10/12;
- max scored 11/12;
- xhigh cost roughly $0.45–$0.48 for the six-case benchmark versus ~$3.00 for max.

Therefore max is not justified as the routine default.

Use `max` only as escalation when:
- xhigh leaves an important tell UNCERTAIN;
- direct editorial review materially disputes an xhigh result;
- the unresolved tell could change Pangram admission or another consequential decision;
- the extra cost/latency is justified by that decision.

Do not escalate merely because max exists.

## Tell-definition consequence

This experiment does **not** support rewriting the tell catalog.

Across the tested cells:
- lower effort mostly converted known answers into UNCERTAIN rather than revealing systematic definition failures;
- xhigh/max both reached high exact accuracy with zero polarity reversals.

The next bottleneck remains calibration coverage:
- T02 has strong two-sided controls;
- T03–T09 are positive-only;
- T01 and T10–T12 are unscored.

Build two-sided owner/editorial controls for those tells before changing wording. Revise a tell only if it continues to fail after good positive and negative controls exist for that exact operation.

## Limits

This is six passages / twelve scored tell cells. It selects the current project default; it is not a universal reasoning-effort benchmark.

No Pangram calls were used.
