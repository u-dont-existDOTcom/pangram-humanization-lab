# Idiolect Preservation Protocol

Status: **provisional quantitative protocol; active qualitative guard.**

This protocol adapts the Idiolect Erasure Rate (IER) research of Ushna Malik and Moiz Sadiq Awan to Joel Rosenblum's byline work. It is intentionally separate from Pangram: Pangram asks whether a boundary looks AI-generated to one detector; this protocol asks whether editing has weakened the computational and editorial signals that distinguish Joel from other writers.

The quantitative layer is **not yet a completion gate**. It becomes eligible for gating only after a Joel-specific calibration corpus, negative set, held-out split, and baseline accuracy have passed the calibration requirements below. Until then, the minimum-edit and source-provenance rules are active editorial safeguards, not numerical claims.

Research source:

- Malik, Ushna, and Moiz Sadiq Awan. *The Assistant Erased You: Measuring Loss of Authorship Signals in AI-Mediated Communication*. arXiv:2608.00926, 2026.
- Reproducibility repository: `ushnamalikk/idiolect-erasure-rate` (MIT).

## 1. What this protocol is meant to catch

Detector-only optimization has an obvious failure mode for named-author work: a candidate can move toward a detector's Human class while also moving away from the author's own stable language patterns.

For Joel's byline, "humanization" therefore has at least three independent targets:

1. preserve the actual thought, claims, causality, chronology, rhetorical functions, and owner authority;
2. preserve Joel-specific authorship signal rather than converging toward generic polished prose;
3. satisfy Pangram on the exact reader-visible delivery boundary when Pangram success is requested.

A fourth objective is **minimum necessary transformation**. If two candidates satisfy the first three objectives, prefer the one that changes less without retaining a known defect.

No detector, attributer, or similarity score may authorize a meaning change.

## 2. Terminology discipline

### Idiolect Erasure Rate

Use `IER` only for the paper's corpus-level quantity:

`baseline held-out authorship-attribution accuracy - post-rewrite held-out attribution accuracy`

An IER value belongs to a specific assistant, rewrite condition, attributer, corpus, and evaluation design. It is not a property of a single sentence and is not an intrinsic score for a model.

### Idiolect-retention evidence

For one Joel source/candidate pair, use terms such as:

- `idiolect-retention diagnostic`;
- `Joel-profile similarity`;
- `source/candidate attribution comparison`;
- `surface-style retention`;
- `deep-style retention`.

Do not call a single-candidate distance or probability "IER."

### Recognition

This protocol measures computational attributability. It does not establish whether Joel, his friends, or ordinary readers would recognize the prose as his. Human recognition and owner judgment remain separate evidence.

## 3. Always-on qualitative guard

Before any calibrated scorer exists, humanization workers must still:

- prefer the smallest edit that repairs the actual defect;
- preserve ordinary owner word choices, contractions, punctuation, function words, sentence joins, rhythm, unevenness, and register unless clarity or correctness requires changing them;
- preserve distinctive authorial reasoning and the route by which the thought was earned;
- avoid replacing a concrete owner realization with a generic explanatory equivalent;
- avoid "polishing" simply because a sentence can be made more professional, symmetrical, explicit, or complete;
- never treat a prompt saying `preserve the author's voice` as evidence that voice was preserved;
- never manufacture quirks, errors, catchphrases, slang, or odd punctuation merely to raise apparent distinctiveness.

This guard complements, rather than replaces, semantic sanity, article architecture, owner locks, and cold audit.

## 4. Reference-corpus provenance

A Joel idiolect reference profile must be trained only from material whose provenance supports the intended claim.

### Eligible primary reference material

Prefer natural owner-authored or owner-final writing that was not produced as a detector manipulation:

- published Joel prose with reliable provenance;
- owner-authored drafts or messages known to predate the current rewrite;
- natural owner rewrites produced for content/editorial reasons rather than to flip a detector;
- register-labeled samples that reflect the kind of text being evaluated.

### Separate or exclude from the primary profile

Do not silently mix these into the natural-owner baseline:

- assistant-generated prose merely accepted by Joel;
- synthetic probes;
- detector-targeted owner minimal pairs;
- assistant prose later edited by Joel when the natural/assistant contribution cannot be separated;
- texts whose authorship provenance is uncertain.

These remain useful as evaluation sets, ablations, or secondary profiles. They do not prove Joel's natural idiolect.

### Register stratification

Joel writes in materially different registers. At minimum, distinguish:

- research-conversational;
- practical guide;
- personal/tender;
- polemical/irreverent.

Do not mistake a register shift for idiolect loss. Report both pooled and register-matched results when data permit.

## 5. Negative authors and topic controls

A classifier that recognizes "Joel's topics" rather than Joel's style is not useful for this purpose.

Calibration should therefore include:

- multiple non-Joel human authors, not merely AI text;
- topic-matched negatives where feasible;
- document/source-level train/test separation;
- no near-duplicate passages across train and test;
- a content-sensitive baseline used explicitly as a confound monitor.

If a system performs well only because Joel discusses distinctive topics, the idiolect metric fails calibration.

## 6. Attribution instruments

The paper's architecture is the starting benchmark, not code to vendor blindly.

### Surface stylometry

Use a surface model based on:

- TF-IDF character 2–4-grams;
- TF-IDF word 1–2-grams;
- a linear classifier;
- held-out author/source splits.

Add a function-word/content-light diagnostic so topic-bearing vocabulary cannot do all the work.

### Deep authorship representation

Evaluate LUAR (`rrivera1849/LUAR-MUD`) or a comparably validated authorship representation:

- create an author profile from multiple natural training documents;
- compare held-out text against author profiles;
- keep register and topic controls visible;
- report baseline accuracy before interpreting rewrite degradation.

The released IER implementation uses mean author embeddings and nearest-profile retrieval, with LUAR profiles averaging up to 60 training documents in the main study.

### Content-sensitive baseline

A general semantic sentence encoder such as MiniLM may be useful to detect topical/semantic retention, but it must **not** be treated as the main idiolect instrument. The paper found that content-sensitive representations can materially understate style erasure.

## 7. Rewrite-dose ladder

Treat edit intensity as an experimental variable. For Joel work, use a ladder such as:

1. `p1` — spelling, grammar, punctuation, or literal mechanical repair only;
2. `minimal-bounded` — smallest semantic/syntactic change needed to fix the diagnosed problem;
3. `architecture-reconstruct` — substantial rewrite because inherited reasoning/structure is wrong;
4. `heavy-polish` — generic clarity/professionalization rewrite used as an adverse control, not a default;
5. `voice-preserve-prompt` — generic model rewrite explicitly instructed to preserve voice, used as a comparison condition rather than trusted as preservation.

Where possible, evaluate paired transformations of the same source passages.

## 8. Measurements

A proper condition-level experiment should preserve:

- exact source and candidate hashes;
- provenance class and register;
- rewrite condition and model;
- baseline attribution accuracy;
- post-rewrite attribution accuracy;
- IER only when the complete corpus-level definition is satisfied;
- surface and deep attribution results separately;
- function-word/content-light result;
- topic-sensitive baseline;
- semantic fidelity;
- edit distance or another transformation-dose measure;
- Pangram 4 result for the exact reader-visible boundary when relevant;
- confidence intervals/repeats when sample size permits.

Do not collapse these into one "human score."

## 9. Calibration gate before quantitative use

Do not use a Joel-specific computational idiolect result as an acceptance criterion until all of the following hold:

- natural-owner reference provenance has been audited;
- held-out splits are document/source separated;
- baseline authorship attribution is meaningfully above chance;
- a topic-matched or content-light check shows the result is not primarily topical;
- results are reasonably stable across resampling or repeated splits;
- at least one surface and one style-sensitive deep measure have been compared;
- register effects are understood well enough not to punish legitimate register changes.

If these conditions fail, record the result as research only.

## 10. Candidate selection: use a Pareto frontier

Do not optimize one metric at the expense of the others.

A candidate is dominated when another candidate:

- preserves meaning and owner authority at least as well;
- retains at least as much Joel-specific signal;
- performs at least as well on the required Pangram boundary;
- and uses no greater edit dose.

Prefer non-dominated candidates, then choose editorially.

A Pangram-green candidate with materially worse idiolect retention is **not** a successful Joel-byline humanization merely because the detector passed.

## 11. "Double erasure" terminology

The paper's `double erasure` means text that becomes difficult both to attribute to its human author and to identify as AI-assisted.

For this lab, a Pangram pass combined with weakened Joel-attribution evidence is a useful **double-erasure-like byline failure**. Do not call it the paper's exact double erasure unless the experimental design actually measures both components comparably.

## 12. Privacy and evidence handling

Authorship models can also support de-anonymization. Keep this project scoped to preserving Joel's own byline identity.

- Do not redistribute private source corpora merely to make the experiment reproducible.
- Store hashes, provenance metadata, splits, aggregate metrics, and code where possible.
- Keep any third-party comparison corpus within its license/consent constraints.
- Do not publish private personal or health material as an authorship benchmark.

## 13. Implementation architecture

Do not add heavy authorship dependencies to the default Pangram install until the calibration design proves useful.

The intended implementation is an optional idiolect research extra, for example:

- `numpy`, `scipy`, `scikit-learn` for surface experiments;
- optional `torch`, `transformers`, `einops` for LUAR;
- deterministic split/export scripts;
- metadata-only corpus manifests;
- result JSON with exact hashes and calibration receipts.

The Pangram detector cache, paid-call safety, and idiolect experiment cache should remain distinct. An authorship measurement must never trigger a paid Pangram call implicitly.

## 14. Rollout sequence

### Phase A — corpus audit

Inventory natural Joel samples by provenance, date, article, and register. Build a contamination ledger before training anything.

### Phase B — baseline validation

Build topic-matched negatives, document-level splits, surface and deep baselines, and content-light controls. Stop if the system cannot reliably distinguish Joel for stylistic rather than topical reasons.

### Phase C — retrospective benchmark

Run known historical transformations:

- natural owner text;
- assistant-heavy rewrites;
- owner-final repairs;
- detector-targeted candidates;
- minimal P1/minimal-bounded edits.

Check whether the instruments rank known voice-preserving and voice-erasing transformations sensibly.

### Phase D — prospective integration

Only after Phases A–C succeed, add idiolect-retention diagnostics to live humanization experiments and evaluate whether they improve candidate selection without damaging meaning or forcing stylometric mimicry.

## 15. Relationship to existing lab authority

This protocol does not change the existing authority order:

- Joel's direct owner correction and owner-final prose remain highest;
- fidelity, semantic coherence, and rhetorical function remain hard gates;
- Pangram remains detector evidence with its existing exact-boundary acceptance rule when requested;
- computational idiolect evidence becomes an additional diagnostic/gate only after calibration.

The purpose is to prevent the lab from solving "AI-shaped" by replacing it with "generic human-shaped."
