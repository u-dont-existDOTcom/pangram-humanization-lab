# Pangram whitespace sensitivity — Romance oxytocin case, 2026-08-12

## Finding

A single additional ordinary ASCII space produced a reproducible Pangram-4 classification flip on the exact same visible oxytocin prose.

Minimal pair:

- Single space: `or if people disappeared on you` → **Mixed**, AI fraction `0.4439140856266022`
- Double space: `or if  people disappeared on you` → **Human**, AI fraction `0.0`, high confidence

Fresh measurement identities reproduced both outcomes:

- single-space repeat → Mixed again at the same AI fraction
- double-space repeat → high-confidence Human again at AI fraction 0.0

All terminal detector versions were `4.0`.

## Context

The owner rewrite also made three visible changes relative to the high-confidence AI endpoint:

1. restarted the condition before `people disappeared on you` (`R`);
2. split the reaction inventory after `suspicious` (`S`);
3. changed the final reaction realization to `feel worthless or fight or flight mode may kick in` (`C`).

Controlled cells showed every tested one- and two-factor subset remained full-text AI. R+S+C together moved the normalized one-space text to Mixed. The extra space (`W`) then moved that exact visible wording to full high-confidence Human.

Therefore there are two separate findings:

- the visible owner edit has a local multi-factor interaction and materially changes the detector boundary;
- the final full-Human endpoint is confounded by a reproducible whitespace artifact.

## Rule

Before promoting a dramatic detector flip into a humanization lesson:

1. compare literal strings, including invisible whitespace;
2. hash exact texts;
3. test a whitespace-normalized version;
4. repeat any surprising minimal pair with a fresh measurement identity;
5. separate visible editorial changes from formatting artifacts and detector variance.

Do **not** infer `double spaces = human` or deliberately inject whitespace/errors to game the detector. Detector-sensitive formatting that has no authorship meaning is evidence about detector brittleness, not about writing quality.

## Evidence

Exact variant texts, SHA-256 values, result payloads, and repeats are stored in:

- `state/experiments/romance-oxytocin-r1-2026-08-12-results.json`
- `state/experiments/romance-oxytocin-c-2026-08-12-results.json`
- `state/ROMANCE-OXYTOCIN-MINIMAL-PAIR-BATCH-2026-08-12.md`
