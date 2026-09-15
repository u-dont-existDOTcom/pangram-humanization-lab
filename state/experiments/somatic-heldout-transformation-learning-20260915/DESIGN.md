# Somatic held-out transformation learning — 2026-09-15

Status: PREREGISTERED / WRITER PACKET FROZEN / HELD-OUT HUMAN TARGET SEALED LOCALLY / NO WRITER OUTPUT YET / NO PANGRAM YET

## Owner outcome

Test whether a genuinely fresh model context can learn the manual humanization transformation from aligned AI-before -> Joel-Human-after examples and apply it to a different AI-shaped passage whose actual Joel-Human target is withheld.

This is method research. The Somatic article is already manually humanized and is being used as a positive-control corpus. This experiment does not edit or humanize the article.

## Why this is materially different

Retired methods include incremental next-sentence writing, semantic-persistence controllers, hidden/revealed obligation schemes, prompt anti-pattern accumulation, local register conditioning, paragraph repacking, minimum transformation, and same-context fresh realizations from richer owner cognition. The fidelity/emergence contradiction in incremental generation is considered exhausted rather than newly rediscovered.

This experiment keeps the complete held-out source meaning visible to the writer and supplies examples of the desired transformation itself. It asks the model to infer the operation from demonstrations rather than execute another prose-rule checklist.

## Isolation requirement

The held-out writer must be a genuinely fresh provider conversation/context. Same-context role-play, requests to forget the target, or a writer that has already seen the held-out Human target are invalid.

The actual held-out Human target is not stored in GitHub before generation. Its exact UTF-8 SHA-256 is committed in `SEALED-MANIFEST.json`. The literal target remains local to the supervising environment until writer output is frozen.

## Training material

`WRITER-PACKET.txt` contains three aligned examples selected for distinct transformation behavior:

1. Somatic Experiencing — substantial re-authoring and analogy-led realization;
2. Narrative/Cognitive Integration — expansion from compressed category-list prose into authorial thought;
3. outcomes/evidence paragraph — conversion of generic abstract guidance into concrete author reasoning without changing the basic claim.

The Hâle first-person blocks are excluded. No unrelated Human donor prose is used.

## Holdout

Held-out source: model-origin Brainspotting passage from the 2026-09-05 working merged Somatic prose.

Held-out target: Joel's manual Human Brainspotting realization in the 2026-09-14 manual-humanized PDF. Literal target is sealed locally and withheld from the writer.

## Writer contract

The writer receives only `WRITER-PACKET.txt` in a fresh context. It may infer the transformation from the demonstrations. It must return only one rewritten held-out passage. It may not use external search, GitHub reads, File Library, memory, or other sources. The writer output is frozen byte-for-byte before the held-out target is revealed.

## Evaluation order

1. Freeze writer output and SHA-256.
2. Run semantic/factual sanity against the held-out AI source without consulting the Human target for repair.
3. If independently acceptable enough to test, submit exact writer output to Pangram 4 under a new experiment audit.
4. Reveal the sealed Human target and verify its hash against `SEALED-MANIFEST.json`.
5. Compare transformation behavior and substantive fidelity after detector result is fixed.
6. A success requires more than phrase similarity: fresh generation must be coherent, not invent unsupported personal facts, preserve the core held-out meaning, and materially improve the detector outcome. Replicate on a second holdout before promoting a general generation method.

## Current transport blocker

The existing Mission Control architecture supports fresh ChatGPT provider conversations through a separate Hostinger browser relay, but current diagnostic evidence does not establish a live/usable relay binding from this Chat. The Railway-hosted Mission Control service is running; the browser relay is a separate runtime. Do not fake independence by generating the candidate in the supervising conversation.

Until a genuine fresh-context execution route is available, the correct state is `WRITER_PACKET_READY / EXECUTION_BLOCKED_BY_FRESH_CONTEXT_TRANSPORT`.
