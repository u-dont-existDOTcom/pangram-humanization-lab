# Global tell-ledger comparison — repeatability

Date: 2026-09-23
Status: SECOND DIRECT-OPENROUTER REPEAT / SAME FROZEN PROMPT AND CASES / NO PANGRAM CALLS

A second independent run used the same frozen prompt, cases, temperature 0, models, and direct OpenRouter path.

## Claude Opus 5.5

- run A: **9/12** exact status;
- run B: **8/12** exact status;
- combined: **17/24 (70.8%)**;
- wrong-polarity calls: **0**;
- UNCERTAIN cells: **7**;
- identical status on repeat: **11/12** cells;
- two-run cost: **$0.575560**.

Only one Opus cell changed between repeats: the known-Human direct-advice cadence control moved from ABSENT to UNCERTAIN.

## GPT-6 Sol

- run A: **6/12** exact status;
- run B: **7/12** exact status;
- combined: **13/24 (54.2%)**;
- wrong-polarity calls: **9**;
- UNCERTAIN cells: **2**;
- identical status on repeat: **8/12** cells;
- two-run cost: **$0.195609**.

GPT changed status on 4 of 12 scored cells between repeats.

## Conclusion

The second run strengthens the bounded preference for **Claude Opus 5.5 as the fresh global tell-ledger sweep model**.

Across two repeats:
- Opus: **17/24 exact, 0 wrong polarity, 7 UNCERTAIN**;
- GPT-6 Sol: **13/24 exact, 9 wrong polarity, 2 UNCERTAIN**.

For this gate, cautious UNCERTAIN is preferable to a confident polarity reversal because UNCERTAIN remains unresolved and routes to focused/manual review. Opus is therefore materially safer in the tested configuration.

It is also about 3x as expensive in these runs. This remains a six-case bounded comparison, not universal model ranking.

The full tell catalog remains authoritative. Opus is an execution aid for the global sweep; narrow calibrated audits and editorial review resolve uncertainty. No Pangram calls were used.
