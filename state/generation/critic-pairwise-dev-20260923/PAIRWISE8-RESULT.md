# Pairwise realization-defect development v1 — GPT-6 Sol result

Date: 2026-09-23
Status: DEVELOPMENT FAILURE / GENERAL-JUDGE FAMILY STOP / NO PANGRAM CALLS

## Configuration

- model: `openai-gpt-6-sol`
- prompt SHA-256: `09a61a990bd0ae78eb4875a4efcc6f142046482b849df5b7b78d98afee57f2f3`
- blind-pair set SHA-256: `8f9caa122eb2afdd22d719d9b78eb692d1efd947ca402ea5653d0aa5f6c369a2`
- hidden development key SHA-256: `e1b16a2513b3dfb9b064aba592e8cccd3fbfdccc777f7410e601fca2b41d1f97`
- frozen response record SHA-256: `6974c784dc7b4c481c8b995982bed4216415650c15bedd37e9f9bd539be4c474`
- response-freeze commit: `78b0f0308557a334987e39b1d13669acff9b1d19`
- valid calls: 8
- transport errors: 0
- Pangram calls: 0

## Score

- total: **5/8 = 62.5%**
- misses: Q1, Q2, Q5

The pairwise task was easier and better aligned than authorship classification: the critic saw two passages serving the same/closely aligned function and only had to identify the rejected realization. It still failed three of eight exact correction cases.

Notable reversals:
- direct owner-final Write-It P1 was called defective while the model Candidate M paragraph was preferred;
- compressed Romance assistant anecdote was preferred over the owner realization;
- the detector-red radical-honesty disclaimer was preferred over the owner-final lived complication.

## Method stop

This is the fourth materially tested general-judge configuration in the debugging sequence:

1. abstract authorship rubric v1 — 14/20;
2. hard scaffold-veto v2 — 10/20;
3. seven-pair absolute contrastive holdout v3 — 10/20 after 11/12 development;
4. matched pairwise realization-defect chooser — 5/8.

The failure is no longer reasonably addressed by adding another example pair or another global rule.

**Stop training one external LLM to emit a single global Human/AI or good/bad realization verdict.**

## Structurally different next architecture

Decompose the production preflight into narrow observable defect audits.

Initial axes from the dangerous-adult owner correction:

1. **Reader-purpose / pragmatic act**
   - Who is the visible reader at this point?
   - What live question/pressure makes this passage necessary here?
   - Does the passage silently switch to clinician/evaluator/safety-policy audience?
2. **Antecedent / referent coherence**
   - For quoted/metalinguistic terms such as `ask`, `voice`, `answer`, does visible context introduce what the term refers to?
   - Did a rewrite delete the setup while leaving the later reference?
3. **Instruction-manual / listicle cadence**
   - Map consecutive beats by speech act/function.
   - Flag repeated question/command/condition/verdict/lesson units that turn the paragraph into a procedural staircase.
   - A list or imperative alone is not a failure; the issue is cumulative passage operation.
4. **Overclosure / explanatory aftercare**
   - Does the prose immediately explain, summarize, or moralize every example/complication instead of letting it perform its own article function?

Each auditor answers only its axis and cites exact spans. It does **not** classify hidden authorship.

Calibration should use known positive/negative examples for that axis. A critic that can answer a narrow observable question may be useful even if it cannot infer authorship.

## Production implication

Fresh-model outputs are advisory defect evidence, not a pass certificate. Production eligibility must not depend on one global classifier score.

Pangram remains downstream of unpaid internal/editorial audits. No additional Pangram call was used.
