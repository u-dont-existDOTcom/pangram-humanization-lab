# Claude Code CLI tell-ledger effort calibration — 2026-09-24

Status: **PROVISIONAL CLI-SURFACE CALIBRATION / SAME FROZEN SIX-CASE DEVELOPMENT BENCHMARK / NO PANGRAM CALLS / NO METERED MODEL API**

## Purpose

Recalibrate Claude Opus 5.5 effort on the provider-native Claude Code subscription CLI rather than transferring the earlier OpenRouter effort ladder across surfaces.

## Route and isolation

Local Claude Code CLI on the owner's authenticated `claude.ai` Max subscription:
- model: `claude-opus-5-5`;
- one fresh non-resumed process per case;
- `--safe-mode`, `--restricted`, strict MCP, tools disabled for scored judge runs;
- no session persistence;
- neutral `/tmp` workspace;
- structured output;
- no OpenRouter/Venice call;
- exact frozen prompt/cases reused.

Frozen identities:
- prompt SHA-256: `b2d3de84afe7798b8910b7a22370ad83b3e2afe1a6b62eb98a6b5f67bef09e9f`
- cases SHA-256: `8bb8a3ba99e617de68c2c146efc15a31d929e72a8dda02c91b039c6d7b0ddd2f`
- owner/editorial key SHA-256: `ca5fc8d02ccc27d54dda46beb6e352c225d1cac2d3452b5083db14fb35420606`

## Results

| CLI effort | Exact | UNCERTAIN | Wrong polarity | Total elapsed | Thinking tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| medium | 9/12 | 3 | 0 | 158.135 s | 3,930 | 13,269 |
| high run 1 | 10/12 | 2 | 0 | 156.634 s | 5,837 | 13,435 |
| high run 2 | 10/12 | 2 | 0 | 167.788 s | 6,111 | 13,927 |
| xhigh | 10/12 | 2 | 0 | 218.876 s | 11,759 | 20,598 |

High repeated the same fail-safe score. Xhigh used about twice the thinking tokens of high and did not improve exact accuracy or wrong-polarity behavior.

The unresolved cells moved somewhat between runs, so this is not evidence that a particular uncertainty is intrinsically unresolvable. It does show that simply increasing CLI effort from high to xhigh did not improve this development benchmark.

## Current routing implication

**High is the provisional Claude Code CLI target effort for rubric development and fresh evaluation.**

Do not promote this to a production clearing default yet. The benchmark is the same six-case development set used for earlier model comparisons. Fresh tell-level controls remain necessary.

A Claude Code CLI max run was deliberately **not** launched. The earlier OpenRouter max result (11/12, zero wrong polarity, one UNCERTAIN) is a different provider surface and does not justify paying the CLI max-token cost after xhigh failed to improve high here.

## Limits

- six passages / twelve scored cells;
- T02 is strongly two-sided; most other original cells are positive-only;
- this measures the original V1 full-ledger prompt, not a revised rubric;
- exact output quality cannot be inferred from effort labels alone.

No Pangram calls were used.
