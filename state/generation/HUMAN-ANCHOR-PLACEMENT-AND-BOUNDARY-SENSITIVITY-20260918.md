# Human anchor placement and detector boundary sensitivity

Date: 2026-09-18
Status: **ACTIVE METHOD LESSON / TWO-SUBSECTION EVIDENCE**

## Second anchored convergence result

For `Write It. Don't Send It Yet`:

- six all-model candidates A–F: AI 1.0;
- owner supplied 113-word Human/medium anchor;
- anchored G: AI 0.6144040823;
- anchored H: AI 0.3021335304;
- opening-only I: AI 0.4466216266;
- opening-only J: AI 0.5706174374;
- structurally reassembled K: AI 0.0 / Human 1.0.

## What changed at K

K did not merely paraphrase the red opening again.

It changed boundary geometry:
- moved the exact Human anchor much earlier;
- reduced pre-anchor model prose to one minimal sentence;
- moved remaining editing functions to a short post-anchor model paragraph;
- preserved the already-strong inward-care ending.

This suggests that **where the Human anchor sits inside the tested boundary matters**, not only whether one exists.

When a red flank resists repeated local rewriting, moving semantic load across a fixed Human anchor can be more effective than further stylistic paraphrase.

## Strong caution: detector boundary sensitivity

After K reached Human 1.0, changing only:

`Lao Tsu` -> `Sun Tzu`

produced:
- AI 0.4598316848;
- Human 0.540168345;
- detector note: AI in later part.

Do not infer local causal blame from this.

A one-token edit can alter Pangram segmentation or contextual scoring non-locally.

Therefore:
- detector evidence binds exact bytes;
- tiny editorial corrections can invalidate an exact detector endpoint;
- a corrected version does not inherit a prior Human score;
- do not optimize individual tokens from non-local score shifts;
- preserve editorial authority over detector oddities.

## Practical method

For anchored convergence:
1. freeze known-Human in-boundary prose;
2. mutate only red model regions while measurements improve;
3. if repeated same-region rewrites regress, change **geometry**, not just diction;
4. remeasure the exact full boundary;
5. stop on Human endpoint or saturation;
6. treat later factual/editorial corrections as new exact boundaries.