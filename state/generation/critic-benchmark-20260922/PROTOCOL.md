# Blinded provenance benchmark v1 — 2026-09-22

Status: FROZEN BEFORE CLASSIFICATION / NO PANGRAM CALLS

## Goal

Test whether the current humanization critic rubric can distinguish known Human-authored from known AI-authored Joel-byline-style passages before the rubric is trusted as pre-Pangram non-detection evidence.

This benchmark measures paragraph/excerpt prose-shape discrimination. It does not replace the production requirement to audit a target inside its natural article boundary.

## Gold standard

Primary labels are **authorship provenance**, not Pangram output.

- HUMAN: direct owner-written or owner-confirmed no-AI prose.
- AI: explicitly model-generated / controlled model-written prose.
- Pangram-Human model prose is excluded from the primary gold labels when its detector result is the only reason to call it Human.
- Hybrid/uncertain provenance is excluded.

Frozen set:
- 20 passages total;
- 10 HUMAN;
- 10 AI;
- blind sample SHA-256: `cc2c7e99b30fa615433181e4f8b00098c572ff579c20c6368b6df9369e1a1f1e`;
- hidden gold-key SHA-256: `83680c6353986aa1646750d88787c90b3d2f5e7bbde3b26117b25748933a35cf`;
- deterministic shuffle seed: `202609222234`.

The gold key remains local/unpublished until every classification response is durably captured.

## Frozen critic prompt

```
You are a blinded prose-shape classifier. One passage below was written either by a human author or by an AI language model.

Classify authorship from the prose shape only. Do not search, use tools, infer from topic, or rely on factual correctness, controversy, medical/drug content, spelling/grammar errors, first person, direct advice, lists, questions, contractions, sentence length, or unusual beliefs by themselves.

Audit adversarially.

First make the strongest case that the passage is model-shaped. Inspect local realization and paragraph topology: cumulative instruction-manual/listicle cadence; one clean teaching job per beat; optimal/equalized semantic efficiency; tidy proposition -> qualification -> verdict cycles; exhaustive completion; checklist/taxonomy flow; generic transitions; abstract compression; fake spontaneity; explanatory aftercare; source/requirements-ledger order made visible; abrupt complication without a reader-visible reason.

Then inspect genuinely Human-facing relations: uneven thought duration driven by what actually matters; causally load-bearing/non-interchangeable detail; unresolved friction; asymmetric attention; a real social act toward the reader; self-implication or authorial judgment that is substantively relevant; a thought that stops without completing every implication.

Aggregate weak or mixed signals. Several individually ordinary features can form one strong model-shaped pattern. Conversely, a list, imperative, rhetorical question, concise explanation, or polished sentence can occur naturally in Human prose and must not be treated as a magic AI tell.

Force a binary classification even when uncertain.

Return valid JSON only:
{
  "classification": "HUMAN" or "AI",
  "confidence": "high" or "medium" or "low",
  "strongest_ai_case": "...",
  "strongest_human_case": "...",
  "decisive_reason": "..."
}

PASSAGE:
<literal passage>
```

## Run discipline

- Same frozen prompt for all 20.
- One genuinely new Railway Agent thread per passage; no thread continuation.
- No prior sample labels, provenance, Pangram results, score, benchmark position, or other responses supplied.
- Tell Railway Agent not to use sub-tools.
- No rubric edits during the run.
- Capture thread id, literal response, tool-call count, parse result, and sample SHA.
- Score only after all 20 responses are frozen.
- Any invalid/non-binary response is a benchmark miss unless a purely mechanical JSON extraction succeeds without semantic reinterpretation.

## Interpretation

- 20/20 on this frozen set is a useful starting calibration, not proof of general authorship detection.
- If any item is missed and the rubric is changed in response, this entire set becomes development data. A later claim of 20/20 must use a new untouched holdout.
- A separate stress set may contain known model-written passages that Pangram has classified Human in some tested boundary. That set tests Pangram/editorial disagreement and must not redefine Human ground truth.
