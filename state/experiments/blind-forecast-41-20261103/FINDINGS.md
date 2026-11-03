# Round 1 findings: blind forecasts of Pangram 4.1 on saved paragraphs

Date: 2026-11-03. Zero new Pangram calls. Design: `README.md` (committed before any forecast). Exact numbers: `RESULTS.json`, produced by `score.py`. Order of commits on this branch: preregistration → arm A frozen → arm B frozen → answer key → scoring.

## Sample

98 already-scored 4.1 texts, one per near-duplicate family, 24 lanes, 50–400 words (median 108). 50 were fully Human. Of the other 48, 47 were Mixed and only one was fully AI. The sample was balanced on outcome on purpose, so always guessing "Human" scores 51%.

## Results

| | Accuracy | AUC (95% bootstrap) | Brier |
|---|---|---|---|
| Always "Human" | 51% | 0.50 | 0.250 |
| A: cold read | 64% | 0.66 (0.54–0.77) | 0.230 |
| B: with tell inventory | 60% | 0.65 (0.53–0.75) | 0.234 |

Both reviewers raised every probability by a constant after their first pass (disclosed in each arm's `NOTE.md`). That leaves AUC unchanged.

1. **Pre-checks carry a real but weak signal.** Both arms beat guessing. Neither is near good enough to replace a measurement, and the tell inventory did not improve forecasting over a cold read.
2. **Over-calling AI on paragraphs that pass.** Arm B called 26 of the 50 fully-Human paragraphs AI or Mixed; arm A called 20. Arm B's citations, read as rough single-reviewer counts: instruction-manual cadence (T02) was cited 14 times and only 5 of those texts were not fully Human; permission syntax (T10) 2 of 8; self-answered question (T24) 1 of 7. Balanced contrast (T12, 8 of 9), engineered landings (T20, 8 of 12) and T17 (4 of 5) pointed the right way more often. Plain advisory writing with steps, permission and questions often scores Human in these lanes.
3. **Surface quirks fooled the cold reader.** Several paragraphs it called Human on the strength of a joke, an emoji, a casual aside or wordy phrasing scored 0% Human (for example B013, B041, B063, B066, B070). A quirk added to AI-shaped reasoning did not carry the paragraph.
4. **Confidence can't be forecast yet.** 31 of the 50 Human paragraphs had every window at High confidence. Among the Human paragraphs, neither arm separated all-High from lower confidence (AUC 0.44).
5. **Pure-AI calls are almost always wrong in kind.** Reviewers labelled 41–51 texts "AI"; one text in the sample was. The live failure mode in these lanes is Mixed.

## Dispositions

- Findings 2 and 3: **provisional**. One sample, one reviewer per arm, per-tell counts are small, and the reviewers saw only isolated paragraphs. Worth replicating with a second reviewer and fresh lanes before any rule changes.
- Finding 1 and 4: **provisional**. They bear on the production budget: a forecast can't yet stand in for a measurement, and a "should be High confidence" judgement made by reading has no measured basis here.
- Finding 5: **no-new-lesson**. It restates that these lanes already remove most pure-AI text before saving a result.

## Limits

The texts are saved lane outputs, which over-represent paragraphs someone thought worth checking. Family merging used word trigrams, so differently worded rewrites of one thought can still appear twice. Both arms ran the same model. No article or production rule changed.
