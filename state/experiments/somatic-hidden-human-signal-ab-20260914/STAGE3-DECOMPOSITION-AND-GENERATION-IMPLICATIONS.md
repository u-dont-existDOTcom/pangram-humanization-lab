# Somatic hidden-signal Stage 3 — R2 decomposition and generation implications

Date: 2026-09-15
Status: DETECTOR RESEARCH / GENERATION-DIRECTION EVIDENCE / NO ARTICLE AUTHORITY

## Owner outcome correction

The objective is not merely to preserve already-Human prose. A preservation rule such as `do not homogenize Joel's register` cannot by itself humanize model-origin prose. The research must support a positive generation method that can create Human-shaped realization from protected meaning without copying an existing Human syntax.

## Stage-3 design

The replicated Stage-2 R2 intervention (uniform polished explanatory register) had flipped both P66 and P17 from Human to AI-Assisted. Stage 3 decomposed that bundle into two approximate factors per paragraph:

- `R2L`: polished lexical/register substitutions while keeping the original sentence/clause architecture relatively stable;
- `R2S`: editorial/syntactic restructuring while retaining the ordinary lexical register relatively closely.

Same audit identity was retained. Owner-authorized ceiling extended 10 -> 14 with the generation-relevant rationale recorded in the call ledger.

## Exact Pangram 4.0 results

| Cell | Factor | Verdict | AI-assisted fraction | Human fraction | Confidence |
|---|---|---|---:|---:|---|
| P66-R2L | lexical/register normalization | Mixed | 0.5456110239 | 0.4543889761 | mixed windows: Human High + AI-Assisted Medium |
| P66-R2S | editorial/syntactic restructuring | Human | 0.0 | 1.0 | Medium |
| P17-R2L | lexical/register normalization | Human | 0.0 | 1.0 | High |
| P17-R2S | editorial/syntactic restructuring | Human | 0.0 | 1.0 | High |

Final accounting after Stage 3: 14 paid API calls in the same audit; no audit reset was used.

## Interpretation

### P66 localizes substantially to lexical/register realization

P66's ordinary-register baseline and its restructuring-only probe remain Human, while lexical/register normalization alone crosses to Mixed. The returned localization keeps the first sentence Human and marks the latter portion AI-Assisted.

This supports a real local register/word-choice contribution at P66. It does not imply a universal list of Human or AI words.

### P17 is interactional

P17's lexical-only and restructuring-only probes both remain Human, even though the full Stage-2 R2 polished package was AI-Assisted / High.

Therefore P17 does not support either subfactor as sufficient. The detector effect requires some interaction in the combined realization, or another bundled R2 difference not captured cleanly by the decomposition.

### Cross-paragraph conclusion

The strongest transferable conclusion is **not** `use informal words` and not `avoid syntactic smoothing`.

Instead, model-shaped risk appears to increase when a paragraph's local realizations become too mutually aligned: diction, syntax, relation-marking, abstraction level, and explanatory posture can converge into one coherent editorial register. Which component is sufficient depends on the paragraph.

This is compatible with the owner's `accumulation of AI shape without compensation` framing: different local Human signals can absorb some model-shaped operations until enough aligned operations accumulate to cross the detector boundary.

## Positive-generation implication

The useful generative target is **function-conditioned heterogeneous realization**, not deliberate roughness.

A generator should choose a sentence's realization from the local thought and speech act rather than from a paragraph-wide style optimizer. Technical naming, source attribution, causal explanation, practical instruction, author judgment, and ordinary reader-facing explanation can legitimately use different lexical and syntactic registers inside one paragraph when the content calls for them.

Formally, prefer a local register function:

`realization_i = g(thought_i, speech_act_i, source_plane_i, stance_i, literal_context_i)`

rather than:

`realization_i = g(paragraph_style, editorial_consistency, global_polish)`

This is a generation hypothesis, not yet a validated generation rule.

## Required next validation

Do not spend the next detector calls further subdividing P66/P17 vocabulary. That would become token hunting.

The next meaningful test is generative:

1. choose genuinely model-origin Somatic prose whose protected semantic/function content is known;
2. withhold any Human rewrite of that passage from the generating context;
3. generate fresh syntax using a function-conditioned realization architecture;
4. compare against a conventional single-register model rewrite/control while preserving the same semantic units;
5. cold-audit fidelity and writing quality before Pangram;
6. use Pangram only after the candidate is independently acceptable prose.

Success requires generation from meaning, not preservation or imitation of an already-visible Human target.