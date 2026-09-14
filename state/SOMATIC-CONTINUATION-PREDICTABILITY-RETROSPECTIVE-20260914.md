# Somatic continuation-predictability retrospective — 2026-09-14

Status: **EXPLORATORY RETROSPECTIVE / OWNER-DIRECTED / NON-BLIND / NO DETECTOR CALL**

Purpose: test the 2026-09-14 owner correction that model-shaped prose can be recognizable from the predictability of the thought continuation from one sentence to the next.

This is a retrospective consistency check against already-labeled boundaries. Because the detector labels were known while coding, this is not independent validation and must not be represented as a classifier result.

## Representation

Code a transition as:

`tau_i = (relation, driver, predictability, closure)`

Relation examples:
- `E` elaborate/unpack
- `L` enumerate
- `Q` qualify/caveat
- `M` scope management
- `T` takeaway/synthesis
- `R` restate/close
- `C` causal/chronological consequence
- `DELTA` a genuine turn in the live thought

Driver:
- `D` generic discourse/editorial completion
- `O` visible obligation/inventory consumption
- `K` intrinsic causal/logical necessity
- `S` actual source/observation/lived evidence
- `J` author judgment/question/decision

Closure:
- `UP` opens or redirects live pressure
- `FLAT` sustains it
- `DOWN` closes/constrains conceptual space

`P` means the relation class is a low-surprise next move at that point. This is rhetorical predictability, not token probability.

## Retrospective cases

### Human-labeled boundaries

1. Stage-2 mixed-provenance cluster — Human / medium
   - approximate route: `E^K -> C^(J/K) -> Q^K -> C^K -> DELTA^J -> E^J -> DELTA^J`
   - generic/editorial closure does not form a sustained run; the later movement is driven by owner observation/judgment.

2. Aquatic opening — Human / medium
   - approximate route: `E^S -> DELTA^(J/S) -> Q^S`
   - locally predictable moves are source-specific and interrupted by a different live concern.

3. Redistributed aquatic full boundary — Human / medium
   - approximate route: `E^S -> DELTA^(J/S) -> Q^S -> DELTA^S -> C^S -> DELTA^J`
   - no sustained generic completion chain.

4. Owner five-stage realization — Human / high
   - macro route is a predictable sequence by design: `C^K x4`.
   - this is a direct counterexample to any rule that treats predictability itself as AI-shaped. The sequence is the author's actual claim; it does not repeatedly add a label-plus-gloss completion around each step.

5. Raw tender owner control — Human / medium
   - contains causal persistence, repetition, self-repair, and enactment, but does not move monotonically through generic explanation slots toward a polished close.

### AI-labeled boundaries

1. Stage-1 Yoga probe — AI / medium
   - approximate route: `E^D -> E^D -> Q^D -> E^D -> E^D -> E^D -> T^D`
   - long low-surprise discourse-driven run; conceptual space is progressively closed.

2. Aquatic failing tail — AI / high
   - approximate route: `C^O -> C^O -> C^O -> T^D`
   - the source packet becomes a compact procedural staircase; each next sentence consumes the next expected function.

3. Independent night-walk probe — AI / high
   - several paragraphs repeat a broad route of `claim -> details/examples -> interpretation/landing`.
   - one paragraph contains a long sequence of same-class example elaborations followed by a synthesis.
   - exact lexical details vary, but the rhetorical next move remains easy to predict.

4. Model five-stage list — AI / high
   - the main failure is not a single long run because the real stage order is structurally required.
   - instead the repeated motif is approximately `(stage label -> explanatory gloss)^O x5`.
   - this shows that motif recurrence must be tracked in addition to consecutive runs.

## Positive-control countercheck

Joel's manually humanized Somatic V4 is owner-reported Pangram 100% high-confidence Human for the exact whole article. It contains some locally predictable sequences, including a practitioner-care sequence in the aquatic material.

Therefore:

- a high local continuation-predictability score cannot be a universal failure rule;
- source/causal sequences and declared lists can legitimately be predictable;
- local flags must be interpreted inside the larger article movement;
- the stronger contrast with the pre-humanization model source is cross-boundary route reuse: the older model repeatedly gives modalities similarly complete explanatory profiles, while the manual article changes rhetorical route substantially from section to section.

A rough matched-section coding found heavy adjacent-route reuse in the older model sections and little route reuse across the corresponding manual sections. This coding is subjective and non-blind, so no numerical threshold is claimed.

## Revised hypothesis

Reject the simple hypothesis:

`AI-shapedness ~= long run of predictable next moves`.

Retain the narrower hypothesis of **editorial inevitability**:

> Risk rises when a natural boundary contains a sustained run of low-surprise transitions that are driven by generic discourse or visible obligation consumption, progressively close conceptual space, and/or instantiate a transition motif that recurs across otherwise independent sections.

The useful representation therefore needs two scales:

### Local scale

Track whether transitions form an `inevitability run`:

`predictable + discourse/obligation driven + closure directed`

Do not count a transition merely because causality, chronology, or an explicitly claimed sequence makes it predictable.

### Cross-boundary scale

Represent each natural section as a transition signature and look for repeated bigrams/trigrams or repeated miniature programs across independent subjects.

Examples of risk shapes:
- repeated `claim -> explanation -> caveat -> synthesis`
- repeated `fit -> mechanism -> safety -> takeaway`
- repeated `label -> gloss`
- repeated `problem -> intervention -> aftercare -> screening close`

The literal operators are not banned. The signal is recurrent routing.

## Current result

- Raw continuation predictability: **PARTIAL / INSUFFICIENT**.
- Driver-aware, closure-aware continuation coding: **CONSISTENT WITH THE REVIEWED CASES**, but subjective and non-blind.
- Cross-boundary route recurrence: **STRONG SUPPORTING EXPLANATION** for the contrast between the old model-shaped Somatic source and the manual positive control.
- Automatic threshold/classifier: **NOT ESTABLISHED**.
- Generation recipe: **NOT ESTABLISHED**.

## Production use now

Use this as a diagnostic representation, not another anti-pattern checklist.

Before delivering a newly model-generated natural boundary:
1. symbolize its transition route after drafting;
2. mark the low-surprise moves;
3. ask whether they are genuinely required by source/causality/judgment or are completing editorial slots;
4. check whether the same route has already been used in neighboring independent sections;
5. if the boundary shows a long editorial-inevitability run or repeats the prevailing section grammar, do not patch one sentence; change the thought route or stop and recover stronger owner/source cognition.

Do not optimize for surprise, randomness, quirks, anecdotes, or broken grammar. This representation is intended to detect model routing, not manufacture human irregularity.
