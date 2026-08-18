# Natural-neighbor authorship calibration — bounded existing-work scan

Date: 2026-08-18

## Independent conception snapshot

Problem: the current closed-set instrument can classify a Joel rewrite as Stian even while its similarity to Joel increases. Joel reports that Stian naturally writes/thinks somewhat like him and that this affinity is part of why they clicked. Therefore a nearest-author flip may represent ambiguity inside a naturally similar author pair rather than simple genericization or idiolect erasure.

Candidate mechanism before search:

- separate target-author similarity from target-versus-alternative identity margin;
- characterize natural-original confusion before interpreting aligned rewrites;
- retain naturally similar authors as hard negatives;
- score every comparison author rather than preserving only the winner;
- exclude already ambiguous originals from clean erasure claims;
- report whether a rewrite's winning alternative was already a stable natural-original neighbor.

Constraints:

- no universal threshold;
- no raw prose or embeddings in Git;
- source-group-held-out evaluation;
- register/platform conditions remain explicit;
- semantic/editorial fidelity and owner authority remain independent and controlling;
- avoid a new heavy model run unless existing frozen evidence lacks a required field.

## Existing work reviewed

### Authorship verification and the impostors method

Koppel and Winter's *Determining if Two Documents Are Written by the Same Author* treats the problem as verification against alternative authors rather than trusting a forced nearest-author label in isolation. The associated impostors logic is directly relevant: difficult alternative authors are evidence, not noise to remove.

Reusable remainder:

- compare the target against multiple plausible impostors/hard negatives;
- reason from repeated comparative evidence rather than one absolute similarity;
- preserve alternative-author competition explicitly.

### PAN authorship-verification evaluations

The PAN authorship-verification tasks operationalize same-author/different-author decisions under explicit corpora and conditions. Their central relevance here is the separation between verification confidence/calibration and raw closed-set winner accuracy.

Reusable remainder:

- condition-specific evaluation;
- score-distribution and calibration discipline;
- abstention/ambiguity instead of forced certainty;
- corpus and cross-domain limitations reported with the result.

### LUAR

Rivera-Soto and colleagues' *Learning Universal Authorship Representations* supplies the existing metric-embedding architecture already used in this repository: author/document representations, cosine comparison, and nearest-profile classification. It does not make every nearest-profile flip interpretable as erasure.

Reusable remainder:

- frozen model/revision and profile identities;
- complete score vectors against every author;
- profile-profile cosine matrices;
- held-out original attribution before aligned rewrite analysis.

### IER research already integrated into Joel Articles

Malik and Awan's *The Assistant Erased You* defines idiolect erasure as an attribution-accuracy drop between held-out originals and aligned rewrites. The Joel Articles protocol already records the key boundary: the original attribution condition must be valid enough to support a degradation claim.

Reusable remainder:

- aligned original/rewrite conditions;
- attribution-drop interpretation only after reliable original performance;
- separate corpus, register, assistant/edit condition, and attributer identity.

### Adjacent metric-learning practice

Hard-negative mining in metric learning deliberately retains examples close to the target representation because they reveal whether the model separates identity rather than merely broad class membership. The transferable principle is useful; model-training machinery is not automatically required for this diagnostic.

Reusable remainder:

- distinguish easy and hard negatives;
- inspect pairwise margins and rank the closest alternatives;
- do not improve apparent accuracy by deleting the difficult neighbor.

## Already solved by established work

- comparing a target author against alternative/impostor authors;
- preserving complete comparative scores rather than one target score;
- treating naturally difficult negatives as informative;
- separating verification/calibration from raw nearest-neighbor classification;
- requiring held-out originals before aligned rewrite degradation;
- reporting condition and corpus dependence.

## Partially solved or condition-dependent

- how much Joel and Stian are naturally confusable across independent registers and platforms;
- whether their similarity is stable outside shared Dharma threads;
- whether apparent closeness reflects broad intellectual/topic affinity, discourse-community accommodation, deeper stylistic similarity, or some combination;
- how much evidence length is needed for stable separation;
- which current Joel register has enough independent human controls for held-out validation.

## Incompatible shortcuts

- removing Stian because he reduces accuracy;
- calling every Joel-to-Stian flip erasure;
- treating a Joel-only cosine increase as successful retention;
- inventing a universal positive-margin cutoff;
- averaging disagreeing surface, content-light, and LUAR instruments;
- interpreting shared-thread similarity as proof of why the authors became similar;
- using owner-reported affinity as a substitute for empirical attribution evidence.

## Genuinely unresolved remainder for this project

The project-specific remainder is not a new authorship algorithm. It is a calibrated evaluation design that combines:

1. Joel's owner-supplied natural-neighbor hypothesis;
2. source-frozen, register-labeled natural originals;
3. empirically ranked hard negatives;
4. aligned humanization edits;
5. exact per-author score and margin movement;
6. an ambiguity gate preventing naturally confusable originals from becoming false erasure cases.

## Build / adapt / reuse decision

**Decision: adapt and compose.**

Reuse LUAR and the existing source-frozen corpus machinery. Adapt verification/impostor and hard-negative diagnostics into a metadata-only report. Compose those with the existing IER eligibility boundary. Do not invent or operationalize an `author-neighborhood score` unless ordinary confusion matrices, pairwise score distributions, margins, and resampling stability later prove insufficient.

## Strongest current baseline

The baseline is not the current Joel-only similarity proxy. It is:

- source-group-held-out natural originals;
- at least three comparison authors;
- complete per-author LUAR scores;
- original confusion/margin distributions;
- explicit hard-negative ranking;
- aligned rewrite deltas counted only for originals predeclared as reliably attributable.

Any later bespoke neighborhood summary must demonstrate added decision value over that baseline before adoption.
