# Dash-style flips on Pangram 4.1 (preregistration)

Date: 2026-11-03. Owner direction (Joel, 2026-11-03): use this week's spare Pangram credits on work that teaches humanization better and quicker. This follows the quote-style experiment (`state/experiments/quote-style-41-20261103/`, PR #195). There, straightening curly marks improved 40 of 113 borderline paragraphs and hurt 4. Status: INPUTS AND PREDICTIONS FROZEN before any check.

## Question

The em dash is the best-known AI tell, and Joel's writer briefs ban it. Does the dash alone move Pangram 4.1's reading? The test changes each em dash to the dash Joel himself types. His paragraphs that read Human at High hold 41 spaced en dashes in prose (" – "), against 12 em dashes and 1 spaced hyphen.

## Design

`build_sample.py` takes the census's frozen paragraphs and results (branch `research/paragraph-census-41-20261103`, commit `8b3a009`), 25 to 100 words, with at least one em dash. Each em dash (with or without spaces around it) becomes " – ". Nothing else changes: quote marks stay as they are.

| Stratum | Census reading | n | Pool |
|---|---|---|---|
| AI | AI | 30 | 54 |
| BORDER | Mixed, or Human with a window below High | 17 | 17 (all) |
| HUMAN_HIGH | 100% Human, every window High | 10 | 10 (all) |

57 credits. Scored with the quote experiment's `score.py`, which ranks readings AI < Mixed < Human below High < Human at High and compares each flip with its own census reading. The quote experiment's ten repeats found verdict and rank stable, so no repeats are spent here.

## Frozen predictions (before any check)

1. BORDER: 3 to 7 of 17 improve, at most 2 get worse.
2. AI: at most 3 of 30 change verdict.
3. HUMAN_HIGH: at most 1 of 10 slips below High.
4. Across AI and BORDER, more improve than worsen.

## What the answer changes

If the dash helps like the quote marks did, "em dash to spaced en dash" joins straightening as a meaning-free first step, proposed to Joel the same way. If it does nothing, the em dash tells a reader something but not this detector, and the tell inventory says so.
