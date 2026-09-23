# Humanization critic provenance holdout v3 — result and target correction

Date: 2026-09-23
Status: COMPLETED UNTOUCHED HOLDOUT / CONTRASTIVE ABSOLUTE CLASSIFIER FAILED / PRODUCTION GOLD-TARGET CORRECTION REQUIRED / NO PANGRAM CALLS

## Frozen identities

- model requested/returned: `openai-gpt-6-sol`
- prompt SHA-256: `0d144827ce1f58daef580022ffd1870f8d03308dadc6c1dd3980b9758e7340e9`
- blind-set SHA-256: `924472ccff10bd45d7065611497cec1634c68bcd39b89f2848f5463511b6a3a8`
- hidden-key pre-run SHA-256: `920b0c6c4467a44c1ba67aaeb36118ebe2e7b124416df563ffcf6b9811c853c4`
- hidden-key commit: `ce3ce122a04fd10ca26ba8e686213827a5832bc4`
- frozen response commit before scoring: `0574407ff6d1351babd0e34ba8cd88e8dfda931f`
- valid responses: 20
- transport errors: 0
- Pangram calls: 0

## Score

- total: **10/20 = 50%**
- Human: **7/10**
- AI: **3/10**
- false AI on Human: 3
- false Human on AI: 7

The seven-pair literal contrastive classifier is **not** production-calibrated.

## Development history

The same architecture looked promising on development data:

- four-pair quick8: 6/8;
- six-pair dev12: 11/12;
- sole dev12 miss was added as literal pair P7;
- untouched seven-pair holdout v3: 10/20.

This is a strong generalization failure. Do not add P8/P9/P10 from the v3 misses and repeat another absolute-classification holdout. That would continue the same architecture after its key prediction failed.

## What v3 does establish

The contrastive critic still misses known problem prose.

Examples among its AI->Human misses include:
- the Inner Monologue model baseline P1, whose source record is explicitly owner-reported Pangram AI/high;
- Romance `If you're already in it` assistant attempts that were exact high-confidence Pangram AI spans and had independently identified rhetorical-function defects.

So the failure cannot be dismissed as provenance labels merely disagreeing with good Human-shaped model prose.

At the same time, the benchmark's binary gold target is too broad for the production job.

`AI` in the benchmark means **model-authored provenance**. Production humanization does not need to infer hidden authorship. It needs to detect **remaining model-shaped realization defects**. A model-authored paragraph that has become genuinely Human-facing should not fail production merely because a model wrote it. Conversely, Human prose can contain listicle/manual cadence without becoming model-authored.

Therefore provenance remains essential metadata and an anti-leak control, but **authorship provenance is not the production gold label**.

## Failed assumption

The benchmark assumed:

> a critic that can infer Human vs AI provenance from short Joel-like passages is a good proxy for a critic that can find AI-shape defects before Pangram.

The three benchmark series do not support that assumption:

- abstract v1: 14/20, too permissive on AI;
- hard-veto v2: 10/20, too aggressive on Human;
- literal contrastive v3: 10/20 untouched despite 11/12 development.

The production task and the benchmark target have diverged.

## Structurally different next architecture

Switch from **absolute authorship classification** to **matched realization defect discrimination**.

Primary calibration unit:
- two passages serving the same or closely aligned thought/function;
- one is owner/editorially accepted Human-facing realization;
- one contains an owner-identified / source-recorded AI-shape defect;
- order randomized;
- provenance hidden;
- critic must choose which realization has the defect and name the concrete operation;
- exact phrases/topic cannot be the reason.

Gold label:
- owner/editorial realization judgment, with exact correction record;
- detector evidence may support the record but does not define the label;
- authorship provenance is stored separately.

This directly tests the production skill: recognizing a bad realization while controlling for topic and function.

Use a small pairwise development set first. If it generalizes, freeze a new untouched 20-pair holdout. Only then decide whether fresh-critic non-detection can again become production-gating evidence.

## Production state

There is currently **no calibrated external fresh critic** authorized to clear a candidate for Pangram.

Do not spend production Pangram on the dangerous-adult H2 until the unpaid internal/editorial gate is genuinely satisfied. No additional Pangram call was used in this debugging sequence.
