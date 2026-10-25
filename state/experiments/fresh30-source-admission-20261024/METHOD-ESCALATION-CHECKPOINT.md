# Fresh30 measured outcome and method-escalation checkpoint

Date: 2026-10-25
Objective: improve faithful human-sounding Joel prose; do not buy Pangram outcomes by discarding meaning.

## Exact completed evidence

All 30 registered source families have been attempted, nested within six article clusters from one writer. 27 faithful baselines yielded two fresh-restricted-context first attempts; three baselines were fidelity-rejected, never replaced.

Review on the 27 comparisons: Example-assisted B rated more natural 15 times, direct A nine times, three ties. But reviewer overall fidelity-first preference favored A in 19, B in six, and tied twice. A left 15 drafts unchanged, B changed 27; B was longer in 24. B was rated fidelity_ok 21 of 27 versus A 27 of 27. These are same-provider fresh-context reviewer ratings, not owner approval.

Backend Pangram 4.1: a frozen one-per-article six-baseline screen found four categorical Human Written, two AI Generated; a separate earlier T13 AI Generated case was not in that six. One-case T13 earlier version mismatch to requested 4.0 was rekeyed 4.1 with no repeat. The six-case script mistakenly used exact-zero raw AI/assisted floats to call all six not-Human even though four had Human Written categorical headline and every window Human; BASELINE-DETECTOR-ADJUDICATION.json fixes this using actual 4.1 window labels, preserving raw results. Frozen label forecast 5 of 6 correct, far too small for predictive claims.

Only two Pangram AI/High starting baselines were fidelity-admitted for a targeted A/B test. ARM-DETECTOR-PREDICTIONS.json froze forecasts before calls. T16 A and B: both Pangram 4.1 AI Generated/High with fraction_ai 1.0. T26 A was byte-identical to its AI/High baseline and was NOT retested. T26 B was also AI Generated/High, fraction_ai 1.0. Three new paragraph-size paid A/B calls; every result/task/cache is saved in ARM-DETECTOR-RESULTS.json and PANGRAM-BASELINE-CACHE. No article changed.

## Interpretation and escalation

The one-example, one-shot writing architecture did NOT transfer to Pangram Human in two real AI-starting test families. Repeating the same approach with more banned-phrase rules would be correlated refinement. Example-assisted rewriting often made the prose smoother but also encouraged unnecessary expansion or rhetorical meaning drift. These observations are provisional for this data; they do not establish that literal teaching examples are broadly useless. Nor does one-pair detector movement establish a general rule.

## Different architecture

Predeclare and test offline a fixed three-candidate pool on T16 and T26, using genuinely fresh restricted contexts: (1) follow reader attention and real source questions, (2) weave a connected thought through source actors/qualifications, (3) minimal-dose editorial repair. Then use a separate source-aware selector that does not see detector results or arms; allow selection of NONE. Keep exact source, first attempts, semantics, and costs. Do not spend more Pangram credits until candidate quality improves with fidelity, and do not treat same-provider reviewer as owner approval.

No article publication/edit, no repeat Pangram paid call, no false cross-author independence.
