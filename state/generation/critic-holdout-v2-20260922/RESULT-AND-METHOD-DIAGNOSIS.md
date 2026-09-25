# Humanization critic provenance holdout v2 — result

Date: 2026-09-23
Status: COMPLETED UNTOUCHED HOLDOUT / FAILED CALIBRATION / RUBRIC V2 RETIRED / NO PANGRAM CALLS

## Frozen identities

- blind set SHA-256: `9afcdc6662c2a3df916b7cfd31037c630c19bef7182c657653d65b15da5e571a`
- hidden key pre-run SHA-256: `288d15e33131ad499eba59d41ccb58e9cfd21f63cd31ed2fc9c5c65e68ddf7a0`
- rubric-v2 prompt SHA-256: `64f7d6cfdc8f577ee2fe6d5c4f6a0306205fe418937f86618c5120aaa48329e4`
- frozen response record SHA-256: `2059a9406ea97c22ddbd62daf898a0fb715a733cc59c832ec55319a4b7d262d4`
- blind response-freeze commit before key reveal: `e320d4429d25fecf8ca70cb8b31fc1932f630ff8`
- key branch: `evidence/humanization-critic-holdout-v2-key-20260922-2350`
- key commit: `c9c490298be73b8599b3ad48273ed807eb2910a8`
- model alias: `gpt-5.6-sol`
- provider model: `openai-gpt-56-sol`
- temperature: 0
- valid calls: 20
- transport errors during the valid run: 0
- Pangram calls: 0

## Score

- total: **10/20 = 50%**
- Human: **1/10**
- AI: **9/10**
- false AI on Human: 9
- false Human on AI: 1

This rubric is **not** a production gate.

## Relationship to v1

Benchmark v1:
- 14/20 overall;
- Human 10/10;
- AI 4/10.

Holdout v2:
- 10/20 overall;
- Human 1/10;
- AI 9/10.

The attempted repair did not improve discrimination. It largely inverted the error direction.

V1 over-credited model-simulated Human-facing features.
V2 over-penalized coherent/efficient structure in genuine Human prose.

## Causal instruction failure

The v2 content-neutralized scaffold test was made too strong.

Reducing prose to sentence jobs is useful for revealing hidden instruction-manual topology, but **almost any coherent Human paragraph can be post-hoc summarized as a clean functional sequence**. V2 then demanded that Human evidence materially “break” that scaffold. This quietly encoded a false theory: genuine Human prose should contain functionally unnecessary surplus, visible inefficiency, or residue that defeats a clean abstract summary.

The holdout falsifies that theory. Direct/natural Joel prose can be:
- highly functional;
- compact;
- causal;
- instructional;
- self-contained;
- carefully sequenced;
- rhetorically complete.

Those properties cannot be used as an absolute AI veto.

The content-neutralization step also deletes information that can be genuinely diagnostic: not merely vivid nouns, but the **specific relations among details, stakes, context, and authorial history**. Once those are replaced with placeholders, Human thought can be made to look artificially generic by the audit itself.

## Method consequence

Do not repair v2 by adding another exception list to the abstract rubric.

The two benchmarks show an oscillation:
- permissive abstract weighting -> false Human on model prose;
- hard scaffold veto -> false AI on Human prose.

That reaches the method-escalation threshold. The next development method must be structurally different.

Recommended next architecture: **contrastive literal-example classification**.

Instead of asking the critic to decide from an expanding abstract rule stack:
1. supply several provenance-secure matched Human/AI realization pairs from development data;
2. keep topic overlap inside pairs where possible;
3. ask the critic to compare the target's thought movement against both literal classes;
4. forbid phrase/topic matching and require relational/topological comparison;
5. use the abstract tell library only as secondary vocabulary for explaining the comparison, not as a veto system.

First test this architecture on development data that is not included in its calibration examples. Only after it demonstrates strong development discrimination should a new untouched holdout v3 be frozen.

## Production state

There is currently **no externally calibrated fresh critic** authorized to gate Pangram admission.

Until a new architecture passes a new untouched 20/20 provenance holdout:
- fresh-critic non-detection is advisory only;
- internal editorial/model-shape review remains blocking;
- Pangram remains downstream and cannot be used to compensate for a failed critic;
- the Inner Child dangerous-adult section stays paused from paid Pangram work.
