# Claude Code CLI effort + rubric-operationalization checkpoint — 2026-09-24

Status: ITERATION EVIDENCE / CLI ROUTE LIVE / RUBRIC V2 NOT PROMOTED / NO PANGRAM CALLS

## Owner outcome

Use the cheapest provider-native Claude Code CLI configuration that safely applies the full Joel post-generation tell ledger, then improve the judge procedure so lower effort does not require wasteful max reasoning.

No hidden-authorship classifier is being revived. This remains a tell-by-tell editorial audit.

## Route and frozen benchmark

Claude Code CLI authentication was restored through first-party claude.ai subscription auth.

The existing six-case / twelve owner-grounded-cell benchmark was reused byte-for-byte:
- prompt SHA-256: `b2d3de84afe7798b8910b7a22370ad83b3e2afe1a6b62eb98a6b5f67bef09e9f`
- cases SHA-256: `8bb8a3ba99e617de68c2d146efc15a31d929e72a8dda02c91b039c6d7b0ddd2f`
- key SHA-256: `ca5fc8d02ccc27d54dda46beb6e352c225d1cac2d3452b5083db14fb35420606`

Each case used a fresh non-persistent Claude CLI session with:
- model `claude-opus-5-5`;
- neutral `/tmp` working directory;
- safe/restricted mode;
- strict MCP isolation;
- tools disabled for the benchmark;
- structured output;
- no resumed session.

## CLI effort results

| Effort | Run | Exact | UNCERTAIN | Wrong polarity | Total elapsed | Thinking tokens | Output tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| medium | 1 | 9/12 | 3 | 0 | 158.135 s | 3,930 | 13,269 |
| high | 1 | 10/12 | 2 | 0 | 156.634 s | 5,837 | 13,435 |
| high | 2 | 10/12 | 2 | 0 | 167.788 s | 6,111 | 13,927 |
| xhigh | 1 | 10/12 | 2 | 0 | 218.876 s | 11,759 | 20,598 |

High and xhigh both remained fail-safe on the scored cells: zero wrong-polarity calls. Xhigh did not improve exact score or unresolved count and used roughly twice the thinking tokens of high while taking materially longer.

The two high runs missed different positive cells in the RT2 cluster, so the unresolved cells are not perfectly stable. Both high runs consistently:
- caught both dangerous-adult scored defects;
- accepted all three Human cadence controls;
- never confidently cleared an owner-known positive tell.

### Current route decision

For the Claude Code subscription-CLI route, **high is the current provisional default** for the full global tell-ledger sweep.

Do not run max routinely. Max remains an escalation only when a high-effort unresolved/disputed tell can actually change detector admission or another consequential decision.

This is CLI-specific evidence. OpenRouter API routing remains separately calibrated at xhigh default / max escalation.

## V2 operational rubric experiment

Claude was asked to convert fuzzy tell judgments into explicit gates/subtests and restrict UNCERTAIN.

The first V2 was tested at Claude CLI high on a new six-case held-out set covering T01, T10 and T11.

Held-out source basis:
- T01 PRESENT: direct owner correction against first-person preference/permission wrappers;
- T01 ABSENT: owner-authored Romance first-person cognition;
- T10 PRESENT: exact generic `you don't have to X before Y` permission realization rejected in the checking retrospective;
- T10 provisional ABSENT: owner-preferred Romance advice;
- T11 PRESENT: generic cancer connective-tissue sentence;
- T11 ABSENT: owner/editorially required Romance temporal transition.

### V1 vs V2 on that held-out set

| Arm | Exact | Wrong polarity | UNCERTAIN | Elapsed | Thinking tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V1 / original prompt | 3/6 | 2 | 1 | 197.393 s | 5,686 | 13,566 |
| V2 / full explicit subtest prompt | 3/6 | 3 | 0 | 259.869 s | 8,340 | 25,235 |

**V2 is rejected as a production replacement.** It was slower, much more verbose, and did not improve held-out exactness.

### What V2 nevertheless taught

The failed holdout localized three procedural ambiguities:

1. **T01** — the judge incorrectly treats “the author is talking about their own therapy” as proof first person is necessary. Owner authority says a personal `I want / I get to / I don't get to` wrapper can still be model-shaped when it merely carries a general criterion.
2. **T11** — “names a causal relation” is too weak a content test. A generic relevance bridge can say `X is why Y matters` while adding no subject-matter state change. The useful discriminator is whether the sentence supplies a needed change in time/case/premise/causal state, plus a deletion test.
3. **T10** — the provisional Romance negative control is not a sound T10 ABSENT label merely because Joel authored/preferred it. V1 and V2 both read it as permission packaging. Treat this cell as CONTESTED and exclude it from rubric scoring until tell-specific owner/editorial adjudication exists.

A second Claude design pass therefore recommended:
- depersonalization/general-criterion testing for T01;
- portability + genuine local logical anchor for T10;
- state-change + deletion tests for T11;
- tell-specific control labels rather than provenance or overall preference.

## Compact V2.1 direction

Do not promote the 189-line V2.

V2.1 should keep the original compact V1 prompt and add only generalized operational clarifications that have decision value:
- T01: distinguish author-specific cognition/evidence from a general criterion wearing first person;
- T02: three-or-more consecutive teaching moves; logical step dependency is not counter-evidence; real anecdote/hypothesis/surplus breaks the run;
- T04: reconstruct the observable checklist from prose; lack of a source ledger is not grounds for UNCERTAIN;
- T08: mild/brief explanatory aftercare still counts; a genuinely new claim/consequence does not;
- T10: test whether permission logic is portable versus dependent on a specific prior mechanism/exception/order;
- T11: state-change + deletion test;
- globally restrict UNCERTAIN to genuine deciding ambiguity or materially missing context.

The next validation must use fresh controls not seen by the V2.1 prompt designer. Do not reuse the first held-out set as evidence of generalization after tuning.

## Jev role

Existing Jev 1.13 evidence remains:
- 9/12 exact;
- 3 wrong-polarity calls, all false ABSENTs;
- 0 UNCERTAIN;
- about $0.00073 total for six twelve-tell cases.

Among the twelve scored cells:
- known positives: 9;
- Jev caught 6/9;
- known negatives: 3;
- Jev correctly left all 3 ABSENT.

Thus Jev is useful as a **cheap positive pre-screen**:
- a Jev PRESENT can trigger immediate editorial inspection/repair before spending a Claude full-ledger sweep;
- a Jev ABSENT cannot clear a tell or candidate;
- Jev does not currently replace or validate Opus;
- no ensemble-accuracy improvement has yet been demonstrated.

Its practical savings come from avoiding expensive Opus iterations on candidates Jev already flags correctly, not from skipping the final high-rigor sweep on a candidate that Jev calls clean.

## Current blocker

During compact V2.1 materialization, the local Remote Desktop/connected-device route dropped and reported zero connected devices. No API fallback was substituted for Claude.

Raw CLI result files remain local and should be committed when the device route returns. This checkpoint records the completed numeric evidence but does not claim raw-artifact closeout.

## Next safe action

1. recover the local device route;
2. materialize compact V2.1;
3. freeze a genuinely fresh second holdout with tell-specific labels;
4. compare V1 vs compact V2.1 at CLI high;
5. only if V2.1 improves without introducing wrong-polarity calls, run the old six-case benchmark as regression;
6. preserve raw outputs and scoring artifacts;
7. update the production fresh-critic gate only after the new procedure has held on unseen controls.

No Pangram calls were used in this work.
