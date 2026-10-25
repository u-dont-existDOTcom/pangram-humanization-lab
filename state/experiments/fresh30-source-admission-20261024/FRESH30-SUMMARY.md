# Fresh30: complete offline A/B writing experiment

Status: **30/30 source families attempted; 27 paired first attempts; 3 baseline fidelity rejections; no new Pangram calls during V3.** Direct owner style approval and general detector effect remain UNMEASURED. These are Claude Sonnet separate-restricted-context reviewer ratings, not Joel's endorsement.

## Counts
| Measure | Observed |
|---|---:|
| Predeclared source paragraphs | 30 |
| Baselines with reviewer-accepted preservation | 27 |
| Baseline rejected (not replaced) | 3 |
| Completed first-attempt A/B pairs | 27 |
| B scored more natural | 15 |
| A scored more natural | 9 |
| Naturalness tied | 3 |
| Reviewer overall prefers B | 6 |
| Reviewer overall prefers A | 19 |
| Reviewer overall tie | 2 |
| A fidelity_ok (model reviewer) | 27/27 |
| B fidelity_ok (model reviewer) | 21/27 |
| A identical to baseline | 15/27 |
| B identical to baseline | 0/27 |
| B longer in words | 24/27 |
| A longer in words | 2/27 |
| Equal word count | 1/27 |

**Critical inference:** The literal-example treatment produced more wording change and sometimes higher perceived naturalness, **but did not improve combined fidelity-first editorial preference** in this setup. Since half of A's drafts were unchanged, a strong confound is that many source-transformed baselines may already be reasonable prose; showing an example makes B feel required to rewrite anyway. The current experiment does not establish that examples are globally harmful, nor that word count or paragraph joins cause Pangram classification.

## Caveats
- Thirty sources come from **one author** nested in six article clusters, not 30 unrelated authors.
- A 6-case pilot was inspected before the other 24 cases were run; the extension is exploratory, not a fully untouched holdout. Inputs and teaching assignments for all 30 had been frozen before the pilot.
- The same model family generated baselines, writers, and fresh-context evaluator; runtime contexts were truly separate and restricted, with zero inherited prompt-cache reads, but this is not independent provider/evaluator architecture or owner review.
- Fidelity_ok flags are reviewer estimates; some 'ok' cases still list small semantic or rhetoric changes. Direct owner judgment can supersede them.
- Model-written baselines were made by transforming source paragraphs, which may already be humanized or mixed-authoring. **Do not assume all 27 baselines were detector-AI**. Exactly one previous Pangram API submission (T13 baseline) returned Pangram backend 4.1 AI Generated/High, 100% AI. The task was recovered/rekeyed from an old 4.0-expected mismatch without resubmission.
- No paragraph of the underlying published/working source was edited.

## What to learn next
Before more model-rewrite experiments, measure a **small, predeclared one-per-article sample of starting baselines** under the actual Pangram-4.1 backend to determine how many are truly detector-AI and eligible for humanization. Freeze forecasts and exact hashes before each paid call; use exact cache/reservation plus no-repeat safeguards. Stop the pair measurement on a source family if the baseline is Human or candidates have fidelity loss.

If the baselines are mostly Human, this is a **source-rewrite-damage** experiment rather than AI-to-Human improvement, and the architecture needs a genuinely AI-generated, meaning-aligned source that did not inherit owner prose too literally. Consider retaining examples as conditional reader-material rather than mandatory rewrite triggers.

If several baselines are AI and both outputs remain faithful, a limited paired Pangram comparison can test whether B affects detector behavior. Keep all wins/losses/no-flips across distinct families. A 1-case detector flip cannot promote a portable prose rule.

## Source trail
- See FRESH30-OFFLINE-OUTCOMES.json for 30 case IDs, categories, scores, stem hashes and reviewer observations.
- Each PILOT-RESTRICTED-RESULTS/Txx folder contains stage-specific sanitized json records with literal outputs and score evidence.
- ISOLATED-PILOT-V3.json, ISOLATED-EXPLORATORY-24.json, COHORT.json, TEACHING.json and MATCH-QUALITY.json were frozen before those respective tasks.
- The Pangram4.1 terminal record is in PANGRAM-BASELINE-CACHE with preserved original 4.0 mismatch record and a rekeyed 4.1 success for the same paid task.
