# Quote-style flips: findings

Date: 2026-11-03. Preregistration: `README.md` (inputs and predictions frozen at `bc9ac20`, before any check). Results: `RESULTS.json` (all 100 texts returned version 4.1, API, public links); scoring: `score.py` writes `SCORE.json`. Spend: 100 credits.

## Result

Only the apostrophes and quote marks changed in each flipped paragraph. A reading's rank, worst to best: AI, Mixed, Human with a window below High, Human at High throughout.

| Stratum | Flip | n | Better | Worse | Same | Verdict changed |
|---|---|---|---|---|---|---|
| AI | curly to straight | 25 | 2 | 0 | 23 | 2 |
| BORDER | curly to straight | 25 | 11 | 1 | 13 | 2 |
| HUMAN_HIGH | curly to straight | 20 | 0 | 1 | 19 | 0 |
| STRAIGHT_HUMAN | straight to curly | 20 | 0 | 2 | 18 | 0 |

Across AI and BORDER, 13 flips got better and 1 got worse (one-sided sign test p = 0.0009). The ten unchanged repeats kept their verdict and rank 10 of 10; one Mixed repeat's fraction human moved by 0.15 inside the same verdict.

- **Two AI paragraphs read Human once straightened.** `inner-child-therapy-012` went from 0% human to 100% human, every window High ([before](https://www.pangram.com/history/dc8109ea-9872-4857-8188-8824c80e25f2), [after](https://www.pangram.com/history/99260814-2599-4e85-bd48-4b192ac3ea1a)). Its unchanged repeat read AI again ([repeat](https://www.pangram.com/history/238f1c8b-eed5-4bb7-a09b-e2bf4f650982)), so the two quote marks did it. `intentional-communities-113` went from 0% to 100% human, with a window below High ([before](https://www.pangram.com/history/001b2683-88b2-44ef-a7d9-14b852433dad), [after](https://www.pangram.com/history/5aa07ae3-26d8-4b3c-85f9-6d230df015c5)).
- **Borderline paragraphs moved most.** 11 of 25 improved: four Mixed went to Human, one of them `romance-169`, from 79% to 100% human at High ([before](https://www.pangram.com/history/27fc171f-2642-4cdd-8d1a-34036cd92d7e), [after](https://www.pangram.com/history/7f72f7eb-eb34-4fba-a7b9-bf33fd41891e)), and seven Human paragraphs with a Medium or Low window went to High throughout. Eight of the 11 are from the romance article, which made up 11 of the 25 BORDER items (8 of its 11 improved; 3 of the other 14 did). One got worse: `neuro-de-armoring-018`, Mixed from 29% to 9% human ([before](https://www.pangram.com/history/3af7b498-1660-4d25-b5cd-36cdc286f9aa), [after](https://www.pangram.com/history/f4aca799-b6eb-41f3-8315-a91d8ad70171)).
- **Paragraphs already Human at High barely move either way.** Straightening cost 1 of 20 its High (it stayed 100% Human). Curling Joel's straight-quoted paragraphs cost 2 of 20 their High (both stayed 100% Human), and none got better.

## Against the frozen predictions

1. Repeats stable: verdict and rank yes (10/10). The fraction "under 0.01 on each" failed once (0.15, a Mixed paragraph). **Partly wrong.** Fractions inside a Mixed reading are noisy; ranks are not.
2. BORDER 3 to 6 better, at most 2 worse: 11 better, 1 worse. **Wrong in size:** the effect is about twice what I predicted.
3. AI at most 2 change: 2. **Right.**
4. HUMAN_HIGH at most 1 slips: 1. **Right.**
5. STRAIGHT_HUMAN 1 to 4 worse, none better: 2 worse, 0 better. **Right.**
6. More improve than worsen across AI and BORDER: 13 to 1. **Right.**

## What it changes (provisional until replicated)

- Straight apostrophes and quote marks are a real lever on Pangram 4.1, not noise. On a paragraph that reads borderline, straightening improved the reading in 11 of 25 and hurt 1. On a paragraph at 100% Human High it is close to neutral. Joel's own observation ("the curly apostrophes are an AI tell") holds, and his G12 ruling for the gut article (straighten every mark) is supported.
- It is not a cure for AI text. 23 of 25 AI paragraphs stayed AI, and most stayed at 0% human.
- For production, straighten first and check after. Do it on a paragraph that fails or reads below High, before any rewording, since it changes no meaning. In a section that already passes it is optional, and the check decides. joel-articles `docs/HUMANIZATION-GATE.md` says to keep Joel's exact characters. That stays for his own straight marks (curling them only hurt). This result is the evidence for asking him whether curly marks that came from Substack or Gemini may be straightened by default.
- The romance concentration needs a replication on other borderline paragraphs before it counts as general. The BORDER pool has 113 paragraphs, and 25 were used.

## Limits

One model version (4.1), API route only, paragraphs of 25 to 100 words, one seed. Each flip was compared with its own census reading (taken earlier the same day). The ten repeats bound that drift for verdict and rank, but not for the fraction inside a Mixed reading.
