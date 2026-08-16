# Romance whole-article Pangram overlay — 2026-08-16

## Exact detector boundary

- detector: Pangram 4.0
- reader-visible SHA-256: `99c803c7eda079582a8ba76b6524dcf726ece42e44e8f85796438b929594ea40`
- reader-visible words: 18,357
- result: Human, 92.997789% Human / 7.002211% AI / 0% AI-assisted
- localized AI segments: 11, all High confidence
- result file: `state/experiments/romance-current-master-visible-final-r2-2026-08-16-results.json` on `automation/pangram-fixed-batch`
- workflow run/job: `31947861945` / `95166666600`, success

This overlay is secondary evidence. A red segment is not a phrase-level verdict and does not override owner-final prose, locked sections, source authority, or the living article map.

## Segment overlay

| # | Reader-visible indices | Architecture node | Detector span / editorial disposition before rewriting |
|---|---:|---|---|
| 1 | 4595–6867 | `Talk about making love` → opening of locked `Casual Sex` | 413 words. Begins `Sex drives are independently alive...` and crosses the H2 boundary into pregnancy/STI/attachment/casual-sex material. **Mixed-authority boundary.** Diagnose Talk separately; do not rewrite locked Casual merely because it shares the red window. |
| 2 | 35109–35530 | `If slow isn’t realistic for you` | 69 words. Gandarussa contraception claim + `don’t let everything else speed up`. **Concrete factual/logic review required** before stylistic repair; do not silently change the claim. |
| 3 | 35955–36493 | `If slow isn’t realistic for you` | 91 words. Formal check-ins → wanting someone vs co-parent/life-partner fitness. **Likely thought-routing defect:** two useful thoughts are adjacent without a live-question bridge. |
| 4 | 37067–37686 | `Slow steady may win...` | 112 words. Long sexual-fit list → possibility of improvement → `Let’s just be friends!` → explanation of why the conversation is hard. **Likely overpacked/aftercare boundary.** Preserve the unique sexual-fit limitation; inspect where the thought should stop. |
| 5 | 56621–56843 | `Primal attraction / Desire is expressed differently` | Two sentences: women ask/reach/name wants; men provide/fix/become indispensable. **Likely tidy male/female symmetry.** Check source/owner provenance and lived examples before changing the claim. |
| 6 | 57772–58521 | `Primal attraction / Not A Performance` | 137 words from heading through symmetrical woman paragraph. Includes natural Bee `wife` example. **Likely model-shaped symmetry around genuine owner material.** Recover source thought; do not delete the Bee example merely because the whole boundary is red. |
| 7 | 68887–69120 | `Two Pillars` | `Romantic love can last... community is one... Community isn’t magic either.` **Strong aftercare/restatement suspect.** The preceding paragraphs already demonstrate dyad overload; following paragraph immediately supplies the important qualification. |
| 8 | 72362–72607 | `Two Pillars` close | 45-word lifetime-love / don’t become entire social world / keep friendships conclusion. **Summary suspect**, but `friendships aren’t automatically a threat` may be a unique payoff. Test function before cutting. |
| 9 | 76900–77451 | `Why marriage vows... / Attraction and exclusivity` | 90-word historical summary: agriculture/property/inheritance, Industrial Revolution, tribal flexibility/social monogamy. **Strong empirical-claim review candidate.** Pangram is secondary; verify before any substantive rewrite because claims are sweeping and historically specific. |
| 10 | 95959–96219 | `Ending consciously` → `After leaving` boundary | Crosses section boundary: final community-witness sentences + heading + opening breakup/public-demonization clause. **Boundary artifact likely.** Do not rewrite heading/opening merely because detector segmentation crosses them; inspect the preceding community recap separately. |
| 11 | 96423–97596 | `After leaving` | 195 words: public truth-telling scope → post-breakup reinterpretation → perspective-taking → neutral opinions → spiritual practice/loving ex. **Likely generalized instructional sequence/aftercare.** Recover owner source pool and identify the minimum lived/intellectual route rather than paraphrasing the red block wholesale. |

## Immediate prioritization

### Highest-confidence editorial opportunities without factual research

1. Two Pillars segments 7–8: test real stopping points and duplicate thesis restatement.
2. If-slow segments 3–4: separate packed thoughts and remove explanatory aftercare only where the live question is already answered.
3. Ending/After leaving segments 10–11: inspect source provenance and generalized advice tail.
4. Primal segments 5–6: inspect source/owner provenance for synthetic symmetry around genuine lived material.
5. Talk segment 1: separate current Talk realization from locked Casual material before any edit.

### Requires factual verification before substantive claim change

- segment 2: Gandarussa contraceptive efficacy/safety relative to condoms.
- segment 9: historical development of sexual exclusivity/monogamy and cross-cultural `social monogamy` claims.

Do not let a detector localization become permission to soften either claim. Verify the claim first if a prose change would materially alter it.

## Supported detector lesson

This whole-article result repeats the lesson from `If you're already in it` and Tough Love: detector spans often cover multiple rhetorical functions and can cross heading/authority boundaries. The correct unit of repair is the thought/architecture node, not every sentence inside the red span. A locked or later-green sentence inside a red window remains a counterexample against phrase superstition.

## Next action

Work the red nodes in article order after source/provenance inspection. Make only semantic/coherence-motivated edits, update `ARCHITECTURE.md` if topology changes, reassemble deterministically, cold-audit each repaired boundary, and use Pangram only after a coherent candidate exists. Do not spend calls on unchanged locked material.
