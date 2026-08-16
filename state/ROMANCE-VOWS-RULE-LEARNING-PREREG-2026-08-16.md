# Romance Vows — rule-learning preregistration

**Date:** 2026-08-16  
**Mode:** detector-rule research; no article prose authority
**Owner learning allowance:** 20 new calls without renewed approval; this batch plans 8.

## Why another experiment is justified

The direct Joel Vows rewrite is already the editorial endpoint and tested Pangram 4.0 Human `1.0`. Prior controlled work isolated two mechanisms: formal source-certification wording and cumulative closing overcompletion. Those mechanisms do not explain the large remaining difference between the prior assistant candidate and Joel's direct rewrite.

There is still useful, non-lexical uncertainty around the middle of the section. Two changes are especially editorially meaningful and recur in other Romance repairs:

1. **interpretive aftercare around an example** — the assistant tells the reader what the insecurity means before the example and then supplies a four-sentence interpretation after it; Joel compresses the setup to `open up` and lets the example carry the thought;
2. **lived route vs normalized diagnosis** — Joel's B./jealousy account retains causal/personal details and an uneven aside; the assistant version smooths the same movement into a cleaner diagnostic account.

The first has a strong transferable editorial hypothesis. The second is worth testing mainly to determine whether lived/idiosyncratic detail is actually detector-causal here or merely correlated with Joel's rewrite.

## Fixed source endpoints

- Human/editorial endpoint: direct Joel rewrite, SHA-256 `1101efe49418bc47df63acb4c9916a1e39b2e8c4b64ac6ca1ff39e669e05dc95`.
- Assistant developmental source: exact candidate preserved in `state/ROMANCE-VOWS-AUTHORITY-RESTORATION-2026-08-16.md`.
- Detector probes are synthetic evidence only and never supersede either source.

## Research questions

### RQ1 — full-boundary cluster swaps

On the exact owner-full backbone, what happens if only the assistant **story/diagnosis cluster**, only the assistant **disclosure/aftercare cluster**, or both are restored?

Precommitted interpretations:

- assistant story alone regresses, disclosure does not → lived route/diagnostic realization is the stronger local detector mechanism;
- disclosure alone regresses, story does not → interpretive completion around the example is the stronger mechanism;
- neither alone regresses but both together do → interaction/cumulative normalization;
- both alone regress → independent mechanisms;
- all remain Human → these middle rewrites improved editorial quality/voice but do not explain the full detector flip by themselves.

The exact old assistant full candidate is also measured as an anchor because the prior owner-visible screenshot/PDF was not preserved as a raw lab task.

### RQ2 — disclosure 2×2

Fixed owner-local boundary around the jealousy disclosure example. Factors:

- **A0 compact setup:** `Instead of stewing in jealousy and throwing out microaggressions now and then, open up.`
- **A1 explicit interpretive setup:** `Instead of stewing in jealousy and throwing out microaggressions now and then, say the actual thing without hiding the insecurity behind anger.`
- **B0 no post-example aftercare**
- **B1 restore assistant post-example interpretation:** `Maybe he really is neglecting you... Every couple has to work out for themselves what actually feels healthy.`

This yields A0B0, A1B0, A0B1, A1B1.

Primary hypothesis: B will matter more than A because B repeats/interprets what the example and preceding paragraph already establish. A may be null because both setup sentences perform a real instruction, though A1 is more explanatory.

Interaction hypothesis: A1+B1 may be worse than either alone because the reader is told how to interpret the insecurity on both sides of an example that already demonstrates it.

## Constraints

- Preserve the full local boundary; do not test isolated one-line snippets.
- Do not add invented memories, facts, jokes, or idiolect.
- No phrase-level inference from this batch.
- If a full-boundary cluster effect appears, decompose by **function** next, not by individual unusual words.
- If no cluster effect appears, treat that as a useful falsification and move to a cross-boundary holdout rather than forcing a Vows-local rule.
- No more than 8 new calls in this batch.
- Stop/adapt after reading the exact windows; remaining owner allowance after this batch will be at least 12 calls.

## Planned section IDs

- `vows-rule-full-cluster-swaps` — 4 variants/new calls.
- `vows-rule-disclosure-factorial` — 4 variants/new calls.

These are genuinely distinct boundaries: complete Vows versus a local factorial around one example. They are not cap-reset aliases.
