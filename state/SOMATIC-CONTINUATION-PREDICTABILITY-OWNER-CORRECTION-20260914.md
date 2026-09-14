# Somatic continuation-predictability owner correction — 2026-09-14

Status: owner-directed working humanization lesson; no detector call.

Joel judged a fresh model-written probe strongly model-shaped and identified a deeper defect beyond its visible list: the thought continuation from one sentence to the next was highly predictable. He also noted that many previously extracted manual-humanization lessons were already known, so the useful next abstraction is not another anti-pattern list.

## Working representation

Let `S_i` be sentence i and `tau_i` the rhetorical relation producing `S_(i+1)`.

Coarse relation labels may include:
- `E` elaborate/unpack
- `L` enumerate
- `Q` qualify/caveat
- `M` manage scope
- `T` takeaway/synthesis
- `R` restate/close
- `C` real causal or chronological consequence
- `DELTA` source-, observation-, memory-, or judgment-driven turn not demanded by generic exposition
- `STOP`

A high-risk generic chain can look like:

`claim -> L -> M -> T -> R -> STOP`

The failure is not any operator by itself. It is a consecutive low-surprise run where each next move is an obvious generic editorial continuation and the paragraph progressively closes conceptual space.

## Driver dimension

Also label what caused the continuation:
- `D` generic discourse/editorial completion
- `K` claim or causal necessity
- `S` source/lived evidence
- `J` author judgment/decision

Represent a transition as `tau^driver`, such as `L^D` or `C^S`.

A model-shaped paragraph may vary rhetorical operators while still being driven almost entirely by `D`. The repetition is therefore not merely lexical, syntactic, or relation-type repetition; it is repeated generic completion as the cause of continuation.

## Expected-next-move audit

For a model-generated natural boundary, temporarily hide what follows each sentence and ask:
1. What are the two or three most obvious generic editorial moves next?
2. Is the actual next sentence simply one of those moves?
3. If yes, what specifically makes it necessary here: source, causality, chronology, author judgment, or a real reader question?
4. If there is no such reason, is the sentence mainly making the paragraph feel complete?
5. If so, stop or recover the next move from the actual thought/source rather than completing the schema.

Do not optimize for surprise. Random detours, fake specificity, forced anecdotes, quirks, and arbitrary jumps are not humanization. One predictable transition is not a failure; the signal is recurring low-surprise continuation across a natural boundary.

## Distinction from prior lessons

Earlier Somatic work already tracked acoustic cadence, semantic persistence, preservation-unit serialization, owner thought topology, and overcompletion. This correction adds **transition predictability itself**: a paragraph can stay on one live thought yet remain model-shaped because the next rhetorical move is repeatedly too obvious.

Validation remains open. This representation is an owner-correction model, not proof of a successful generator.