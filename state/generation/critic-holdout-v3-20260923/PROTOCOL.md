# Humanization critic provenance holdout v3 — pre-run protocol

Date: 2026-09-23
Status: FROZEN / UNTOUCHED / NOT YET CLASSIFIED / GPT-6 SOL CONTRASTIVE CONFIGURATION

## Purpose

Validate the seven-pair literal contrastive critic after:
- abstract rubric v1 scored 14/20;
- abstract hard-veto v2 scored 10/20;
- contrastive four-pair GPT-6 Sol quick8 scored 6/8;
- contrastive six-pair GPT-6 Sol dev12 scored 11/12;
- the sole dev12 miss was added as literal pair P7 rather than converted into another abstract prohibition.

## Frozen configuration

- model: `openai-gpt-6-sol`
- provider: Venice through authenticated UDA gateway
- temperature: 0
- classifier prompt: `state/generation/critic-contrastive-dev-20260923/contrastive-prompt-v3.txt`
- prompt SHA-256: `0d144827ce1f58daef580022ffd1870f8d03308dadc6c1dd3980b9758e7340e9`
- total holdout passages: 20
- HUMAN: 10
- AI: 10
- blind-set SHA-256: `924472ccff10bd45d7065611497cec1634c68bcd39b89f2848f5463511b6a3a8`
- hidden-key SHA-256: `920b0c6c4467a44c1ba67aaeb36118ebe2e7b124416df563ffcf6b9811c853c4`
- selection seed: `202609230057`

## Eligibility and selection

The candidate pools were assembled before classification.

Human pool:
- exact direct-owner/final prose or confirmed natural no-AI prose;
- paragraph-scale 40–210 words;
- no exact SHA used as a target in benchmark v1, holdout v2, contrastive quick8, or contrastive dev12;
- no exact SHA used as one of the seven teaching references.

AI pool:
- explicit model/assistant realization;
- owner-cognition-assisted near-verbatim hybrid prose excluded;
- same word-range and exact-SHA exclusions.

Ten items per class were sampled deterministically from the eligible pools, then shuffled deterministically.

## Blind-key separation

The gold key must not exist on the classifier branch during the run. It is stored on separate evidence branch `evidence/humanization-critic-holdout-v3-key-20260923`, exact key commit `ce3ce122a04fd10ca26ba8e686213827a5832bc4`. The pre-run key SHA remains the commitment above.

Do not fetch/read the key branch in the runner or classifier context until:
1. all 20 valid responses exist;
2. all response/sample hashes are frozen durably;
3. an explicit `holdout_v3_end` marker exists.

## Run rules

- one stateless Venice request per passage;
- exact fixed prompt and exact fixed target bytes;
- no tools/search/provenance/detector result supplied to classifier;
- capture requested/returned model, response id, literal response, parsed binary classification, usage, elapsed time, sample SHA;
- transport errors are not classifier misses; rerun only failed transport items with unchanged configuration;
- a valid wrong binary result is a miss;
- freeze all responses before key reveal;
- production-gating threshold: **20/20**;
- anything below 20/20 leaves the fresh critic non-gating;
- if this prompt is changed after any v3 result is seen, v3 becomes development data and any later calibration claim requires a new untouched holdout;
- Pangram calls: 0.
