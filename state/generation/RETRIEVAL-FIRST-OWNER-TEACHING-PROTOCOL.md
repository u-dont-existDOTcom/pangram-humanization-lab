# Retrieval-first owner teaching protocol

Status: ACTIVE RESEARCH / generation-method durability

Date: 2026-09-15

## The durability failure this repairs

The humanization work repeatedly learned useful things during a live Joel correction loop and then saved only the abstraction: e.g. `avoid overcompletion`, `preserve the live thought`, or `restore complete thought before realization`.

That compression destroys much of the learning signal. A fresh writer does not receive the actual model sentence/paragraph that failed, the exact owner correction that taught the distinction, or the next model realization that demonstrated transfer. It therefore has to reconstruct the lesson from a slogan and often falls back into the same model prior.

The durable unit is an **episode**, not merely a rule:

`literal model-before -> literal Joel aligned rewrite/correction -> literal subsequent model transfer (if attempted) -> outcome`

The corpus for these episodes is:

`state/generation/OWNER-ALIGNED-TRANSFORMATION-CORPUS-v1.json`

## Alignment gate

Before adding an owner rewrite as a generation demonstration, classify it.

### ALIGNED_SAME_THOUGHT

Joel deliberately preserved essentially the same substantive thought/function and changed its realization. This is the highest-value positive training evidence.

Use it for few-shot retrieval.

### OWNER_REAUTHORING

Joel added, removed, changed, or rerouted substantive thought. This is valuable article authority and authorial cognition, but it is **not** clean evidence for how to humanize the same thought.

Do not present it to a writer as a style-transfer target.

### CONTROLLED_REVERSE_ALIGNED_PAIR

A Human owner baseline was later transformed into an AI-shaped controlled variant while protected meaning was held fixed. It can be read in reverse to teach a realization difference, provided chronology remains explicit.

### TRANSFER_SUCCESS_WITH_OWNER_INTERVENTION

After an owner correction/teaching episode, the model generated another realization that successfully carried the learning. Preserve this separately from owner prose. It is particularly valuable evidence that the generator—not only the critic—changed behavior.

### LEGACY_INDEX_ONLY

We know an old episode/outcome exists, but the exact literal teaching artifacts are not yet recovered into the corpus. Never reconstruct the missing bytes from memory. Keep the pointer and recover the exact artifacts when useful.

## Retrieval before generation

For a new model-shaped paragraph or short natural boundary:

1. Recover the exact target meaning and provenance normally.
2. Query the corpus for **2–4** eligible episodes with the closest transformation problem: semantic compression, explanatory completion, relationship announcement, model-polished synthesis, hidden taxonomy, etc.
3. Prefer examples with the same kind of rhetorical job over examples sharing surface vocabulary or topic words.
4. Give the writer the literal before/after demonstrations. Do **not** replace them with a list of generalized prohibitions.
5. Give the writer the complete current target meaning needed for fidelity. Do not hide future meaning to manufacture false incrementalism.
6. Ask for one whole realization of the target. The demonstrations are examples of transformation, not phrase banks.
7. Cold-read the first pass before supplying critic diagnoses. If it obviously remains model-shaped, do not spend Pangram merely to certify the obvious failure.
8. If Joel corrects that candidate while keeping the thought aligned, immediately capture the new episode before continuing.

## What the writer must not do with demonstrations

Never transplant anecdotes or memories, names or personal facts, jokes/catchphrases, distinctive wording merely because it appeared in a successful example, factual claims from another topic, or punctuation/errors/slang as camouflage.

The examples teach **how the realization changed**, not what words to copy.

## Capture immediately after Joel teaches the paragraph

Do not wait for article completion.

For every useful aligned correction, store:

- literal failed model paragraph;
- literal Joel rewrite/correction;
- SHA-256 for both;
- exact provenance and chronology;
- semantic-alignment classification;
- any changed/added/removed substantive units;
- short transformation annotation for retrieval only;
- the next fresh or ordinary model attempt, if one is made;
- whether the next model attempt transferred the lesson without sentence-specific repair;
- detector result only when the cold read is uncertain or a controlled experiment genuinely needs it.

If the owner rewrite changes the thought, store it as `OWNER_REAUTHORING`, not as a failed alignment pair.

## Transfer is the primary generator-learning evidence

A paragraph becoming good after Joel rewrites it proves Joel can rewrite it. It does not by itself prove the model learned.

The stronger event is:

1. model fails;
2. Joel supplies an aligned correction;
3. model sees that correction;
4. on a different target, the model produces a materially better first pass;
5. the improved realization survives owner/cold review, and detector only if genuinely needed.

Record step 4 literally. Do not summarize it away as `the model learned X`.

## Relationship to abstract lessons

Abstract lessons remain useful as indexing/search metadata and post-hoc explanation. They are no longer the sole durable representation of successful owner teaching.

A rule such as `avoid explanatory aftercare` may help retrieve relevant episodes, but the writer should normally see the actual transformation examples rather than a growing environment of prohibitions.

## Relationship to Pangram

Pangram is not a mandatory checkpoint for every episode.

Use it when a competent cold read is genuinely uncertain whether the passage remains AI-shaped, an exact controlled experiment needs a detector outcome to distinguish hypotheses, or a production boundary requires detector certification under a current owner/task contract.

Skip it when the candidate plainly still looks model-generated and the detector cannot change the next decision.

## Current corpus limitations

Version 1 starts conservatively.

- The EFT episode has exact failed and successful Chat transfer text, but the exact intervening Joel teaching bytes have not yet been recovered. It therefore remains transfer evidence rather than an owner-demonstration pair.
- The compact Somatic trauma C0/C1 pair has exact text and preservation evidence, but its chronology is Human -> controlled AI. It is eligible only as an explicitly reverse controlled pair.
- r19/r20/r22/r25 are indexed with historical outcome evidence but remain ineligible for literal retrieval until their exact before/restrained/owner texts are imported.

Do not fill these gaps from memory. Add exact historical artifacts when recovered, and capture all new owner teaching episodes prospectively so this problem stops recurring.
