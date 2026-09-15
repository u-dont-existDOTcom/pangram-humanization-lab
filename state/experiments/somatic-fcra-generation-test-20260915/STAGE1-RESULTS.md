# FCRA generation test 1 — Stage 1 results

Date: 2026-09-15
Status: **NEGATIVE GENERATION RESULT / FCRA v0.1 STOPPED / DETECTOR RESEARCH ONLY**

## Exact Pangram 4 results

Durable result: `state/experiments/somatic-fcra-generation-test-20260915-stage1-results.json` on `automation/pangram-fixed-batch`.

| Candidate | Purpose | Verdict | AI | AI-assisted | Human | Confidence |
|---|---|---|---:|---:|---:|---|
| A-global-polish | conventional globally polished control | AI | 1.0 | 0.0 | 0.0 | High |
| B-fcra-v01 | function-conditioned realization architecture | AI | 1.0 | 0.0 | 0.0 | High |

Both were preservation-clean against the same S1-S8 semantic/function packet with zero unexplained substantive deltas before submission.

The FCRA candidate did not improve Pangram directionally. Its returned window `ai_assistance_score` was higher than the control's; that field is not treated as a calibrated probability, but it provides no basis for claiming latent improvement.

## Strategy consequence

Do **not** iterate FCRA v0.1 by adding lexical/style prohibitions. The positive architecture failed the actual model-origin generation test.

The failure is consistent with the existing Somatic owner-teaching lesson: a bounded meaning/function packet can itself become an attractor. Changing local register selection while still requiring the writer to realize all packet obligations in one compact paragraph did not escape the model prior.

## Structurally different next test

Test the same source boundary with:

1. the exact untouched model-origin working source, to establish whether this exact boundary actually needs detector repair;
2. a **scope-relaxed realization** that preserves S1-S8 at the section boundary but lets separate live thoughts occupy separate paragraphs rather than packing the packet into one paragraph;
3. a **minimum-transform realization** that preserves most existing sentence material and changes only the editorial packaging needed to carry the same functions, instead of regenerating the boundary wholesale.

This is a method switch, not another FCRA rewrite.

If neither structurally different candidate improves materially and the untouched model source is AI, stop model-only closed-packet generation for this boundary and require new authorial cognition / source recovery / reopening of semantic authority rather than accumulating more style rules.

No article authority changes from this experiment.