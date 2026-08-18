# Transformation-sensitivity owner interpretation — Stian near-neighbor correction

Date: 2026-08-18

## Authority

Joel's direct correction outranks the earlier assistant interpretation:

> It is kind of normal that Stian is writing like me. That's why I clicked with him.

This is an owner statement about the relationship and a plausible explanation for why Stian is a naturally difficult comparison author. It is not by itself empirical proof that the two writers have the same idiolect or that homophily rather than mutual accommodation caused the similarity.

## Preserved evidence

Do not alter the exact PR #79 result or its historical hashes. In the frozen oxytocin microbenchmark, the owner one-pass rewrite:

- increased cosine similarity to the Joel profile by `+0.09258`;
- increased similarity to Stian slightly more;
- reduced the Joel-versus-winning-alternative margin by `-0.011757`;
- changed the nearest profile from Joel to Stian.

The controlled topology deltas also remain unchanged:

- conditional restart only: `-0.001667` Joel-margin delta;
- sentence split only: `+0.004656`;
- combined topology: `+0.002139`.

## Corrected interpretation

The Joel-to-Stian flip does **not** establish straightforward movement away from Joel's voice, genericization, or idiolect erasure. Stian is plausibly a natural stylistic/intellectual near-neighbor. The rewrite may have moved within a region in which the current instrument already has difficulty uniquely separating the two authors.

The result still establishes an important negative finding: a rise in similarity to Joel is not sufficient evidence of preserved Joel identity, because similarity can rise to several naturally similar authors at once. `Joel-likeness`, unique Joel identifiability, and retention within a broader author-neighborhood are different questions.

Stian must remain in the benchmark as a high-value hard negative. Removing him because he is confusable would make the attribution problem artificially easy and would hide the exact ambiguity the benchmark needs to characterize.

## Required next diagnostic

Before interpreting another aligned rewrite:

1. establish natural-original Joel-versus-Stian confusion and margin distributions across independent held-out source groups;
2. preserve each original's score against every author rather than only the winner;
3. distinguish easy negatives from empirically hard negatives;
4. compare shared-thread and non-overlap material where possible, without claiming that this identifies the cause of the similarity;
5. report target-score movement, target-versus-nearest-alternative margin movement, and whether the alternative was already a natural-original near-neighbor;
6. count an aligned case toward rewrite-degradation or IER only when the original is reliably attributable under a predeclared held-out/resampling condition.

A naturally ambiguous original remains useful diagnostic evidence, but a later nearest-author flip from such an original is not a clean erasure event.

## Method choice

Adapt and compose established authorship-verification, hard-negative/impostor, metric-embedding, and score-calibration practice. Do not invent an operational `author-neighborhood score` or universal margin threshold before the ordinary confusion/margin diagnostics are exhausted.

## Cost and privacy boundary

Reuse frozen scores and embeddings where the existing artifacts contain them. Do not buy another heavy GitHub Actions run merely to recreate available evidence. Raw prose and embeddings remain local; durable reports contain hashes, source groups, score vectors or matrices, margins, counts, and uncertainty only.
