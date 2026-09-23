# Jev typed tell-ledger benchmark

Date: 2026-09-23
Status: BOUNDED ADVISORY COMPARISON / NO PANGRAM CALLS

## Setup

Same six frozen cases and same twelve owner/editorially grounded scored tell cells as the Opus/GPT global-ledger comparison.

Model/API:
- `typesafe/jev-1.13`
- OpenRouter Decisions API
- one independent typed `choice` question per tell: PRESENT / ABSENT / UNCERTAIN
- explicit per-tell criteria
- no global Human/AI classification

One 5-MeO control initially returned provider HTTP 529; the exact unchanged case was retried once and succeeded. The 529 is transport-only evidence.

## Score

- **9/12 exact (75%)**
- **3 wrong-polarity calls**
- **0 UNCERTAIN**
- total reported cost across the six successful decisions calls: approximately **$0.00073**

Wrong-polarity cells:
- dangerous-adult abrupt complication: expected PRESENT -> ABSENT;
- RT2 scene-skinned semantic staircase: expected PRESENT -> ABSENT;
- RT2 equalized/optimal semantic efficiency: expected PRESENT -> ABSENT.

Correctly handled:
- readiness manual/listicle cadence PRESENT;
- dangerous-adult manual/listicle cadence PRESENT;
- RT2 synthetic props, generic therapeutic abstraction, simulated spontaneity, and explanatory aftercare PRESENT;
- all three Human cadence controls ABSENT.

## Interpretation

Jev is **useful but not safe as a clearing gate**.

Its advantages:
- extremely cheap;
- sub-second to ~1.5 s per 12-tell case;
- returns a typed choice, probabilities, and confidence per tell;
- can cheaply surface likely PRESENT tells for follow-up.

Its limitation in this benchmark:
- it made three confident false-ABSENT calls on owner-known defects;
- unlike Opus max, it did not fail safely to UNCERTAIN.

Practical use:
- optional cheap **positive triage/advisory signal**;
- a Jev PRESENT can prioritize a tell for inspection;
- a Jev ABSENT must **not** clear a tell;
- do not let Jev override Opus max, calibrated narrow audit, or direct editorial judgment.

No Pangram calls were used.
