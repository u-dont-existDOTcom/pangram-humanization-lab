# Idiolect-retention protocol

This protocol adds **authorship-signal retention** as a separate evaluation axis in Joel humanization work. It is grounded in Malik and Awan, *The Assistant Erased You: Measuring Loss of Authorship Signals in AI-Mediated Communication* (arXiv:2608.00926v1, 2026-08-02).

The paper's Idiolect Erasure Rate (IER) is the percentage-point drop in closed-set authorship-attribution accuracy from held-out originals to aligned AI rewrites. It is not a property of a model alone: the result depends on the assistant, rewrite condition, attributer, and corpus.

## Production objective: prevent erasure first

The production goal is **not** to make an authorship classifier approve prose. It is to avoid needless erasure by editing in a way that preserves the author's actual language and thought movement.

Primary prevention rules:

- reuse good natural owner prose rather than regenerating it;
- preserve owner thought route, sequence, under-specification, cadence, and stopping point;
- move intact prose when movement solves the architecture;
- use the minimum coherent edit dose;
- remove model aftercare, abstraction, and overcompletion rather than replacing them with new polish;
- restore owner wording or localize a repair when a rewrite becomes smoother but less distinctly Joel.

Authorship measurement is secondary evidence. It is useful only when the instrument can recognize the relevant natural-owner condition reliably enough for the result to affect a real decision.

## Three independent axes

Do not collapse these into one score:

1. **Meaning and authority:** claims, argument, certainty, provenance, rhetorical function, chronology, and owner-final language survive.
2. **AI-detector status:** the exact reader-visible delivery boundary meets Joel's current Pangram requirement when that requirement applies.
3. **Authorship-signal retention:** when measured, the candidate has not needlessly moved away from a held-out corpus of Joel's actual writing.

A candidate may pass Pangram while losing Joel's recoverable idiolect. It may retain measured authorship signal while remaining detector-red. It may preserve meaning while becoming generic. **Authorship retention and AI-detection are different tasks.**

Therefore idiolect-retention output does **not** substitute for Pangram. A future substitution or Pangram-skipping rule would require a separate empirical calibration showing that a named idiolect instrument predicts the relevant Pangram outcome with adequate reliability on held-out Joel-byline examples. Until then, use idiolect only for anti-erasure evidence, not as an AI detector.

## Edit-dose ladder

Use the lowest dose that solves the actual defect.

| Dose | Operation | Default authorship-retention handling |
|---|---|---|
| D0 | No visible prose change | None |
| D1 | Mechanical spelling, punctuation, capitalization, spacing, or literal agreement correction | Preserve wording and sentence architecture; no metric normally needed |
| D2 | Local repair of a sentence or short span | Reuse owner language; optional comparison when distinctive material changes |
| D3 | Sectional reconstruction, rerouting, consolidation, or substantial assistant rewriting | Apply the prevention rules and full editorial gates; retention measurement is optional/non-blocking unless an already-valid instrument could change a real decision |
| D4 | Full regeneration or article-wide rewrite | Presume high erasure risk; preserve natural-owner material and minimize regeneration; use valid retention evidence when available, but do not make unvalidated measurement a production prerequisite |

The dose is about transformation, not word count.

## Reference-corpus construction

Use texts that genuinely establish the target byline:

- Prefer `owner-authored untouched` and `owner-edited final` material.
- Match genre and register where possible.
- Exclude the evaluated original and near duplicates from the profile.
- Do not silently treat `assistant-produced owner-accepted` prose as natural idiolect evidence.
- Keep profile texts private. Reports store hashes and aggregates, not raw prose.
- More varied, independent samples are better. Fewer than three samples, less than 1,000 profile words, or a test boundary under 50 words is weak evidence rather than a pass/fail condition.

A profile is contextual evidence, not a bag of quirks to imitate. Never add errors, filler, catchphrases, odd punctuation, autobiographical details, or pet constructions merely to raise similarity.

## Optional single-author retention proxy

Use this only when the comparison is meaningful and decision-relevant:

```bash
pangram-lab idiolect-retention \
  --profile-dir path/to/private-joel-reference-texts \
  --original original-visible-text.txt \
  --candidate candidate-visible-text.txt \
  --output idiolect-retention.json
```

The report contains exact identities, edit-distance metadata, and original-vs-profile / candidate-vs-profile movement under two channels:

- `surface`: character 2–4-grams and word 1–2-grams; topic-sensitive;
- `content_light`: function words, punctuation, contractions, casing, rhythm bins, word-length bins, and reduced syntax; less topic-dependent but not a deep authorship representation.

Interpret `candidate_minus_original` as direction, not a calibrated pass score. Negative movement is evidence to inspect. Positive movement does not prove natural authorship, quality, fidelity, or detector-Human status.

If the result cannot change a real editorial decision, skip it and record `not measured / no validated gate`.

## Closed-set IER and LUAR/SVM work

Closed-set attribution is **research tooling**. Use it only for benchmark or method-development work with a predeclared reusable question, disjoint profile/evaluation samples, and aligned originals/rewrites.

True IER requires baseline attribution meaningfully above chance before rewrite degradation can be interpreted.

The completed four-author exact-50 LUAR calibration for Joel/Stian/David/Greg disconfirmed that named 50-word matched-Dharma condition as an operational unique-Joel gate. Do not keep adding controls, shortening windows, or launching article-specific rewrite probes merely to rescue an unstable condition.

Any future longer-boundary calibration must answer a concrete reusable research question; it is not required just because current article work is D3/D4.

## Decision procedure

For substantial production work:

1. Freeze the authoritative original and reader-visible comparison boundary.
2. Map meaning, protected functions, and architecture.
3. Identify natural owner prose and thought movement that can survive intact.
4. Make the smallest coherent edit.
5. Run semantic sanity, fidelity, architecture, and cold prose-shape audits.
6. Decide whether existing idiolect measurement is valid and decision-useful. If not, do not create a research detour.
7. If drift is suspected, restore owner wording, reduce dose, localize the repair, recover the owner realization, or separate structural movement from sentence rewriting.
8. Run Pangram only under its own authorization, boundary, cache, and paid-call rules when Pangram evidence is required.
9. Treat detector and idiolect evidence as separate results. Neither overrides meaning or owner authority.

When two candidates are equally faithful and coherent, prefer the lower-dose candidate; valid retention evidence may be one tie-breaker.

## Pangram substitution boundary

Idiolect retention can provide evidence that prose still resembles Joel's natural writing. That is relevant to whether the humanization process preserved the author. It is **not presently evidence that Pangram will classify the prose as Human**.

A future cheap pre-screen could reduce Pangram calls if, and only if, existing cached Joel candidates with both measurements demonstrate out-of-sample predictive value. Such a study should use already-cached Pangram results first and must report false negatives: any case where the idiolect rule would have skipped Pangram but Pangram later called the passage AI/Mixed is especially important.

Until such calibration exists:

- do not replace Pangram with idiolect retention;
- do not claim high idiolect retention means `sounds human` in the detector sense;
- do treat strong retention as evidence that humanization preserved more of Joel's recoverable author signal.

## Known limitations

- The paper measures computational attribution, not recognition by readers who know the author.
- Surface methods are confounded by topic, genre, source quoting, formatting, and repeated subject vocabulary.
- The local instrument does not reproduce LUAR's deep representation.
- Short passages and small or contaminated profiles are unstable.
- A metric can be gamed; optimizing directly for it can produce caricature or corpus mimicry.
- AI-detector status and authorship retention are orthogonal unless separately demonstrated otherwise on the target corpus.

## Repository boundary

- `u-dont-existDOTcom/joel-articles` owns editorial authority, edit-dose policy, corpus/provenance rules, and article acceptance.
- This repository owns measurement implementation, tests, metadata-only reports, detector evidence, and research-method limitations.
- A paper result or local metric never authorizes changing Joel's claims, certainty, politics, allegations, personal history, or argument.
