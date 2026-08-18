# Idiolect validation protocol — calibrating the fast proxy against research-grade attribution

Status: **required before the dependency-free retention proxy is treated as more than directional evidence.**

The merged `idiolect-retention` command is deliberately cheap, private, deterministic, and dependency-free. That makes it suitable for routine editing, but it is not the paper's TF-IDF/linear-SVM or LUAR authorship-attribution setup. This protocol defines the second-tier validation lane needed to learn when the fast proxy is trustworthy for Joel's actual registers and when it is not.

Research basis: Ushna Malik and Moiz Sadiq Awan, *The Assistant Erased You: Measuring Loss of Authorship Signals in AI-Mediated Communication* (arXiv:2608.00926, 2026), plus the authors' MIT-licensed reproducibility repository `ushnamalikk/idiolect-erasure-rate`.

## 1. Two-tier architecture

### Tier A — operational retention proxy

Use the existing dependency-free `pangram-lab idiolect-retention` command during substantial D3/D4 rewriting.

Its job is fast directional screening:

- compare an authoritative original and candidate with a held-out author profile;
- report movement on `surface` and `content_light` channels;
- preserve hashes and aggregate metadata without storing private source text;
- identify suspicious drift worth editorial inspection;
- never make a universal pass/fail claim.

Tier A remains useful even after Tier B exists because it is cheap enough to run routinely.

### Tier B — research-grade validation

Run periodically, and whenever a new register/corpus is promoted to operational use, with style-sensitive and content-sensitive attribution methods closer to the paper.

Tier B answers a different question: **does the cheap Tier-A signal track actual held-out authorship attribution well enough in this corpus/register to be useful?**

Tier B is not required on every live edit. It validates the instrument and the corpus, not each individual sentence.

## 2. Paper-faithful comparison instruments

A research validation suite should contain all of the following rather than selecting the one that gives the most convenient result.

### A. Surface stylometry benchmark

Implement independently from the paper description:

- TF-IDF character 2–4-grams;
- TF-IDF word 1–2-grams;
- linear SVM classifier;
- closed-set author prediction on held-out texts.

Record exact preprocessing, random seed, train/test identities, hyperparameters, package versions, and baseline chance rate.

Do not blindly vendor an upstream helper merely because it lives in the paper repository. If released code and paper description differ, preserve the discrepancy and treat the paper-described experiment as the target unless the authors' exact reported-result path establishes otherwise.

### B. Deep style-sensitive authorship benchmark

Use LUAR (`rrivera1849/LUAR-MUD`) or a later validated replacement only with an explicit method/version record.

For paper-comparable LUAR evaluation:

- embed multiple natural training documents for each author;
- average the author's training embeddings into a profile;
- normalize profiles;
- attribute each held-out text by nearest-profile cosine similarity;
- keep the test text excluded from its author profile;
- preserve truncation/windowing and profile-size settings.

The original paper's released scripts use mean author profiles and nearest-profile retrieval. Any local deviation must receive a distinct instrument name.

### C. Content-sensitive confound baseline

Use MiniLM or another semantic sentence encoder only as a **topic/content confound monitor**, never as the primary voice score.

If a rewrite remains easy to attribute under the semantic baseline while style-sensitive SVM/LUAR attribution falls, topic is likely helping identify the author while style is being normalized. That is exactly the kind of false reassurance this validation lane is designed to catch.

### D. Content-light/function-word benchmark

Retain a topic-reduced attribution condition using function words and/or the existing content-light feature family.

This does not replace LUAR. It asks whether the observed retention/erasure survives when distinctive content words are minimized.

## 3. Sensitivity sanity checks

Before interpreting the instruments, verify that they behave differently under controlled perturbations.

At minimum:

- **word-order shuffle:** style-sensitive attribution should degrade more than a content-sensitive semantic baseline when lexical content is largely retained;
- **topic substitution or topic-matched authors:** an authorship instrument should not derive most of its accuracy from subject nouns;
- **mechanical P1 edit:** should normally preserve substantially more authorship signal than a heavy generic rewrite;
- **generic heavy polish:** should function as an adverse-control transformation likely to move natural owner text toward cross-author convergence;
- **voice-preserve prompt condition:** should be measured, not assumed successful.

If an instrument cannot distinguish these conditions sensibly, do not use it to calibrate the operational proxy.

## 4. Joel corpus design

The validation corpus must test Joel's style rather than merely Joel's recurring subjects.

### Provenance classes

Keep these physically or logically separable:

- `natural-owner` — natural Joel-authored or owner-edited-final prose with reliable provenance;
- `current-hybrid` — assistant-produced material that Joel substantially accepted/edited, when the explicit target is the current publication voice;
- `detector-targeted-owner` — owner edits made specifically during detector experiments;
- `synthetic` — generated controls and probes.

The primary natural-Joel validation must not silently train on the latter three classes.

### Registers

At minimum stratify:

- research-conversational;
- practical guide;
- personal/tender;
- polemical/irreverent.

Do not convert a legitimate register shift into an idiolect failure. Report pooled results only alongside register-matched results.

### Negative authors

Use multiple human non-Joel authors. Where feasible, include topic-matched negatives that discuss similar subject matter.

A validation set containing only Joel vs AI is invalid for authorship retention: it tests human/AI discrimination rather than author identity.

### Leakage controls

- split by document/source, not random paragraph fragments from the same source;
- remove exact duplicates and audit near duplicates;
- keep quotations, copied research language, templates, boilerplate, and long source excerpts from dominating profiles;
- keep profile and evaluation boundaries disjoint;
- record all source hashes and split assignments.

## 5. Calibration manifest

Raw private corpus text should remain local unless Joel explicitly assigns it a repository destination. Commit only a metadata manifest and aggregate results.

A manifest entry should include:

```json
{
  "sample_id": "opaque-stable-id",
  "author_id": "joel-or-control-alias",
  "sha256": "...",
  "provenance": "natural-owner",
  "register": "research-conversational",
  "topic_group": "health-research",
  "source_group": "article-family-or-independent-source-id",
  "split": "profile|validation|test",
  "word_count": 0,
  "near_duplicate_group": null,
  "contains_long_quotation": false,
  "privacy": "private-local-text",
  "notes": ""
}
```

The manifest must contain no raw private prose.

## 6. Baseline gate

Do not interpret rewrite degradation until original-text attribution is meaningfully above chance.

For every register/instrument report:

- number of candidate authors;
- chance rate;
- original held-out accuracy;
- rewritten accuracy by transformation condition;
- IER in percentage points where the closed-set definition is valid;
- sample count;
- confidence interval or resampling interval;
- split seed/identity;
- confusion matrix or per-author error summary when privacy permits.

If baseline accuracy is weak, the result is `insufficient baseline`, not evidence that rewriting preserved idiolect.

## 7. Proxy-agreement calibration

Tier A becomes `validated-for-register` only after retrospective paired testing against Tier B.

Use known transformations spanning at least:

- natural originals;
- P1/mechanical edits;
- minimum-bounded repairs;
- substantial architecture reconstruction;
- generic heavy polish;
- explicit voice-preserve rewrites;
- historical owner-final repairs when provenance permits;
- detector-targeted candidates as a separate, clearly labeled set.

For every pair, record the Tier-A movement and the Tier-B attribution outcome.

### Required questions

1. Does the Tier-A `content_light` direction agree with LUAR/SVM degradation more often than chance?
2. Does the Tier-A `surface` channel become falsely optimistic when topic overlap is high?
3. Which registers show stable agreement?
4. Which edit doses produce the largest disagreement?
5. Are there false positives where Tier A flags drift but research-grade attribution remains stable?
6. Are there dangerous false negatives where Tier A looks stable but LUAR attribution collapses?

Do not promote a numeric Tier-A threshold merely because it correlates on the calibration set. Hold out a final validation set.

## 8. Calibration status model

Record one status per instrument × target corpus/register:

- `unvalidated` — no research-grade comparison exists;
- `provisional` — retrospective comparison exists but sample size, leakage control, or holdout is insufficient;
- `validated-for-register` — held-out validation supports useful directional agreement for a named register and instrument version;
- `disconfirmed` — the proxy fails to track research-grade attribution reliably enough for that use;
- `stale` — corpus, feature algorithm, model checkpoint, or preprocessing changed after validation.

No status is global. Validation for research-conversational prose does not automatically transfer to tender personal writing.

## 9. Disagreement rule

When Tier A and Tier B disagree materially:

1. do not average them into one score;
2. inspect topic leakage, register mismatch, quotation density, boundary length, and transformation dose;
3. preserve the exact counterexample in the calibration evidence;
4. downgrade or narrow the proxy's validated scope when warranted;
5. do not let either metric override owner authority, semantic fidelity, or article architecture.

For live editing, unresolved measurement disagreement means the metric is inconclusive. Prefer owner/fidelity authority and the minimum coherent edit rather than optimizing toward one instrument.

## 10. Statistical discipline

Research-grade validation should use deterministic split identities plus resampling rather than one lucky train/test partition.

At minimum:

- bootstrap or repeated-split confidence intervals for accuracy differences/IER;
- paired significance testing for original-vs-rewrite attribution where appropriate;
- fixed random seeds recorded in results;
- report null and negative IER rather than clipping them;
- preserve per-condition sample counts;
- avoid phrase-level inference from corpus-level IER.

Any threshold or promotion criterion must be calibrated on training/validation data and evaluated once on a held-out test set.

## 11. Dependency isolation

Research-grade attribution must remain optional and must not expand the default Pangram runtime or the paid-detector path.

A future optional research environment may use the upstream lower-bound stack as a starting point:

- NumPy / SciPy;
- scikit-learn for TF-IDF + linear SVM;
- PyTorch / Transformers / einops for LUAR;
- sentence-transformers for the semantic confound baseline.

Keep this separate from the base installation and from `INSTALL-AND-RUN.sh`. Model downloads must never occur as an implicit side effect of a Pangram paid call.

## 12. Reproducibility boundary

Prefer independent implementation of the method described in the paper, then compare with the released repository as a reproducibility reference.

Record:

- paper version/date;
- upstream repository commit used for comparison;
- any paper/code discrepancy;
- local instrument version;
- dependency/model versions;
- exact dataset manifest hash;
- exact split hash;
- exact result hash.

Do not claim numerical replication unless the corpus, preprocessing, attributer, rewrite condition, model, and evaluation protocol actually match.

## 13. Completion criterion

The fast retention proxy is suitable as an operational **directional diagnostic now**. It becomes suitable for stronger candidate-ranking language only after Tier-B validation establishes where it tracks style-sensitive authorship attribution and where it fails.

Until then, reports should say:

> `Idiolect retention: directional proxy only; research-grade calibration for this register is not yet established.`

This protocol strengthens the merged IER architecture without replacing it: fast routine screening stays cheap, while stronger claims require stronger evidence.
