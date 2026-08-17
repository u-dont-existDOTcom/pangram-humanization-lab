# Idiolect-erasure research integration — 2026-08-17

## Source

Ushna Malik and Moiz Sadiq Awan, “The Assistant Erased You: Measuring Loss of Authorship Signals in AI-Mediated Communication,” arXiv:2608.00926v1, submitted 2026-08-02.

- Paper: https://arxiv.org/abs/2608.00926
- Public protocol/code: https://github.com/ushnamalikk/idiolect-erasure-rate
- The upstream repository is MIT-licensed. The implementation added here is independent standard-library code rather than copied upstream source.

## What the paper establishes

The paper defines Idiolect Erasure Rate (IER) as:

> baseline authorship-attribution accuracy on held-out originals minus attribution accuracy on aligned AI rewrites, in percentage points.

IER is explicitly instrument- and corpus-dependent. It is a property of the assistant, rewriting condition, attributer, and corpus together, not an intrinsic score for an assistant.

The main heavy-rewrite results were:

| Corpus | Surface IER | Deep LUAR IER |
|---|---:|---:|
| Personal blogs | +38.5 pp | +66.5 pp |
| Enron email | +28.7 pp | +52.5 pp |
| Reuters C50 news | +10.0 pp | +1.0 pp, not significant |

The Reuters result is an important control: topic can continue to predict author identity even when style is weakened. Content-sensitive attribution can therefore understate stylistic erasure.

Other findings material to this repository:

- Grammar-only correction erased substantially less signal than heavy generative rewriting.
- A prompt explicitly instructing the assistant to preserve the author’s voice reduced surface erasure but left most deep authorship signal unrecovered.
- Rewrites remained semantically similar while authorship attribution fell, supporting stylistic convergence rather than simple content loss as the main explanation.
- Function-word attribution also degraded, strengthening the style-loss interpretation.
- The effect appeared across Qwen models, GPT-4o-mini, and Gemini Flash.
- Aggregating rewritten blog messages saturated near 50% author identification, while originals reached 100% by eight messages in the reported setup.
- Heavy rewrites could also evade AI-text detectors, creating “double erasure”: weaker human-author attribution and weaker AI-assistance detection.
- The measure captures computational attributability, not recognition by familiar human readers.
- Preserving identity can conflict with privacy or anonymity; it is not universally desirable.

## Why existing Pangram practice was incomplete

The repository already protects semantic fidelity, owner authority, rhetorical function, whole-article architecture, and exact Pangram acceptance boundaries. Those controls remain necessary.

They do not directly test whether a candidate still carries recoverable authorship signals. Pangram asks whether text appears Human/AI-assisted under its instrument. IER asks whether a known author's text remains distinguishable from other authors after rewriting. A passage can satisfy one and fail the other.

This produces a three-axis model:

1. semantic/editorial fidelity;
2. AI-detector outcome;
3. authorship-signal retention.

No axis can certify either of the others.

## Promoted workflow lesson

A “preserve the author’s voice” prompt is an instruction, not evidence that voice was preserved. Humanization should use the minimum necessary edit dose, prefer actual owner language and thought routes, and separately record meaning/fidelity, detector status, and authorship-retention evidence.

For substantial AI-mediated reconstruction:

- build a held-out, genre-relevant corpus of genuine owner writing;
- exclude the evaluated original and near duplicates;
- compare original and candidate against that profile;
- inspect measured movement without imposing an uncalibrated pass threshold;
- reduce or localize the rewrite when it drifts needlessly;
- never inject errors, catchphrases, fake specificity, memories, or quirks to improve a score;
- keep a true closed-set IER experiment separate from a single-author retention proxy.

## Implemented instrument

`src/pangram_lab/idiolect.py` adds two standard-library paths:

### `idiolect-retention`

A single-author comparison for routine Joel work. It reports:

- profile, original, and candidate SHA-256 identities;
- token-change fraction, length ratio, and lexical-set overlap;
- profile similarity for a topic-sensitive `surface` channel;
- profile similarity for a more content-light function-word/punctuation/rhythm channel;
- corpus-size and boundary-quality flags;
- no raw source prose;
- no universal pass threshold.

This is explicitly a **retention proxy**, not IER, because it does not classify among multiple known authors.

### `idiolect-ier`

A closed-set multi-author attribution-drop calculation. It uses nearest-author cosine against equal-sample profile centroids, reports baseline and rewritten accuracy plus IER in percentage points, and preserves its instrument identity. It is not numerically equivalent to the paper’s TF-IDF/linear-SVM or LUAR models.

## Non-conclusions

Do not infer:

- that a high similarity score proves Joel wrote a passage;
- that low similarity authorizes changing an owner-final sentence;
- that deeper-model attribution can be replaced by the local surface proxy;
- that one fixed threshold can govern every genre, article, or boundary;
- that lower token-change fraction always means better editing;
- that Joel's most frequent quirks should be copied into every passage;
- that Pangram 100% Human means idiolect was retained;
- that measurable idiolect preservation is always desirable outside Joel's chosen byline objective.

## Validation boundary

The focused deterministic tests cover:

- identical-text zero-edit/full-relative-retention behavior;
- expected movement away from a synthetic author profile under a polished generic rewrite;
- metadata-only reports with hashes and no raw source text;
- a synthetic closed-set case with a 100-percentage-point attribution drop;
- rejection of a one-author “IER” dataset.

Full repository tests, repository audit, lesson closeout, and exact-head GitHub Actions remain the merge gate.
