# Pangram continuation: source review and twelve concealed-outcome forecasts

## Outcome

The source review sharpened the question but did not establish a strong general predictor. The frozen current-Chat forecasts matched **9 of 12** saved Pangram 4.1 outcomes. Always predicting Human would match **8 of 12**. All four non-Human cases were identified; three of eight Human cases were over-flagged. The three false alarms had forecasts of 0.40 for an all-Human result, so they were uncertain calls, not claims of definite AI authorship. Brier score: **0.185625**; class-rate constant on this sample: **0.222222**. The sample is too small to establish improvement over the preceding pass.

No new Pangram submissions were accepted in this continuation. The eight live paired comparisons were prepared and frozen, but execution was blocked by OpenAI safety checks before the runner started. That block was not bypassed. The original preceding study still has eight accepted calls; this continuation adds zero. Do not represent the prepared variants as measured findings.

## What the source review clarified

The richer calibration bundle distinguishes detector success, owner visual preference, and actual authorship. They are not interchangeable. Its owner examples sometimes add a missing thought or change what the paragraph does for a reader; they are not merely longer versions of the same claim.

In the inner-monologue example, an inventory of internal experiences becomes attention to a stomach knot or a place one wants to leave. Speaking or writing is linked to comfort. The owner also changes language exposing a feeling into thoughts provoking a feeling. These are meaningful changes, and omitted images/songs must remain documented rather than called stylistic noise.

In the relational-capacity example, the owner asks the reader to compare the other person's promised change with how long the reader's own change took. The rewrite also adds mutual uncertainty and a reason that boundaries can help support the other person. The source correctly classifies this as reauthoring. The useful operation is giving the reader a relevant comparison to consider, not adding a rhetorical question to any paragraph.

The unsuccessful expansions in the preceding study mainly repeated qualifications. They did not establish a clean test of all the kinds of development present in the owner examples. This is an interpretation of the literal texts, not an independently validated detector explanation.

## A particularly informative archived contrast

The 74-word differentiation paragraph returned Human Written, with every segment Human. Inserting one new reason for taking a break produced an all-AI result in three saved realizations:

1. “Even when it isn’t, a break can let the old programming quiet down long enough for what you actually want to come up.” — 97-word complete input, AI Generated / High.
2. “And sometimes you need the break anyway, because it’s hard to hear what you actually want while the old programming is still playing in your ear.” — 100-word complete input, AI Generated / High.
3. The same second idea as a parenthetical after “necessary” — 98-word complete input, AI Generated / High.

For each, deleting only the inserted text exactly reproduces the saved baseline. All records are version 4.1, from October 23. This is existing local contrast evidence, not three independent replications and not a fresh rerun. The full texts and raw summary/window records are in RESULT.json.

The addition supplies a real extra reason; it is not merely empty repetition. Therefore neither “more explanation helps” nor “adding a logically relevant reason helps” is a sufficient prediction rule. Conversely, the no-addition paragraph is orderly and concise yet passed. This constrains our explanation without proving which linguistic representation caused the detector's internal response. The records do not license a ban on “old programming,” “because,” or explanatory insertions in general.

## The three prediction misses

- **U01, 47 words:** friends/family may resist someone becoming happier; consider the loss, behavior and obligations before assuming envy. Recorded Human / High. I overweighted compact evaluative structure.
- **U02, 74 words:** temporary distance, return on different terms, possible permanent exit and uncertainty. Every segment Human, with mixed confidence levels. I overweighted the tidy sequence and concluding restatement.
- **U05, 64 words:** imagined communication, a concrete fallback statement and redirecting care to oneself. Recorded Human / High. I overweighted its efficient sequence of instructions.

These are post-result observations. The original forecasts and reasons remain unchanged. They are not causal explanations retroactively proven by the result.

## Method and leakage limits

The 12 cases were selected by outcome-independent hash order from 28 eligible candidates, with one per ledger lineage/close-text group. Previous15 lineages and strings with SequenceMatcher similarity >=0.60 to a previous text were excluded. Similarity was used only for leakage screening, not semantic judgment or AI detection. Different lineages can still share a section, theme or thought. This is not a fully independent passage-family benchmark.

Predictions were made by the current Chat context before exposing the selected exact labels. The separate-evaluator route had been blocked in the prior handoff and was not retried. Prior archive familiarity remains. All cases come from one author's guide and share register. Performance must not be generalized to Helwa or actual authorship.

## Frozen but unexecuted live comparisons

Eight cells keep source claims and examples fixed more carefully than the previous expansions: four combinations of packing paragraphs2/3 in the owner inner-monologue passage; one two-cell causal-image comparison; and one two-cell reader-self-comparison. These use1–3 paragraphs and90–205 words each. The causal-image pair keeps the metaphors and differs by only3 words while coordinating separate cultural actions into one sentence. It is intended to distinguish rhetorical packaging from merely adding words. Wording and syntax still co-vary, so even a future flip would not prove a universal mechanism.

Do not combine the cells into one Substack post and treat the results as equivalent: doing so changes the evaluated boundaries and context. No workaround to the blocked execution is authorized by this record.

## Preservation and verification

The executable verifier checks the frozen prediction hash, recomputes the12-case summary, verifies saved source-input hashes, checks the three exact insertion-only contrasts, confirms the eight live cells are explicitly unexecuted, and checks the artifact manifest. It makes no network requests and reads no credential.

The historical samples include health and religious claims; they are writing-analysis data, not newly fact-checked advice. No source article, production gate, or owner preference is changed by this study. Findings are provisional or passage-specific.

## Source anchors

- joel-articles@dc929e66beb4b06cbc8b80d5be7eec7cd967c89f, articles/inner-child-therapy/experiments/t99-api through t103-api: exact stored texts and4.1 results.
- pangram-humanization-lab@f73e5fa91bec4522f9ce19d89edc883f48941460, state/generation/positive-calibration-20260917/sources/inner-monologue-pair.md and relational-capacity-owner.md.
- Same lab snapshot, OWNER-CALIBRATED-WRITER-REFERENCE-V2-20260917.md and OWNER-CALIBRATION-MARCHING-EFFICIENCY-20260917.md: owner visual calibration kept separate from detector outcomes.

## Next discriminating question

Does preserving the actual reader comparison or causal sequence while changing only its packaging alter the detector result? The prepared tests address that more directly than adding general reassurance. Their outcomes remain unknown. Until live execution is available, do not tune them to imaginary results or call the proposed mechanism learned.
