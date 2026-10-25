# Fresh30 findings: the evaluator was rewarding the wrong style

**2026-10-25. Research result, not a new production writing rule.**

## Main finding

The attempted learning method did not establish better humanization. More importantly, its automatic editorial evaluator failed a check against Joel's existing judgments. It preferred the compact original over the owner-golden forgiveness revision, explicitly praising the original's crisp, axiomatic cadence. That is the very kind of difference Joel wanted the system to recognize in the opposite direction.

This does not invalidate the literal generated texts, the frozen Pangram forecasts, or the actual detector responses. It does invalidate treating this evaluator's overall preference counts as validated measurements of Joel's writing quality. All original scores remain preserved rather than being rewritten after the correction.

## What actually ran

Thirty source-paragraph families from six articles were attempted. Twenty-seven produced baseline-admitted paired revisions: A used no teaching example; B received a preassigned literal cross-article example. Three starting drafts were stopped by the programmed gate. Two were judged materially unfaithful by the model; the third (T05) was stopped despite a top-level preservation approval because the reviewer listed a marginal certainty difference. Do not describe all three as proven meaning failures.

The fresh-restricted-context model reviewer scored B more natural in 15 pairs, A in 9, and tied 3. Its overall preference was A in 19, B in 6, and tied 2. It marked B faithful in 21 of 27, A in 27 of 27. These are observations of the evaluator, not accepted owner judgments. A returned the baseline unchanged in 15 pairs; B changed all 27 and was longer in 24. Thus example exposure was associated with more intervention in this setup, not demonstrated improvement in explanatory thought.

The six-case pilot was examined before extending to the other 24; this is exploratory. Thirty passages are nested in six articles from one author, not thirty independent author/style samples. Initial teaching matches were uneven. Model-created baselines were close transformations of registered source prose, which could already have been humanized. The experiment therefore mixes potential humanization with unnecessary-revision controls.

## What Pangram actually measured

A frozen first-eligible-case-per-article baseline screen measured six one-paragraph inputs: T01, T06, T11 and T21 were Human Written throughout their returned windows; T16 and T26 were AI Generated/High. Four of six model-produced baselines did not need detector repair. This is a small selected screen, not a prevalence estimate for all 27.

On the two AI-starting screened families, T16 A and B both remained AI Generated/High. T26 A was exactly the baseline and reused its previous result; T26 B also remained AI Generated/High. All returned fraction_ai = 1.0. These two local non-flips do not prove examples can never help; they provide no successful transfer in the two measured families.

Across the complete recovered detector work there are 10 distinct provider tasks, all one paragraph, totaling 823 whitespace-delimited submitted words: one prior T13 baseline, six screening baselines, and three new A/B texts. The two extra cache records are not extra submissions. No new Pangram call was made during this continuation.

The earlier T13 result returned backend 4.1 despite the runner expecting 4.0. It was recovered and rekeyed without resubmission. Another derived-field bug treated tiny nonzero raw AI fractions as categorical failures although the provider headline and every window were Human Written. The categorical adjudication was corrected, preserving raw fractions and the stricter old numeric gate as distinct records. No provider output was altered.

## Different architecture: candidate pool plus a separate selector

The completed alternate approach generated three first attempts per target using reader-attention, connected-thought and minimum-dose approaches. A fresh selector saw five anonymous versions per case: the three new outputs and the previous A/B controls. For both T16 and T26 it selected old A for joint fidelity/style. In T26 the new minimum-dose version was identical to old A, so this is not a uniquely informative rank between those two copies. No pool result was sent to Pangram. The pool did not supply a new selected improvement in these two cases; it is not a general test of diverse-candidate selection.

## Evaluator calibration against direct owner judgments

Four exact previously owner-scored pairs were used. The model was not shown the owner's ratings or prior detector results. Original A was included as a candidate, recreating the source-conservative setting. The mixed fidelity/style rubric matched none of the four explicit style preferences: two opposite preferences and two ties. On three explicit owner meaning judgments it matched one. Golden forgiveness has no separately recorded owner fidelity rating and was not scored on that dimension.

| Case | Joel's style choice | Mixed reviewer style ranking | Source-free style-only ranking |
|---|---|---|---|
| Repeated advice / envy context | B | A | B |
| Thank-you joke | A | Tie | B |
| Belonging beyond place | B | Tie | B |
| Golden forgiveness | B | A | B |

The golden revision remains owner-golden. The mixed reviewer called it a run-on chain and favored the original's crisp, axiomatic cadence. It also treated changes in perspective and rhythm as missing source properties. That is evidence of a mismatch in the evaluation target, not a reason to override Joel's endorsement.

A second, separately invoked style-only architecture withheld the privileged source block and omitted fidelity scoring. It matched 3 of 4 known style choices. It now recognized the golden revision as a connected thought developing toward a realization. It still preferred removing the thank-you callback, against Joel's judgment that the callback carried humor and made the emoji work.

The second comparison changed both source presentation and instructions, and used the same four calibration cases after the initial mismatch had been seen. It is adaptive local calibration, not a held-out estimate of accuracy or proof that source removal alone caused the change. No source paragraph was rewritten in this continuation.

## Practical decision

Do not promote the present example-assisted generator or the old evaluator. Do not discard the golden example. Stop buying additional detector scores on near-identical local rewrites whose ordinary editorial quality has not improved.

The next evaluation architecture should keep two jobs separate: (1) preservation of actual claims, qualifications, agency, humor and author-intended function, with harmless realization changes explicitly allowed; (2) source-free pairwise style preference calibrated to actual owner choices, not brevity or similarity to the original. Exact owner corrections control known cases. Independent style evaluation is not established merely by placing the same model in another role.

Before another broad writing trial, this separated architecture needs validation on different, literal owner-scored families. The existing four are now calibration data, not a clean holdout. Sparse repair and copied source cadence must not win by definition, and longer/conversational prose must not win by definition either. This is an unresolved evaluation requirement, not a new claim that a writer learned the skill.

## Durable scope

Exact sources, frozen assignments, first attempts, all failures, raw detector results, reviewer responses, calibration labels and the alternative architecture remain in the experiment branch. This report separates measured outcomes from interpretations and proposed design. No article master, owner-final wording, or published article was changed.
