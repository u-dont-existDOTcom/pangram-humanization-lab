# Pangram whitespace sensitivity — historical audit, 2026-08-12

## Trigger finding: Romance oxytocin

A single additional ordinary ASCII space produced a reproducible Pangram-4 classification flip on the exact same visible oxytocin prose.

Minimal pair:

- Single space: `or if people disappeared on you` → **Mixed**, AI fraction `0.4439140856266022`
- Double space: `or if  people disappeared on you` → **Human**, AI fraction `0.0`, high confidence

Fresh measurement identities reproduced both outcomes: the single-space version returned the same Mixed AI fraction again, while the double-space version returned high-confidence Human again. All terminal detector versions were `4.0`.

The owner rewrite also made three visible changes relative to the high-confidence AI endpoint: restarted the condition before `people disappeared on you`; split the reaction inventory after `suspicious`; and changed the final reaction realization to `feel worthless or fight or flight mode may kick in`. Every tested one- and two-factor subset remained full-text AI. All three visible changes together moved the normalized one-space text to Mixed. The extra space then moved that exact wording to full Human.

## Historical audit after discovering the whitespace confound

The discovery required rechecking earlier promoted detector lessons rather than assuming whitespace was harmless.

### Open-list topology — survives normalization

The earlier love-definition finding was rerun on whitespace-normalized Pangram-4 inputs:

- closed list (`agape, metta, loving-kindness, divine love`) → **100% AI**
- open list with `and so forth` → **100% Human**
- open list with `etc.` → **100% Human**

This strongly supports the original local list-openness/topology finding. It is not explained by accidental extra horizontal whitespace.

### Nibbāna r15 X11 owner endpoint — survives normalization

The archived r15 X11 text contained `Buddhist books ,` with a stray space before the comma. Current Pangram-4 retest:

- exact malformed-space version → **100% Human**
- normalized `Buddhist books,` version → **100% Human**

The green endpoint therefore survives removal of that whitespace anomaly on current Pangram 4.

### Nibbāna r16 X111 — no qualitative whitespace effect

The archived r16 X111 text had the same `books ,` anomaly. Current Pangram-4 retest:

- exact malformed-space version → Mixed, AI `0.2250700891`
- normalized version → Mixed, AI `0.1939102560`

Normalization moved slightly toward Human rather than causing the historical improvement. Because the original discovery was made under Pangram 3.3.2, this current-v4 test cannot retroactively isolate the old model's exact whitespace effect; the old v3 finding should be described as historically whitespace-confounded at input, with current-v4 normalization evidence against whitespace being the main explanation.

### Different Levels owner-final r23 — quantitative sensitivity, qualitative result survives

The exact owner-final source contained both a trailing heading space and `Is the  one playing the client...`. Pangram-4 retest on the complete section:

- exact owner text → Mixed, AI `0.1647454351`, Human `0.83525455`
- whitespace-normalized version → Mixed, AI `0.1955320686`, Human `0.8044679165`

The anomalous whitespace made the exact version somewhat more Human-scored, but did not create the Mixed/Human qualitative status. The exact result also reproduces the previously recorded r26 owner-endpoint AI fraction, confirming we reconstructed the relevant historical boundary correctly.

### Romance matched-clause 2×2 — no suspicious horizontal whitespace found

The archived exact Pangram-4 inputs for the matched-clause interaction use ordinary single spaces; the only whitespace difference between submitted text and Pangram's returned echo is normal paragraph/newline normalization. No extra horizontal-space anomaly was present in the tested clauses or boundaries. Therefore there is no anomalous horizontal whitespace to normalize/retest for that experiment.

## Corrected methodological rule

Before promoting any detector flip, owner endpoint, or minimal-pair lesson:

1. compare literal strings, including horizontal runs, tabs, NBSP, leading/trailing spaces, and spaces before punctuation;
2. hash exact submitted texts;
3. if anomalous whitespace exists, test a whitespace-normalized version before interpreting the prose change;
4. repeat any surprising whitespace-sensitive minimal pair with a fresh measurement identity;
5. keep visible editorial effects separate from formatting artifacts and detector variance;
6. do not treat a detector report saying the returned text differs only by whitespace as evidence that the difference is detector-irrelevant.

Do **not** infer `double spaces = human` or inject formatting errors to game the detector. Whitespace sensitivity is evidence about detector brittleness, not writing quality.

## Evidence

- `state/experiments/romance-oxytocin-r1-2026-08-12-results.json`
- `state/experiments/romance-oxytocin-c-2026-08-12-results.json`
- `state/experiments/historical-whitespace-audit-r1-2026-08-12-results.json`
- `state/experiments/historical-whitespace-audit-r2-2026-08-12-results.json`
- `state/ROMANCE-OXYTOCIN-MINIMAL-PAIR-BATCH-2026-08-12.md`
