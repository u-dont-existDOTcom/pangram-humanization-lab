# Humanization method fingerprint — preserve the structure of a successful correction loop

Status: PROVISIONAL / owner-taught process lesson
Date: 2026-09-16

## Triggering evidence

In the Inner Child Therapy manual-humanization loop, the successful late-stage Episode 007 process was more specific than the shorthand `write instructions, then apply them later`.

The useful instruction form was:

`literal current sentence/span -> explicit operation -> concrete positive generation target`

Typical operations were `keep`, `merge`, `rewrite`, `compress`, `delete as separate sentence`, `re-sequence`, or `demote`.

The positive target described what the replacement should *do* in the reader's experience, rather than supplying only prohibitions such as `don't sound academic`, `avoid listicles`, or `make it more human`.

After those instructions were frozen, applying them on a later owner turn produced materially better results in Episode 007. A later Episode 008 attempt preserved only the turn-separation dimension while applying a broader section-level guide. That was not a faithful reproduction of the successful method even though it was initially described as such.

## Failure mechanism

The method was compressed into one salient abstraction: `write repair instructions, then apply them on the next turn`.

That compression lost other defining dimensions:

- literal sentence/span anchoring;
- one explicit operation per span;
- positive, concrete replacement jobs;
- preserving stronger attacks/rejected alternatives rather than only the winning edit;
- applying the frozen guide without silently rewriting it during generation.

As a result, an older available guide could satisfy the *label* of the method without satisfying its structure.

## Current method fingerprint

When this process is intentionally reused or tested, verify all of the following before calling it the same method:

1. **Literal target anchoring** — work from the exact current sentence/span, not only a section-level diagnosis.
2. **Explicit operation** — mark the local move: keep, merge, rewrite, compress, delete as a separate sentence, re-sequence, demote, etc.
3. **Positive generation target** — specify the sentence's intended job in concrete reader-facing terms. Prefer `put the reader inside one recognizable state, then let the practical consequence follow` over `avoid abstraction`.
4. **Instruction freeze** — finish and preserve the repair table before generation.
5. **Phase separation when being tested** — if the experiment concerns critic/writer separation, cross a genuine owner turn or fresh context before applying the guide. Same-turn role-play is not independent.
6. **Literal application** — apply the frozen table without redesigning the instructions while drafting.
7. **Preservation proof** — re-run source->candidate and candidate->authority traceability with zero unexplained substantive deltas.
8. **Adversarial cold audit** — identify the strongest remaining attacks on the candidate, including plausible stronger alternatives and why they were rejected.
9. **Detector only after editorial admission** — do not spend Pangram while a concrete model-shaped defect is still believed present.

## Episode 008 R7 result — method fidelity is not sufficient by itself

R7 was the first Episode 008 pass to reproduce this method fingerprint faithfully across a real owner-turn boundary. It remained preservation-clean and froze the prior known-green somatic material. Joel's Pangram screenshot nevertheless showed 1719 UI words split as:

- 334 AI / High from the opening;
- 32 Human Written / Medium beginning `Sometimes you need more bottom-up...`;
- 1353 AI / High beginning `If your body is still too clenched for tal...`.

By displayed segment word share, that is approximately 98.14% AI / 1.86% Human. Therefore the method fingerprint is **not a guarantee of detector success on a long practical-guide boundary**. It is an execution discipline that makes failures more interpretable and produces cleaner local teaching evidence.

A text-first prediction frozen before deliberate screenshot inspection correctly anticipated the broad red opening, a tiny somatic Human island—especially the `Sometimes you need more bottom-up...` paragraph—and a broad red tail beginning at the roadmap transition. Because the screenshot was attached in the same turn, this is non-isolated prediction evidence, not a genuinely independent blind test. The useful fact is narrower: the critic can now localize the large-scale guide-shape failure much better than the generator can remove it.

## Minimal aligned owner repair versus broad voice dump

Current owner proposal: if further model-only minimal repair stalls, prefer **small same-thought owner edits** over a broad rough audio/voice dump for the purpose of teaching the humanization transformation.

This is strongly consistent with the existing retrieval-first alignment classes:

- A minimal owner edit that preserves essentially the same thought can be captured as `ALIGNED_SAME_THOUGHT`, giving a clean literal model-before -> owner-after pair.
- A broad audio/voice dump is likely to add, remove, reprioritize, reroute, or contextualize thought. That can be excellent authorial source material, but it will often classify as `OWNER_REAUTHORING` rather than clean realization evidence.

Therefore the current order for **generation learning** is:

1. try one bounded model minimal-repair pass when the critic has a specific, preservation-safe hypothesis;
2. if it remains red, ask Joel for minimal same-thought corrections to selected spans and capture each aligned pair prospectively;
3. use broader audio/voice input for Target #2 ownerization, new authorial cognition, or when the thought itself—not merely its realization—is missing.

This order is provisional until more aligned repairs transfer successfully, but it is methodologically cleaner than treating all fresh owner language as equivalent training evidence.

## General lesson

**Method identity must be structural, not label-based.**

When a workflow succeeds, save a compact fingerprint of the operations that made it distinct. On reuse, compare the current plan against that fingerprint. If a defining dimension is missing, call the new run a method variant rather than treating it as evidence for or against the original method.

This matters especially when several factors can be confused:

- turn/context separation;
- instruction granularity;
- positive versus negative guidance;
- sentence-local versus section-level repair;
- preservation gating;
- post-generation adversarial audit.

A failure of one variant does not falsify another unless the relevant factors actually match. Conversely, a faithful method reproduction that still fails Pangram falsifies the claim that the method alone is sufficient for that boundary; do not respond by silently weakening method identity or inventing another label for the same execution.

## Relationship to retrieval-first owner teaching

This supplements `state/generation/RETRIEVAL-FIRST-OWNER-TEACHING-PROTOCOL.md`.

The existing episode rule preserves literal before/after/transfer prose. This method fingerprint preserves the **execution shape** of a successful owner-teaching loop so future workers do not retrieve the right prose lesson but apply it through a materially different repair architecture.

## Evidence pointers

- `u-dont-existDOTcom/joel-articles:articles/inner-child-therapy/experiments/EPISODE-007-OWNER-SENTENCE-REWRITE-GUIDE-20260916.md`
- `u-dont-existDOTcom/joel-articles:articles/inner-child-therapy/experiments/EPISODE-008-R3-TO-R4-SENTENCE-REPAIR-GUIDE-20260916.md`
- `u-dont-existDOTcom/joel-articles:articles/inner-child-therapy/experiments/EPISODE-008-R6-TO-R7-POSITIVE-SENTENCE-REPAIR-GUIDE-20260916.md`
- `u-dont-existDOTcom/joel-articles:articles/inner-child-therapy/experiments/EPISODE-008-R7-OWNER-SCREENSHOT-RESULT-20260916.json`
- `u-dont-existDOTcom/joel-articles:articles/inner-child-therapy/experiments/EPISODE-008-R7-TO-R8-MINIMAL-REPAIR-GUIDE-20260916.md`

Episode 008 R8 detector outcome remains pending. The current lesson is process evidence plus one negative long-boundary result; it is not yet proof that the proposed minimal-repair pass will succeed.
