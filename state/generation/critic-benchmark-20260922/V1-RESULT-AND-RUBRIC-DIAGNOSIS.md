# Blinded provenance benchmark v1 — result and rubric diagnosis

Date: 2026-09-22
Status: COMPLETED DEVELOPMENT BENCHMARK / RUBRIC V1 FAILED SENSITIVITY / NO PANGRAM CALLS

## Frozen identities

- blind set SHA-256: `cc2c7e99b30fa615433181e4f8b00098c572ff579c20c6368b6df9369e1a1f1e`
- prompt SHA-256: `5a4bc5e5f5ccf519fb681556d2e56ff3fbcde9ff36100636425564d38492fe19`
- hidden gold-key pre-run SHA-256: `83680c6353986aa1646750d88787c90b3d2f5e7bbde3b26117b25748933a35cf`
- frozen Venice response record SHA-256: `43068ed7f7ee17f0016b8e3235eb947aa66e46cb635a4a797482ca1e37ba3049`
- exact benchmark runner source commit: `f7031def5279f8c1c3a14c949dadb671db61e6f5`
- response-freeze commit before gold reveal: `81952162b5dbaba6afe900a38098bd5575060ad4`
- Venice model alias: `gpt-5.6-sol`
- returned provider model: `openai-gpt-56-sol`
- calls: 20 stateless chat-completions requests through the authenticated UDA Venice gateway
- Pangram calls: 0

## Score

- total: **14/20 = 70%**
- HUMAN: **10/10**
- AI: **4/10**
- invalid/missing: **0**

This is not a calibrated production gate.

## False negatives

All six errors were AI passages classified Human:

- B03 / A07 — model paragraph;
- B04 / A05 — model paragraph;
- B06 / A02 — model candidate;
- B09 / A06 — model paragraph;
- B17 / A03 — model-generated article candidate;
- B20 / A04 — model output whose provenance had previously been corrected after an owner/machine attribution mix-up.

There were **no** Human passages classified AI.

## Repeated failure mechanism

The critic often identified the model-shaped architecture correctly and then allowed one or more positive-looking features to override it.

Across the six misses it credited:
- a concrete reaction such as `ugh, no`;
- a substantive judgment such as preserving the reader's `no`;
- an unresolved endpoint;
- a real-seeming social act toward the reader;
- source-grounded-looking specifics;
- a sustained metaphor whose details carried the lesson.

Those are not reliable authorship evidence. A language model can deliberately generate each one.

The v1 rubric said Human-facing relations should be inspected after the AI case, but it still let them operate as positive votes. This recreated the earlier production failure in a more measurable form: **simulated Human-facing relations can mask a still-engineered semantic topology.**

## What v2 must change

1. **Cumulative AI topology gets veto priority.** If the functional skeleton is strongly model-shaped, a Human-looking device cannot clear it merely by being concrete, emotionally plausible, or rhetorically apt.
2. **Human evidence must contain surplus.** A detail counts against the AI hypothesis only when it does more than perfectly service the teaching objective—e.g. it creates genuine unevenness, context dependence, unresolved social residue, or authorial partiality that is not interchangeable with another equally apt didactic detail.
3. **Purpose-built concreteness is not Human evidence.** A scene/metaphor can skin a staircase. Map each concrete element back to its instructional function; if the mapping is unusually one-to-one and efficient, treat that as AI evidence.
4. **Unresolvedness can be engineered.** Ending without a solution is not Human evidence when the lack of resolution itself cleanly performs the intended lesson.
5. **Authorial judgment can be simulated.** A strong opinion is Human evidence only when its realization introduces non-required perspective/context, not when it is simply the passage's crisp thesis.
6. **Content-neutralization is mandatory.** Replace names, topic nouns, and vivid specifics mentally with placeholders. If the same maximally efficient teaching architecture remains, the specifics do not rescue it.
7. **The classifier must explain why any positive Human signal actually disrupts the model-shaped scaffold.** If it cannot, the signal is non-diagnostic.

## Experimental consequence

The 20 v1 items are now **development data**. They may be used to tune rubric v2, but never again as an untouched validation set.

A later `20/20` claim requires a new frozen holdout selected from unused provenance-secure Human and AI passages before that holdout's first classification call.

A separate detector-disagreement stress set should include known model-written passages that Pangram has classified Human in a tested boundary. Those remain AI by provenance and are useful specifically because Pangram success does not define the ground truth.
