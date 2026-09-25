# Global tell-ledger max-effort comparison

Date: 2026-09-23
Status: BOUNDED MAX-EFFORT COMPARISON / SAME FROZEN TELL DEFINITIONS / NO PANGRAM CALLS

## Question

Before changing the tell catalog, test the simpler hypothesis:

> Did the earlier global-ledger misses primarily come from underpowered/adaptive reasoning rather than bad tell definitions?

The prompt, six cases, and twelve owner-grounded scored cells were held byte-identical to the prior comparison.

## Configuration

All three models:
- reasoning effort: `max`;
- max completion budget: 48,000 tokens;
- same frozen global tell prompt;
- same six cases;
- same pre-registered owner/editorial score key;
- no tools;
- no Pangram calls.

Provider routing:
- Claude Opus 5.5: direct OpenRouter;
- GPT-6 Sol: Venice via the canonical UDA Venice gateway;
- GPT-6 Astra: Venice via the canonical UDA Venice gateway.

## Result

| Model | Exact | UNCERTAIN | Wrong polarity |
|---|---:|---:|---:|
| Claude Opus 5.5 max | **11/12** | 1 | **0** |
| GPT-6 Sol max | 8/12 | 1 | 3 |
| GPT-6 Astra max | 7/12 | 1 | 4 |

### Claude Opus 5.5 max

- **11/12 exact (91.7%)**
- **0 wrong-polarity calls**
- one unresolved cell: Human seat-belt paragraph / cumulative manual-listicle cadence, expected ABSENT, returned UNCERTAIN.
- reasoning tokens across six cases: **136,240**
- OpenRouter reported cost: **$2.99572**

It correctly called:
- readiness manual/listicle cadence PRESENT;
- both dangerous-adult defects PRESENT;
- all six RT2 owner-known tells PRESENT;
- 5-MeO Human list cadence ABSENT;
- Human direct-advice cadence ABSENT.

### GPT-6 Sol max — Venice

- **8/12 exact (66.7%)**
- **3 wrong-polarity calls**
- one UNCERTAIN.

Wrong polarity:
- dangerous-adult abrupt complication expected PRESENT -> ABSENT;
- Human direct-advice cadence expected ABSENT -> PRESENT;
- Human seat-belt cadence expected ABSENT -> PRESENT.

RT2 scene-skinned staircase remained UNCERTAIN.

Reasoning tokens across six cases: **54,437**.

### GPT-6 Astra max — Venice

- **7/12 exact (58.3%)**
- **4 wrong-polarity calls**
- one UNCERTAIN.

Wrong polarity:
- dangerous-adult abrupt complication expected PRESENT -> ABSENT;
- Human 5-MeO hypothesis list cadence expected ABSENT -> PRESENT;
- Human direct-advice cadence expected ABSENT -> PRESENT;
- Human seat-belt cadence expected ABSENT -> PRESENT.

RT2 scene-skinned staircase remained UNCERTAIN.

Reasoning tokens across six cases: **52,163**.

## Comparison to adaptive/default reasoning

Earlier repeated adaptive/default global-ledger evidence:
- Opus 5.5: 17/24 exact across two runs, 0 wrong polarity, 7 UNCERTAIN;
- GPT-6 Sol: 13/24 exact, 9 wrong polarity, 2 UNCERTAIN.

Max effort materially improved Opus:
- from 8/12 and 9/12 on the two adaptive/default repeats
- to **11/12** max,
- while preserving **zero wrong-polarity** behavior.

Max effort also improved Sol relative to its prior 6/12 and 7/12 repeats, but it still made three confident polarity errors.

Astra max did not outperform Sol max on this task.

## Current decision

Do **not** rewrite the tell list wholesale yet.

The current tell definitions are capable of producing 11/12 correct owner-grounded judgments when executed by Opus 5.5 at max effort. That is strong evidence that model/effort was a major part of the earlier failure.

The one remaining Opus uncertainty is exactly the safe failure mode for this process:
- UNCERTAIN does not clear the tell;
- route it to a narrow calibrated cadence audit / direct editorial check.

Next method step:
1. keep the full current tell catalog unchanged;
2. use Opus 5.5 max as the preferred fresh full-ledger sweep when cost/latency is justified;
3. treat PRESENT and UNCERTAIN as unresolved until dispositioned;
4. expand tell-level calibration coverage before editing definitions;
5. change a tell definition only when repeated max-effort evidence shows that specific tell is systematically ambiguous or mis-specified.

This is a small six-case / twelve-cell benchmark, not universal accuracy evidence.
