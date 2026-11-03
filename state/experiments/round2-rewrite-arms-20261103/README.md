# Round 2: does giving the writer Joel's own fixes make first-pass rewrites better?

Date: 2026-11-03. Owner direction (Joel, 2026-11-03): spend this week's spare Claude and Pangram credits on experiments that make humanization better and quicker; "don't stop unless you need my input". Status: PREREGISTERED before any rewrite exists.

This runs the comparison designed on 2026-10-24 (`state/experiments/owner-conditional-learning-correction-20261024/README.md`): a fixed current method against the same method plus Joel's literal fixes, across many distinct passage families rather than one paragraph, keeping no-flips, regressions and meaning failures.

## Inputs (frozen)

`inputs.json`: 74 paragraphs from round 1's 98 saved Pangram 4.1 texts (one per near-duplicate family, 24 lanes), relabelled P001–P074 in a seeded shuffle. `input_key.json` (not shown to writers, checkers or forecasters) links each to its round-1 id, lane and original 4.1 result.

- **T set, 48:** every round-1 text that was not fully Human (47 Mixed, 1 AI).
- **R set, 26:** fully-Human texts that round 1's tell-inventory reader wrongly called AI or Mixed. These model the realistic false alarm: a reader flags a passing paragraph and a writer rewrites it.

## Arms

Both arms get the same core brief (`WRITER-CORE.md`), the joel-articles tell inventory and the gate's owner rulings on rewriting his words (gate lines 20–123 at joel-articles `1cac9dd`). Every paragraph is presented as flagged; a writer may return it unchanged.

- **M1, current method:** core brief + tell inventory + owner rulings.
- **M2, plus Joel's fixes:** the same, plus `JOEL-FIXES-CATALOGUE-20260928.md`. For each paragraph the writer first names the two or three catalogue fixes closest to it, then revises the way Joel fixed those.

Six writers (three per arm) each take the same contiguous chunks of P001–P074. Writers never see detector results.

## Checks before any Pangram call

1. **Meaning check:** separate reviewers, blind to arm, compare every changed rewrite with its original claim by claim and return PASS or FAIL with the changed claim.
2. **Character check:** a script flags curly quotes, apostrophes or dashes that the original didn't have.
3. **Forecast:** a cold forecaster, blind to arm and original scores, gives P(all-Human) for each changed rewrite.

All of these are committed before the first Pangram call.

## Measurement

Pangram API, explicit `pangram-4` model, version recorded (expected 4.1), via joel-articles `tools/humanization/pangram_api.py` (cache keyed by text hash, task id saved before polling, no automatic POST retry). Unchanged rewrites reuse the original's saved result. Each text is checked alone.

## Outcomes

- T set: share of rewrites that become fully Human, per arm; the same counting only meaning-PASS rewrites (the headline); paired M2-vs-M1 counts; change in fraction_human; window confidence (all-High share).
- R set: regression rate (fully Human → not) per arm, and how often each arm leaves the paragraph alone.
- Meaning-FAIL rate per arm.
- Forecast accuracy on the rewrites (replicates round 1 on new text).

Expected cost: about 150 checks, roughly 260 API credits. Findings are recorded as provisional unless they replicate; no article or production rule changes in this round.

## Amendment after assembly (before any check or Pangram call)

The first character check counted occurrences, so it flagged rewrites that simply used more of the curly apostrophes their originals already used. The brief's rule is about character types the input doesn't have; `assemble.py` now checks that.

A first assembly ran while two catalogue writers were still finishing, so it is void. In that draft, M2's P041 had straight apostrophes in a paragraph written with curly ones; the writer's final file returns P041 unchanged, so no mechanical fix applies. That writer noted that P041 is Joel's own published paragraph, and that the catalogue records it reading 100% Human with his straight apostrophes and 100% AI curled. The experiment keeps the input as saved.
