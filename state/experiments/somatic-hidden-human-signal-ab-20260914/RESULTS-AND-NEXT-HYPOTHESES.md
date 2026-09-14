# Somatic hidden-Human-signal A/B — results and next hypotheses

Date: 2026-09-14
Status: **COMPLETE THROUGH OWNER-AUTHORIZED 10-CALL CEILING / DETECTOR RESEARCH ONLY / NO ARTICLE AUTHORITY**

## Durable evidence

Programmatic route: trusted private self-hosted executor -> canonical `automation/pangram-fixed-batch` runner -> Pangram 4.0.

Exact result files on `automation/pangram-fixed-batch`:

- Stage 0: `state/experiments/somatic-hidden-human-signal-ab-20260914-stage0-results.json`
- Stage 1: `state/experiments/somatic-hidden-human-signal-ab-20260914-stage1-results.json`
- Stage 2: `state/experiments/somatic-hidden-human-signal-ab-20260914-stage2-results.json`
- Ledger: `state/pangram-call-ledgers/somatic-hidden-human-signal-ab-20260914.json`

Final accounting: 10 paid API calls, 0 cache hits, 0 pending resumes, estimated 10 credits / $0.50.

## Owner correction to call-budget semantics

Joel clarified on 2026-09-14 that six calls is a **review threshold**, not an absolute universal maximum: effectively, `you better have a good reason to go past 6`.

The first six calls all remained Human. Joel then explicitly authorized four additional R1/R2 calls because they were the next predeclared discriminating experiment. The existing audit was extended from 6 to 10; it was not reset or replaced with a nominally fresh audit. The exact override reason is recorded in the Stage-2 spec and call ledger.

The fixed-batch implementation was updated so a ceiling above six requires an explicit `section_call_cap` plus non-empty `owner_override_reason`, while preserving the same ledger and all previous call accounting.

## Results

| Cell | Operation | Verdict | AI | AI-assisted | Human | Confidence | `ai_assistance_score` |
|---|---|---|---:|---:|---:|---|---:|
| P66-S0 | conspicuous Human-looking surface stripped | Human | 0.0 | 0.0 | 1.0 | High | 0.1089144498 |
| P17-S0 | conspicuous Human-looking surface stripped | Human | 0.0 | 0.0 | 1.0 | High | 0.0023145126 |
| P66-H1 | context detached | Human | 0.0 | 0.0 | 1.0 | High | 0.0127232755 |
| P66-H2 | active process nominalized | Human | 0.0 | 0.0 | 1.0 | High | 0.0657183677 |
| P17-H1 | context detached | Human | 0.0 | 0.0 | 1.0 | High | 0.0005668470 |
| P17-H2 | two problems parallelized as First/Second | Human | 0.0 | 0.0 | 1.0 | High | 0.0607697591 |
| P66-R1 | semantic-efficiency normalization | Mixed / AI Assisted | 0.0 | 1.0 | 0.0 | High | 0.5031172633 |
| P66-R2 | register homogenization | Mixed / AI Assisted | 0.0 | 1.0 | 0.0 | Medium | 0.5874951482 |
| P17-R1 | semantic-efficiency normalization | Human | 0.0 | 0.0 | 1.0 | Medium | 0.3495758474 |
| P17-R2 | register homogenization | Mixed / AI Assisted | 0.0 | 1.0 | 0.0 | High | 0.4284324348 |

`ai_assistance_score` is returned metadata only; it is not treated here as a calibrated probability or validated detector margin.

## Interpretation

The first six calls weakened several intuitive local explanations. Human classification survived removal of conspicuous personal/colloquial texture, article-local context, active-process realization, and simple branch asymmetry.

### R1 — semantic-efficiency normalization: heterogeneous

P66-R1 crossed the detector boundary to AI Assisted / High. P17-R1 did not: it remained Human / Medium. Therefore `semantic inefficiency protects Human` is too broad. Semantic compression/cleanup is detector-relevant for P66 but is not a transferable sufficient explanation.

### R2 — register homogenization: replicated across both paragraphs

P66-R2 crossed to AI Assisted / Medium and P17-R2 independently crossed to AI Assisted / High. This is the strongest cross-paragraph result in the experiment.

The R2 operation shifted mixed ordinary/technical realization toward a uniformly polished explanatory register, for example:

- `the way we process` -> `the process of reprocessing`
- `in a healthier way` -> `in a more adaptive form`
- `being honest about what happened` -> `preserving an accurate account of what occurred`
- `works best` -> `is most applicable`
- `goal` -> `objective`
- `do show meaningful impact` -> `demonstrate meaningful benefits`
- `But there are two main problems` -> `However ... two principal limitations`
- `isn’t well-captured` -> `may be insufficiently represented`
- `creating` -> `establishing`
- `old conditioned fear responses` -> `prior conditioned fear responses`

These examples describe the bundled intervention; they are not phrase-level causal rules or a blacklist.

## Current best hypothesis

The evidence now points away from a single macro thought-topology rule and toward **surface realization distribution**. A stronger candidate is loss of natural register heterogeneity when model/editorial processing normalizes ordinary wording, technical language, attribution, evaluative language, and local phrasing residue into one smooth professional explanatory voice.

R2 reproduced an intervention effect across two paragraphs, but it changed multiple lexical and syntactic choices together. It does **not** establish a unique Pangram mechanism or prove that `register` alone is causal.

This is compatible with the previously known AI-1.0 Somatic controls, which are realization-efficient, strongly synthesized, and comparatively register-stable.

## Production implication

Do not gratuitously normalize Joel-origin prose into one uniformly polished explanatory register. Semantically sound collisions between ordinary language, technical terminology, attribution, and evaluative wording may carry real authorship signal and should not be treated automatically as editorial dirt.

This does **not** authorize adding mistakes, fake awkwardness, filler, slang, or artificial irregularity. The production lesson is minimum-dose preservation, not deliberate degradation.

Visible model-shaped thought topology remains useful as an editorial diagnostic, but it is not sufficient as a paragraph-level Pangram predictor.

## Next experiment, only if further calls are decision-relevant

Do not run R1×R2 interactions next. R2 alone already flipped both paragraphs, while R1 was heterogeneous.

The next materially different test would decompose R2:

1. lexical/register substitutions while sentence/clause architecture is held as constant as practical;
2. syntactic/editorial smoothing while core lexical register is held as constant as practical.

If those subfactors remain heterogeneous, stop looking for a single magic feature and treat the signal as distributed/interactive at this scale.

Calls beyond the six-call review threshold still require a concrete reason and explicit owner authorization. Never reset an audit/section identity merely to evade review.

## Validation / tooling note

Focused regression tests were added for default-six behavior and reasoned same-audit extension. This Chat runtime could not execute local pytest because DNS resolution for `github.com` was unavailable, so do not claim a full deterministic suite ran here.

The trusted self-hosted workflow did validate the new path end to end before and during paid execution: immutable trigger validation, exact spec SHA verification, paid-dispatch validation, short-section routing, durable 6 -> 10 ledger extension with owner reason, all four new reservations, terminal Pangram 4.0 `STAGE_SUCCESS` responses, and successful workflow completion.

## Authority boundary

These are detector-research probes. None of the R1/R2 variants is publication prose or article authority. No Somatic article master, owner-final section, or publication state changed.