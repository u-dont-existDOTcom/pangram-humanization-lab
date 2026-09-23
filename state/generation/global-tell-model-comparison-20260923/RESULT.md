# Global tell-ledger model comparison — Claude Opus 5.5 vs GPT-6 Sol

Date: 2026-09-23
Status: BOUNDED DEVELOPMENT COMPARISON / DIRECT OPENROUTER / NO PANGRAM CALLS

## Question

Can a strong fresh model execute the **original global tell-ledger task** better than the GPT critic that false-passed the Inner Child safety prose?

This is not hidden-authorship classification. Each model receives the same current tell inventory and must emit one PRESENT / ABSENT / UNCERTAIN judgment for every tell, with no global Human/AI vote.

## Frozen setup

- direct OpenRouter HTTPS from the authorized local machine; no Railway inference route;
- models:
  - `anthropic/claude-opus-5.5`
  - `openai/gpt-6-sol`
- prompt SHA-256: `b2d3de84afe7798b8910b7a22370ad83b3e2afe1a6b62eb98a6b5f67bef09e9f`
- cases SHA-256: `8bb8a3ba99e617de68c2d146efc15a31d929e72a8dda02c91b039c6d7b0ddd2f`
- gold-key SHA-256: `ca5fc8d02ccc27d54dda46beb6e352c225d1cac2d3452b5083db14fb35420606`
- six prose cases;
- twelve pre-registered scored tell cells;
- no Pangram calls.

Ground truth is limited to tells already established by owner/editorial records. Unscored extra model findings are not automatically treated as right or wrong.

## Strict score

`UNCERTAIN` counts as incorrect against an expected PRESENT or ABSENT.

- Claude Opus 5.5: **9/12 (75%)**
- GPT-6 Sol: **6/12 (50%)**

Observed OpenRouter cost for the six requests:
- Claude Opus 5.5: **$0.285420**
- GPT-6 Sol: **$0.092146**

## More useful gate-oriented comparison

For a pre-Pangram tell sweep, `UNCERTAIN` should remain unresolved and route to focused review rather than being silently treated as absence.

Under that interpretation:

### Claude Opus 5.5

Across all 12 known cells:
- correct polarity: 9;
- unresolved/UNCERTAIN: 3;
- **wrong polarity: 0**.

Specifically:
- readiness AI-N16/manual cadence: UNCERTAIN rather than the owner-known PRESENT;
- dangerous-adult AI-N16 and AI-N17: both PRESENT;
- RT2 owner-known T04–T09 bundle: five PRESENT, scene-skinned staircase T04 UNCERTAIN;
- Human 5-MeO hypothesis-list T02: ABSENT;
- Human direct-advice T02: ABSENT;
- Human seat-belt T02: UNCERTAIN rather than known ABSENT.

So Claude did not hard-clear any known-positive tell and did not hard-flag the known-negative cadence controls. Its errors were caution/indecision, not polarity reversals.

### GPT-6 Sol

Across the same 12 cells:
- correct polarity: 6;
- unresolved/UNCERTAIN: 1;
- **wrong polarity: 5**.

Wrong-polarity examples included:
- dangerous-adult AI-N16: ABSENT;
- dangerous-adult AI-N17: ABSENT;
- RT2 scene-skinned staircase: ABSENT;
- RT2 equalized efficiency: ABSENT;
- Human seat-belt AI-N16: PRESENT.

## Interpretation

On this small, owner-grounded comparison, **Claude Opus 5.5 is materially better suited than GPT-6 Sol to the one-call global tell-ledger sweep**.

It is still not safe as a sole certifier:
- it called the readiness manual cadence UNCERTAIN rather than PRESENT;
- it called the RT2 scene-skinned staircase UNCERTAIN rather than PRESENT;
- it also called the Human seat-belt cadence UNCERTAIN rather than ABSENT.

The useful architecture is therefore the owner's original full-catalog process with explicit uncertainty handling:

1. run the complete tell ledger on the literal natural boundary;
2. every tell gets PRESENT / ABSENT / UNCERTAIN;
3. PRESENT is editorially inspected and repaired when real;
4. UNCERTAIN is **not a pass**; resolve it with a focused tell-family audit / direct editorial check;
5. only ABSENT or a specifically justified false-positive resolution clears that tell;
6. no overall Human/AI vote may override the ledger.

Current bounded evidence supports Claude Opus 5.5 as the preferred fresh **global sweep** model while this exact configuration remains relevant, with calibrated narrow auditors as follow-up rather than replacements for the full list.

This does not establish universal accuracy or detector predictiveness.
