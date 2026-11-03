# Dash-style flips: findings

Date: 2026-11-03. Preregistration: `README.md` (inputs and predictions frozen at `90f874c`, before any check). Results: `RESULTS.json` (57 of 57 returned 4.1, API, public links); `score.py` writes `SCORE.json`. Spend: 57 credits.

## Result

Each em dash became a spaced en dash (" – "), the dash Joel types. Nothing else changed.

| Stratum | n | Better | Worse | Same | Verdict changed |
|---|---|---|---|---|---|
| AI | 30 | 3 | 0 | 27 | 3 |
| BORDER | 17 | 6 | 0 | 11 | 2 |
| HUMAN_HIGH | 10 | 0 | 0 | 10 | 0 |

Across AI and BORDER, 9 got better and none got worse (one-sided sign test p = 0.002).

- **Three AI paragraphs stopped reading AI.** Two read 100% Human: `neuro-de-armoring-087` went from 0% to 100% human ([before](https://www.pangram.com/history/7feff475-8a5f-4cec-8e65-7354422a5a56), [after](https://www.pangram.com/history/4466d025-832e-4ae6-895a-be2fe41aec43)), and `inner-signal-153` from 5% to 100% ([before](https://www.pangram.com/history/a64f03c9-ab2b-4a28-82a7-6b9666a43d12), [after](https://www.pangram.com/history/44fbfcba-1695-4c86-8691-3746aeb044f9)). The third, `inner-signal-112`, went to Mixed.
- **6 of 17 borderline paragraphs improved and none got worse.** Three Mixed paragraphs went to Human, for example `inner-child-therapy-216`, from 41% to 100% ([before](https://www.pangram.com/history/7f2fde2b-b422-4b2a-b2f2-a64dee170a5c), [after](https://www.pangram.com/history/d3138280-3cf4-40e2-8a8d-facef38e5af5)). Three Human paragraphs went from a Medium or Low window to High throughout.
- **The ten paragraphs already Human at High didn't move.**

## Against the frozen predictions

1. BORDER 3 to 7 better, at most 2 worse: 6 and 0. **Right.**
2. AI at most 3 change verdict: 3. **Right**, at the edge.
3. HUMAN_HIGH at most 1 slips: 0. **Right.**
4. More improve than worsen: 9 to 0. **Right.**

## What it changes (provisional)

- The em dash is a lever on Pangram 4.1, the same kind as the curly quote mark, and about as strong on borderline paragraphs (35% improved there, 35% here). Here it never hurt. It rescued more AI paragraphs (3 of 30, against 2 of 25 for quote marks).
- With the quote result (`state/experiments/quote-style-41-20261103/`), the proposed first step for any paragraph reading below 100% Human at High becomes: straight quote marks and Joel's spaced en dash in place of each em dash, check, and keep it only if it reads at least as well. It changes no meaning and costs one check. It needs Joel's ruling, since his gate keeps his characters as typed. Most em dashes in his posts came from Gemini or the editor rather than from him: his Human-at-High paragraphs use the spaced en dash 41 times to the em dash's 12.
- Not replicated: the borderline pool here was all 17 paragraphs available at 25 to 100 words. A replication needs longer paragraphs or new articles.

## Limits

One model version (4.1), API only, one sample, 25 to 100 words. Quote marks were left as they were, so the two levers were tested separately and never combined. Each flip was compared with its own census reading from earlier the same day. The quote experiment's ten repeats found verdict and rank stable between identical checks.
