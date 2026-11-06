# Claude CLI global tell rubric optimization — V1 -> V2 -> compact V2.1

Date: 2026-09-24
Status: **ACTIVE METHOD EXPERIMENT / V2 REJECTED / V2.1 FROZEN CANDIDATE AWAITING FRESH HOLDOUT / NO PANGRAM CALLS**

## Parent outcome

Make the full T01–T12 post-generation tell sweep easier for Claude Opus 5.5 to execute safely on the provider-native subscription CLI, so routine evaluation does not require max effort.

This is not hidden-authorship classification. PRESENT and UNCERTAIN remain unresolved; direct editorial review and calibrated narrow audits remain downstream.

## Why optimize the judge procedure

On the unchanged six-case development benchmark:
- medium CLI: 9/12 exact, 3 UNCERTAIN, 0 wrong polarity;
- high CLI: 10/12 exact, 2 UNCERTAIN, 0 wrong polarity on two runs;
- xhigh CLI: 10/12 exact, 2 UNCERTAIN, 0 wrong polarity.

The remaining uncertainty did not respond monotonically to more effort. That made judge-procedure ambiguity a live hypothesis.

A bounded literature scan also supported decomposition/calibration/uncertainty-aware evaluation rather than forcing one global judgment. This is compositional prior art, not a novelty claim.

## Expanded V2 — rejected

Claude proposed a fully operationalized V2 with explicit subtests for every tell and a verbose structured receipt.

A new six-cell owner/editorial holdout was frozen before comparing V1 vs V2 at CLI high effort.

### Held-out score

V1 high:
- 3/6 exact;
- 2 wrong-polarity;
- 1 UNCERTAIN;
- 13,566 output tokens;
- 5,686 thinking tokens;
- 197.393 seconds.

Expanded V2 high:
- 3/6 exact;
- 3 wrong-polarity;
- 0 UNCERTAIN;
- 25,235 output tokens;
- 8,340 thinking tokens;
- 259.869 seconds.

V2 therefore produced no exact-accuracy gain, converted one fail-safe uncertainty into a confident error, used about 86% more output tokens and about 47% more thinking tokens, and was slower. **V2 is rejected and must not be promoted.**

## Control-quality audit after the miss

The first holdout is now consumed development evidence and is not a valid validation set for a later revision.

Important label/protocol findings:
- the T10 negative control was weak/maybe malformed under the original broad wording because a negative-imperative reassurance can plausibly instantiate permission packaging; do not optimize a judge merely to force that label;
- the T01 positive control tested a real owner correction but also exposed that V1 did not operationalize the distinction between author-specific evidence and a general criterion wrapped in first person;
- T11 positive/negative controls were the strongest operational pair: generic structural linkage versus a necessary time/case/premise transition;
- four of six original holdout targets came from two source families, so transfer evidence was weak;
- judging only one keyed cell per target hid unscored false positives. Future scoring should preserve the primary pre-registered cells but inspect all unexpected PRESENTs before promotion.

## Compact V2.1 hypothesis

Instead of keeping V2's full subtest bureaucracy, V2.1 returns to V1 and makes only targeted execution clarifications:

- T01: identity-substitution test — first person is suspicious when replacing `I want / I care / I need` with a generic agent leaves the same general criterion; author-specific observation/history/reaction remains legitimate;
- T10: narrow the tell to actual necessity/permission release, especially prerequisite-release relations; a plain negative imperative is not automatically permission syntax;
- T11: deletion/state-change test — a necessary transition changes time, stage, case, condition, or premise such that deleting it misattaches what follows; a sentence that merely justifies document structure remains generic connective tissue;
- T02/T09: explicit minimum target scale rather than vague uncertainty from short spans;
- T04: observable scene-translation/causation test; absence of the hidden source ledger cannot by itself produce UNCERTAIN;
- UNCERTAIN: allowed only for a genuine evidence split that changes the status or truly missing supplied context; mildness/shortness/missing ledger are not uncertainty reasons;
- output: minimal JSON rather than per-tell subtest telemetry.

Exact frozen candidate: `GLOBAL-TELL-PROMPT-V21-CANDIDATE.txt`.
Exact character count: **7,132 bytes/characters in the local UTF-8 ASCII-compatible prompt file before repository persistence**.

This candidate was produced after the first holdout was inspected. It is development material, not validated evidence.

## Fresh second holdout — frozen, not run

A small decision-specific second holdout was frozen from a different source pool:
- natural community-essay material;
- natural oral-transcript material;
- controlled synthetic one-variable mutations based on community logic.

Primary scored axes:
- T01 PRESENT/ABSENT;
- T10 PRESENT/ABSENT;
- T11 PRESENT/ABSENT.

Regression cells:
- T02 ABSENT;
- T09 ABSENT.

The full frozen spec/key is `V21-HOLDOUT2-SPEC-20260924.json`.

Execution order:
1. run V2.1 at Claude Code CLI high effort;
2. score the pre-registered cells and inspect unexpected PRESENTs;
3. run V1 on the same frozen holdout only if the V2.1 result is good enough that the baseline comparison can change the routing decision;
4. do not run CLI max unless high leaves a decision-changing gap after the rubric question is resolved.

## Current blocker

At launch of the second holdout, the authorized Desktop Commander relay to the owner's laptop went offline. No second-holdout Claude call had started, so there is no ambiguous inference or duplicate-call recovery problem.

Do not substitute OpenRouter merely to bypass this local transport outage; the experiment is specifically about the provider-native Claude CLI surface.

## Promotion boundary

V2.1 is **not production-valid** until the fresh second holdout executes successfully and supports the change.

Do not update the production fresh-critic gate or claim a new CLI default from this branch yet.
