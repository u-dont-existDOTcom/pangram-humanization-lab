# Quote-style flips on Pangram 4.1 (preregistration)

Date: 2026-11-03. Owner direction (Joel, 2026-11-03): use this week's spare Pangram credits on work that teaches humanization better and quicker. Joel, the same day, on the gut article: "and yes the curly apostrophes are an AI tell i know that". Status: INPUTS AND PREDICTIONS FROZEN before any check.

## Question

Does the apostrophe and quote-mark style alone move Pangram 4.1's reading of a paragraph? joel-articles `docs/HUMANIZATION-GATE.md` (2026-10-02) records one pair: a section-3 paragraph of Joel's read 100% Human with his straight apostrophes and 100% AI with the same words curled, while another paragraph passed both ways. The gut article now has every curly mark straightened (Joel's G12, 2026-11-03). This measures how often the style decides the reading, in which direction, and where.

## Design

`build_sample.py` takes the census's frozen paragraphs and results (branch `research/paragraph-census-41-20261103`, commit `8b3a009`: 1,536 paragraphs, each checked alone through the API, 4.1) and keeps paragraphs of 25 to 100 words (one credit each) with at least two quote marks, all of one style. It samples, seed 20261103:

| Stratum | Census reading | Flip | n | Pool |
|---|---|---|---|---|
| AI | AI | curly to straight | 25 | 226 |
| BORDER | Mixed, or Human with a window below High | curly to straight | 25 | 113 |
| HUMAN_HIGH | 100% Human, every window High | curly to straight | 20 | 234 |
| STRAIGHT_HUMAN | Human (any confidence) | straight to curly (editor-style smart quotes) | 20 | 42 |

Only the quote characters change: same length, every other character identical (asserted). Ten originals (the first five AI and five BORDER items) go through again unchanged, in a fresh output folder so the client's cache can't answer, to measure how much a repeat moves the reading. 100 credits in all.

Each flipped text is compared with its own census result (same API route, same 4.1 model). Outcomes: the verdict (Human = 100% Human, Mixed, AI), the fraction human, and each window's confidence.

## Frozen predictions (before any check)

1. Repeats: 10 of 10 give the same verdict, and the fraction human moves by under 0.01 on each.
2. BORDER, curly to straight: 3 to 6 of 25 move to a better reading (Mixed to Human, or a below-High window up to High), and at most 2 move worse.
3. AI, curly to straight: at most 2 of 25 change verdict (most census AI paragraphs read 0% human; a quote mark rarely moves those).
4. HUMAN_HIGH, curly to straight: at most 1 of 20 stops being 100% Human at High.
5. STRAIGHT_HUMAN, straight to curly: 1 to 4 of 20 get worse (a window drops below High, or the verdict leaves Human); none get better.
6. Direction overall: across BORDER and AI, more flips improve than worsen (sign test, one-sided).

## What the answer changes

- If straightening helps and never hurts: straight marks become a standing production step for every article (as G12 did for the gut article), and the tell inventory's curly-quote entry gets its measured size.
- If it helps some and hurts others: the style is a per-paragraph lever, to try only on paragraphs that fail, with a check either way.
- If it does nothing beyond repeat noise: the single 2026-10-02 pair was noise or context, and the inventory entry is downgraded.

## Files

`build_sample.py`, `FLIP-INPUTS.json` (the items, their census results and hashes), `TEXTS.json` (what goes to the API). Results, scoring and findings follow in this folder.

## Replication of the BORDER arm (preregistered 2026-11-03, after the first results and before these checks)

The first run's BORDER gain (11 better, 1 worse of 25) was about twice my prediction and concentrated in the romance article (8 of its 11). `build_replication.py` takes every other paragraph in the same BORDER pool under the same rules: 88 paragraphs (romance 28, nibbana 30, intentional communities 15, inner signal 7, inner child therapy 4, neuro de-armoring 4), curly to straight, 88 credits. Scored by `score.py REPL-INPUTS.json REPL-RESULTS.json REPL-SCORE.json` against each paragraph's own census reading.

Frozen predictions:

1. 26 to 44 of 88 improve (30 to 50%), and at most 6 get worse.
2. Outside romance (60 paragraphs), at least 12 improve (20%).
3. More improve than worsen (one-sided sign test p < 0.01).

If (1) and (3) hold, straightening becomes the first step for any paragraph reading below 100% Human at High, before any rewording (proposed to Joel, since his gate keeps his characters as typed).
