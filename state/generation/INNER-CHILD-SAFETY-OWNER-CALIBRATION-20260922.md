# Inner Child safety H2 — owner calibration after six-call campaign

Date: 2026-09-22
Status: CASE EVIDENCE / OWNER CORRECTION / NO NEW DETECTOR CALL / NO GENERAL PROMOTION

## Exact detector context

The dangerous-present-adult stable section consumed six paid Pangram 4 calls:

1. V8 exact H2 — AI 1.0, probability 0.9873712062835693.
2. V35 exact H2 — AI 1.0, probability 0.9835429191589355.
3. Current 109-word H2, SHA 21a81abbe93bffd616748830734e1432ee58450d02bc878fa5256d8ddae4af87 — AI 1.0, probability 0.7611563801765442.
4. Natural publication boundary, SHA a07e59ab4834bc891358b1ad14c28ff54ef4d9fa255c41a24df8ed9828d4baae — AI 0.3600907028 / Human 0.6399092674.
5. Same boundary without the H2, SHA 21c890f7c948909334ace90a323905e4c63ddd86e576d8d2ca73dd2cc3bb6477 — Human 1.0 / AI 0.0.
6. Natural-boundary anti-false-positive ablation, SHA b5ed7edda5caf9644068f3f1f5e502ba91d3f189cd80d499afccc8b6933d4c2e — AI 0.3193439543 / Human 0.6806560755.

No seventh call was made during owner calibration.

## Owner correction

Joel reviewed the exact boundary and identified obvious AI-shaped prose that the automated critics had missed.

For the accepted readiness paragraph, despite the no-H2 boundary scoring Pangram Human 1.0, Joel classified the prose as instruction-manual/listicle shaped.

For the current H2, Joel classified the long span after the opening sentence as more listicle/manual prose and challenged the reader model directly: who is the passage talking to, and why would that reader care about this sequence?

Joel also identified a coherence defect in the accepted next section: the humanized prose says that `ask` sounds like a question followed by a second voice, but the local setup for the term is gone. The raw source had explicitly introduced `“Voice,” “ask,” and “answer”` together.

## Case finding

This case is direct evidence that a Pangram-Human boundary can still contain prose Joel judges obviously model-shaped at the editorial/tell level.

It does not establish a Pangram false-negative rate, a universal failure mode, or a new phrase rule. It reinforces an existing limit already represented in the lab: detector status is separate from editorial authorship-shape judgment and cannot immunize known-green prose from later owner-identified defects.

The more important process failure is upstream: the production preflight/tell audit failed to apply existing AI-N16 instruction-manual cadence and AI-N17 missing reader-visible setup strongly enough before paid calls.

Disposition: project-specific case evidence. No new universal tell promoted from this single case.
