# Idiolect proxy validation gap — 2026-08-17

## Status

The merged idiolect architecture is operational and correctly scoped, but its dependency-free single-author retention proxy is **not yet research-grade validated for Joel's registers**.

This is not a defect in the command's stated contract. The current implementation explicitly reports a directional proxy, not a calibrated pass threshold or paper-equivalent IER. The gap is that we do not yet know how reliably its two lightweight channels track style-sensitive held-out authorship attribution on natural Joel prose.

## Why the gap matters

The IER paper's most informative deep results use LUAR, while its main surface attribution uses TF-IDF character/word n-grams with a linear SVM. The merged local proxy instead uses profile cosine over dependency-free feature vectors so it can remain fast, private, deterministic, and usable during ordinary editing.

Those are different instruments. Agreement cannot be assumed.

The paper also shows why validation must control topic: Reuters authors remained highly attributable under LUAR in a setting where topic was strongly predictive, and content-sensitive representations can therefore conceal stylistic convergence.

## Current evidence state

Already merged and durable:

- three-axis separation of semantic/editorial fidelity, Pangram status, and authorship-signal retention;
- D0–D4 edit-dose policy;
- natural-owner/current-hybrid provenance separation;
- held-out corpus and privacy rules;
- dependency-free `idiolect-retention` command;
- dependency-free closed-set `idiolect-ier` command for its named local instrument;
- tests proving report identity/privacy and synthetic directional behavior;
- explicit warning that the local instrument is not numerically equivalent to paper TF-IDF/SVM or LUAR.

Not yet established:

- Joel-specific baseline authorship accuracy using paper-faithful surface SVM;
- Joel-specific LUAR attribution baseline;
- topic-matched human negative set;
- register-stratified validation;
- agreement/disagreement rates between the fast proxy and research-grade instruments;
- held-out calibration showing whether any operational threshold is justified;
- known false-negative and false-positive cases for the proxy.

## Decision

Keep the fast proxy as a directional D3/D4 diagnostic.

Do **not** promote it to a hard acceptance gate or imply that `candidate_minus_original >= 0` establishes preserved Joel voice.

Add a second-tier validation lane under `docs/IDIOLECT-VALIDATION-PROTOCOL.md` using:

- paper-faithful TF-IDF char 2–4 + word 1–2 + linear SVM;
- LUAR mean-author-profile nearest-neighbor attribution;
- semantic MiniLM/content baseline as a confound monitor, not a voice score;
- content-light/function-word controls;
- topic-matched human negatives;
- source-level holdouts and near-duplicate auditing;
- register-specific validation;
- repeated/resampled accuracy intervals;
- explicit proxy-vs-research-grade disagreement logging.

## Implementation boundary

Do not put PyTorch/Transformers/LUAR dependencies into the default Pangram environment. Research-grade validation belongs in an optional environment or isolated runner.

Do not blindly vendor the paper repository's source. Reimplement the paper-described method under a distinct local instrument identity and use the upstream repository as a reproducibility reference, preserving any paper/code discrepancy rather than silently selecting one.

## Completion criterion

This gap closes only when at least one named Joel register has:

1. a provenance-audited natural-owner corpus;
2. multiple human comparison authors with topic controls where feasible;
3. source-separated held-out validation;
4. meaningfully above-chance original attribution under a style-sensitive research-grade instrument;
5. Tier-A vs Tier-B agreement analysis on multiple edit doses;
6. held-out confirmation of whatever directional interpretation is proposed;
7. exact instrument, corpus-manifest, split, and result hashes.

Until then the canonical wording remains: **directional proxy only; research-grade calibration for this register is not yet established.**
