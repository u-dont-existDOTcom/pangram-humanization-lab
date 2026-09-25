# Inner Child Episode 007 — R8D sentence-pass detector result

Date: 2026-09-16

Disposition: **boundary-local generation/detector evidence; not article authority**

## Exact candidate

Joel Articles branch: `task/inner-child-therapy-intake-20260915`

Candidate: `articles/inner-child-therapy/experiments/EPISODE-007-MY-JOURNEY-CANDIDATE-R8D-SENTENCE-PASS-20260916.json`

SHA-256: `1df78ef135579076e0b52b7f448d1854df8129a140c1a30c0f9eb4e446e15039`

Method: the same-context writer did **not** regenerate the section holistically. It followed a previously frozen sentence-level disposition guide (`rewrite`, `merge`, `delete-as-separate-sentence`, `keep`) on the three prior AI/high regions, then integrated the section.

## Blind prediction before screenshot

Before seeing the result screenshot, Chat durably predicted:

- AI/high for the practical-danger -> no-self -> therapy/resistance run;
- AI/high for the first part of the final method-origin paragraph;
- Human, likely lower confidence, for the final sentence beginning `The three adult jobs from the map...`.

## Owner screenshot result

- Human / High — 348 UI words;
- AI / High — 187 UI words;
- Human / High — 150 UI words;
- AI / High — 45 UI words;
- Human / Medium — 50 UI words.

Displayed AI share: `232 / 780 = 29.74%`.

The red regions and Human/medium tail matched the blind prediction.

## Comparison

Prior exact R8C displayed AI share: `39.67%`.

R8D sentence pass displayed AI share: `29.74%`.

This is material progress, unlike the essentially flat R7 -> R8C whole-boundary iterations.

## Supported local lesson

A generator that repeatedly rebuilds a known model-shaped section when asked for holistic rewrites may improve when the critic first assigns **sentence-level operations** and the writer executes those operations locally before integration. This is not a universal detector recipe; it is boundary-local evidence that decomposing the generation task can change the generator's output prior.

The remaining 187-word failure is no longer primarily sentence-local. Its strongest editorial defect is section-scale outline pulse: danger, no-self timing, and therapy disagreement still arrive as three consecutive compact advice mini-essays. The remaining 45-word failure still allocates one beat each to `simple setup -> protective obstacle -> child-state obstacle`.

The 50-word causal tail after that red span is Human/medium and should not be reopened for detector reasons merely because Medium is lower than High.

## Next discriminating step

Use a second targeted sentence/paragraph operation pass only on the two AI/high regions while freezing the known-green spans. For the 187-word region, remove the independent mini-essay closures and let no-self hand directly into therapy through their shared `emerging self / ability to say no` pressure. For the 45-word region, demote the protective-part issue and let loss of adult perspective dominate before handing into the known-Human tail.

If either residual remains AI/high after that pass, stop same-context optimization for that residual and require owner language or genuinely fresh context rather than adding more anti-pattern rules.
