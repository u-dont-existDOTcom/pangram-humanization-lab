# Idiolect-erasure paper integration — 2026-08-17

## Source reviewed

Malik, Ushna, and Moiz Sadiq Awan, *The Assistant Erased You: Measuring Loss of Authorship Signals in AI-Mediated Communication*, arXiv:2608.00926 (2026), plus the authors' released reproducibility repository `ushnamalikk/idiolect-erasure-rate`.

This record captures what is transferable into Joel's humanization architecture and what remains experimental.

## Relevant findings

The paper defines Idiolect Erasure Rate (IER) as the drop in held-out authorship-attribution accuracy after AI-assisted rewriting. It reports both surface stylometry and LUAR deep-authorship attribution.

In the heavy-rewrite condition:

- Blog surface attribution fell by 38.5 percentage points and LUAR by 66.5 points.
- Enron surface attribution fell by 28.7 points and LUAR by 52.5 points.
- Reuters C50 surface attribution fell by 10.0 points while LUAR changed only 1.0 point, not significantly; topic remained strongly predictive of journalist identity.

Other findings directly relevant to this lab:

- light grammar-only rewriting erased substantially less signal than heavy rewriting;
- explicit `preserve the author's voice` prompting reduced some surface erasure but still left most deep authorship signal unrecovered;
- high semantic similarity can coexist with large authorship-signal loss;
- function-word checks still showed degradation when topical information was minimized;
- content-sensitive encoders such as MiniLM can understate idiolect erosion;
- the authors use `double erasure` for AI-assisted text that becomes difficult both to attribute to the human author and to identify as AI-assisted;
- IER is instrument-, corpus-, condition-, and assistant-specific and measures computational attributability rather than human recognition.

## Why this changes our architecture

The current Pangram lab already separates detector score from meaning, provenance, architecture, and owner authority. The paper identifies another independent failure plane: **authorship signal can disappear even when semantic content remains.**

That matters especially for this project because the task is not merely to make generic AI prose look human. It is to preserve a named author's byline voice while repairing model-shaped prose.

A Pangram improvement therefore cannot be treated as a complete humanization improvement if the candidate simultaneously becomes less distinguishable as Joel.

## Promoted principles

1. **Idiolect preservation is separate from detector passing and semantic similarity.** Named-author humanization must preserve distinguishable author signal as its own objective.
2. **Rewrite dose is a controlled variable.** Prefer the minimum transformation that fixes the real defect; generic heavy polishing is an adverse-risk condition, not a default.
3. **A voice-preservation prompt is not preservation evidence.** Measure or audit the result.
4. **Authorship measurement must be style-sensitive and topic-controlled.** Topic similarity must not masquerade as voice.
5. **Reference-corpus provenance matters.** Natural Joel writing must remain separable from assistant-produced, owner-accepted, and detector-targeted material.
6. **IER has a narrow definition.** Do not attach the term to one passage or one similarity score.
7. **Detector green plus idiolect loss is a byline failure.** It may be described as double-erasure-like only with the paper's terminology limits made explicit.

## Provisional elements

The following are not promoted as proven Joel-specific effects:

- any numerical Joel IER threshold;
- any single-pass LUAR/profile-similarity cutoff;
- any claim that a particular Joel phrase is an authorship marker;
- any requirement to preserve typos, awkwardness, or surface quirks;
- any claim that computational attribution equals human recognition;
- any use of a semantic encoder alone as a voice metric.

A quantitative gate requires a validated Joel corpus and negative set first.

## Repository split

### `pangram-humanization-lab`

Owns:

- `docs/IDIOLECT-PRESERVATION-PROTOCOL.md`;
- calibration design and future optional attribution tooling;
- raw/derived idiolect experiment evidence;
- lesson disposition and detector/idiolect interaction research.

### `joel-articles`

Owns:

- the byline-level editorial rule that idiolect preservation is a separate objective;
- minimum-edit and provenance safeguards;
- integration with article architecture/fidelity gates;
- routing to the calibrated Pangram-lab protocol when quantitative evidence exists.

## Implementation decision

Do **not** vendor the paper repository or add its heavy ML dependencies to the Pangram lab's default install now. The released project is a research protocol with dependencies including scikit-learn and LUAR-related PyTorch/Transformers tooling, while this lab's default runtime is deliberately lightweight.

First build a corpus/provenance manifest and validate that a Joel-specific attributer can distinguish style rather than topic. Only then add an optional `idiolect` research extra or isolated runner.

This also avoids blindly importing implementation details: the released repository should be treated as a reproducibility reference, while our scorer must match this lab's provenance, privacy, register, and evidence requirements.

## Next implementation checkpoint

1. Inventory eligible natural Joel writing by register and provenance.
2. Define topic-matched human negatives and source-separated train/test splits.
3. Run surface stylometry, function-word/content-light controls, LUAR, and a content-sensitive confound baseline.
4. Establish baseline accuracy and stability before calculating any Joel IER.
5. Retrospectively test known natural, assistant-heavy, owner-final, and detector-repair pairs.
6. If the instruments behave sensibly, integrate idiolect-retention evidence into prospective Pangram candidate selection as a separate axis rather than a replacement score.
