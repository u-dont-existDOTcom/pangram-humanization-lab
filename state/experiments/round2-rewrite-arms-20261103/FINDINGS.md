# Round 2 findings: first-pass rewrites with and without Joel's fixes catalogue

Date: 2026-11-03. Design: `README.md` (preregistered). Every rewrite, meaning verdict and forecast was committed before the first Pangram call. Exact numbers: `out/RESULTS.json` and `out/per_paragraph.json` from `score.py`. 97 changed rewrites checked alone on Pangram 4.1 (API), every one with a public link in `out/pangram_results.json`.

## Results

| | M1: current method | M2: + Joel's fixes catalogue |
|---|---|---|
| T set (48 not fully Human): left unchanged | 19 | 10 |
| T set: became fully Human, meaning PASS | 0 | 5 (3 substantive, see below) |
| T set: changed rewrites whose human share rose / fell by more than 5 points | 3 up, 6 down | 12 up, 4 down |
| T set: mean change in human share | −1.8 points | +6.8 points |
| R set (26 fully Human, wrongly flagged): left unchanged | 11 | 11 |
| R set: changed and no longer fully Human | 2 of 15 | 2 of 15 |
| Meaning FAIL among changed rewrites | 3 of 44 | 5 of 53 |

1. **A single first-pass rewrite rarely fixes a paragraph.** The current method fixed none of 48. With Joel's fixes catalogue, five became fully Human with meaning intact. Two of those five started at 0.99997 human, so only three are substantive fixes: P048 (59% → 100%, every window High), P053 (17% → 100%) and P066 (76% → 100%). Paired, every success was M2's alone (5 to 0; one-sided sign test p ≈ 0.03).
2. **The catalogue moved scores the right way more often.** Among changed T rewrites, M2 raised the human share in 12 and lowered it in 4; M1 raised it in 3 and lowered it in 6. M1's rewrites made the set slightly worse on average.
3. **Rewriting a passing paragraph carries real risk.** Of the 15 flagged-but-passing paragraphs each method changed, 2 per method came back not fully Human. Two of the four are float-level (0.9994 and 0.99999994 human, and one of them is the same text in both arms: both writers changed "it" to "them" for the little one in P032); one is substantive: M2's P029 fell from 100% to 47% after its short diagnostic questions were rewritten into sentences modelled on Joel's P5 lines. Under Joel's standard (100% Human), all count.
4. **Forecasting the rewrites failed outright.** The blind forecaster's accuracy was 54% against 68% for always guessing "not fully Human", AUC 0.53. With round 1 (AUC 0.66 on saved texts), reading is not a substitute for checking, and is worst exactly where a writer has just been working.
5. **Meaning held in about nine of ten changed rewrites.** The failures were stance shifts (a caution turned into permission, a flat claim turned into a hedge) and dropped qualifiers or closing points.

## Dispositions

- Finding 1: **provisional**. Three substantive successes is a small number; the direction matches the 2026-10-24 design's hypothesis that literal owner fixes help more than rules alone.
- Finding 2: **provisional**. Same limits; worth a replication on fresh passage families.
- Finding 3: **provisional**. Supports the production rule that a paragraph which passes is not rewritten on a reader's flag alone.
- Finding 4: **provisional**. Replicates round 1's weak forecasting in a harder setting.
- Finding 5: **no-new-lesson**. It matches the meaning-check record of earlier lanes.

## Limits

One writer per chunk and arm, single pass, no reviewer-writer loop, no Pangram feedback between attempts: this measures a cold first pass, not the full production method. The T set includes four texts already at 0.999+ human, where a flip says little. Writers, checkers and forecasters were the same model family. No article changed.
