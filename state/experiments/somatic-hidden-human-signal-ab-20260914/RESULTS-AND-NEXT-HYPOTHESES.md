# Somatic hidden-Human-signal A/B — results and next hypotheses

Date: 2026-09-14
Status: **COMPLETE THROUGH SIX-CALL CAP / DETECTOR RESEARCH ONLY / NO ARTICLE AUTHORITY**

## Exact durable detector evidence

API transport: trusted private self-hosted executor -> canonical `automation/pangram-fixed-batch` runner -> Pangram 4.0.

Result files:

- Stage 0: `state/experiments/somatic-hidden-human-signal-ab-20260914-stage0-results.json` on `automation/pangram-fixed-batch`.
- Stage 1: `state/experiments/somatic-hidden-human-signal-ab-20260914-stage1-results.json` on `automation/pangram-fixed-batch`.
- Call ledger: `state/pangram-call-ledgers/somatic-hidden-human-signal-ab-20260914.json` on `automation/pangram-fixed-batch`.

Call accounting at completion:

- new paid API calls: 6
- cache hits: 0
- pending resumes: 0
- estimated credits: 6
- estimated cost: $0.30
- hard section cap: 6/6 reached

No H12 interaction cell was submitted because the audit reached its standing six-call cap.

## Results

| Cell | Operation | Pangram 4 verdict | AI fraction | Human fraction | Window confidence | Window `ai_assistance_score` |
|---|---|---|---:|---:|---|---:|
| P66-S0 | conspicuous Human-looking surface stripped | Human | 0.0 | 1.0 | High | 0.1089144498 |
| P17-S0 | conspicuous Human-looking surface stripped | Human | 0.0 | 1.0 | High | 0.0023145126 |
| P66-H1 | detach article-local context/backreferences | Human | 0.0 | 1.0 | High | 0.0127232755 |
| P66-H2 | nominalize active process realization | Human | 0.0 | 1.0 | High | 0.0657183677 |
| P17-H1 | detach article-local context/backreference | Human | 0.0 | 1.0 | High | 0.0005668470 |
| P17-H2 | regularize the two problems into matched First/Second branches | Human | 0.0 | 1.0 | High | 0.0607697591 |

`ai_assistance_score` is preserved as returned metadata only. It is not treated here as a calibrated probability or validated detector-margin measure. Its direction is not coherent enough across these manipulations to rescue either hypothesis.

## What this falsifies or weakens

### Context dependence is not sufficient

Both context-detached variants remain Human / High confidence / 0 AI fraction. The Human verdict is not being carried simply by phrases such as `this part of the map`, `prior therapies`, or `those therapies`.

### P66 active-process realization is not sufficient

Turning the active process phrase into a more nominalized package still remains Human / High confidence / 0 AI fraction.

### P17 branch asymmetry is not sufficient at the tested dose

Regularizing the paragraph into explicit matched `First` / `Second` branches still remains Human / High confidence / 0 AI fraction.

### Obvious Human texture was not the whole explanation

Both new stripped controls reproduce Joel's qualitative observation: even after removing conspicuous personal/metaphoric/colloquial signals, the passages remain Human at this exact boundary.

## Stronger comparison with known AI-1.0 Somatic surfaces

The closest existing AI-1.0 controls in `human-to-ai-minimal-pairs-20260828` are C1 and C7. Those passages are highly compressed and realization-efficient: clauses map cleanly onto exposition jobs, diction stays comparatively register-stable, and cross-domain relations are explicitly synthesized.

The new hard-positive Human cells retain different microstructure even after obvious Human markers are stripped:

1. **semantic inefficiency / surplus wording** — e.g. overlapping or partially redundant formulations rather than maximum compression;
2. **mixed register** — technical/abstract language sits next to ordinary evaluative wording instead of being normalized into one polished register;
3. **clause-to-job misalignment** — one sentence can carry attribution, evidence limitation, causal explanation, and ordinary-language judgment in an uneven way rather than cleanly assigning one rhetorical job per clause;
4. **local lexical/syntactic residue** from the owner-origin backbone may survive substantial editorial regularization even when macro topology looks model-shaped.

These are candidate explanations, not established Pangram mechanisms.

## Next discriminating experiment if the owner explicitly expands the paid-call cap

Do not reopen context dependence, active-vs-nominal process realization, or simple First/Second parallelization. They were null at this boundary.

The next materially different factors should be:

### R1 — semantic-efficiency normalization

Compress redundant/overlapping wording while preserving claims and architecture. The test is not generic shortening; it specifically removes surplus phrases that make the current Human surface less information-efficient.

### R2 — register homogenization

Replace collisions between technical language and ordinary/awkward phrasing with a consistently polished explanatory register, preserving claims and overall sequence.

Preferred adaptive design:

- one R1 cell and one R2 cell per paragraph = four new cells;
- do not automatically add R1×R2 interactions;
- if either single factor flips Mixed/AI, localize that factor before any combination;
- if all four remain Human, stop this family rather than token-hunting and treat the surviving Human signal as distributed/idiosyncratic at the tested scale.

Running those cells requires explicit owner authorization to exceed the existing 6/6 audit cap. Do not create a nominally new audit ID merely to evade the cap.

## Production implication now

The experiment strengthens Joel's correction: visible model shape can contribute risk without determining the binary verdict. It also shows that several plausible forms of `compensation` are not individually necessary.

For production humanization, do not force prose to preserve contextual dependence, active verbs, branch asymmetry, or obvious colloquial texture merely because they can occur in Human passages. The unresolved signal appears deeper and more distributed.

Pangram remains detector evidence only. No publication prose or article authority changed.