# Somatic held-out transformation learning — 2026-09-15

Status: COMPLETE AS DIAGNOSTIC / HELD-OUT TARGET UNSEALED AFTER WRITER FREEZE / CLEAN SAME-MEANING HOLDOUT INVALIDATED

## Owner outcome

Test whether a genuinely fresh model context can learn the manual humanization transformation from aligned AI-before -> Joel-Human-after examples and apply it to a different AI-shaped passage whose actual Joel-Human target is withheld.

This is method research. The Somatic article is already manually humanized and is being used as a positive-control corpus. This experiment does not edit or humanize the article.

## Why this was materially different

Retired methods include incremental next-sentence writing, semantic-persistence controllers, hidden/revealed obligation schemes, prompt anti-pattern accumulation, local register conditioning, paragraph repacking, minimum transformation, and same-context fresh realizations from richer owner cognition. The fidelity/emergence contradiction in incremental generation is considered exhausted rather than newly rediscovered.

This experiment kept the complete held-out source meaning visible to the writer and supplied examples of the desired transformation itself. It asked the model to infer the operation from demonstrations rather than execute another prose-rule checklist.

## Isolation requirement

The held-out writer had to be a genuinely fresh provider conversation/context. Same-context role-play, requests to forget the target, or a writer that had already seen the held-out Human target were invalid.

The actual held-out Human target was not stored in GitHub before generation. Its exact UTF-8 SHA-256 was committed in `SEALED-MANIFEST.json`. The literal target remained local until the fresh writer output was frozen.

## Training material

`WRITER-PACKET.txt` contained three examples selected for distinct transformation behavior:

1. Somatic Experiencing — substantial re-authoring and analogy-led realization;
2. Narrative/Cognitive Integration — expansion from compressed category-list prose into authorial thought;
3. outcomes/evidence paragraph — conversion of generic abstract guidance into concrete author reasoning.

The Hâle first-person blocks were excluded. No unrelated Human donor prose was used.

## Holdout

Held-out source: model-origin Brainspotting passage from the 2026-09-05 working merged Somatic prose.

Held-out target: Joel's manual Human Brainspotting realization in the 2026-09-14 manual-humanized PDF.

Fresh writer output was frozen before target reveal at SHA-256 `c52e3dcf8f4cf559796db375cf4c182b543aa239ffa9c05fb71fe79b576eaefa`.

The Human target was then revealed and its preregistered SHA-256 `f50e30267b306ef4c8d516baa043c1d51981f2f2190bead44c4d69d5c050916f` verified exactly. The literal target is now durable as `HELDOUT-HUMAN-TARGET-H1.txt`.

## Result

The fresh writer output remained strongly reverse-mappable to the AI source's exposition. Pangram 4 was run before Joel's later detector-use correction and returned AI / High confidence / AI fraction 1.0. Retain that measurement as diagnostic evidence, but under the corrected workflow it would not have been necessary because the candidate was already visibly model-shaped enough that the detector result did not change the decision.

More importantly, the Human target was not actually an aligned same-meaning realization of the held-out source. It relied on preceding water-therapy context, added owner judgments/facts not present in the source, and omitted several source obligations that the writer contract told the model to preserve. See `RESULTS-AND-DIAGNOSIS.md`.

Therefore this experiment does **not** cleanly test whether few-shot demonstration learning can reproduce Joel's manual humanization from the information available to the writer. It diagnoses a design error: manual humanization passages that include new owner cognition cannot be treated as pure style/realization targets unless that cognition is included in the source pool.

## Corrected detector-use rule

Per Joel's 2026-09-15 correction, Pangram is not a routine certification step for prose that already looks obviously AI-shaped. Use Pangram when classification is genuinely uncertain or when a controlled measurement can change the next research/editorial decision. The durable owner correction is in `state/PANGRAM-DECISION-VALUE-OWNER-CORRECTION-20260915.md`.

## Next valid experiment requirement

Use either:

1. an **aligned-realization holdout**, where AI source and Human target carry the same substantive/function inventory; or
2. a **full-source-pool re-authoring holdout**, where all owner cognition/context needed for the Human target is actually available to the writer and source selection/omission is explicitly authorized.

Do not use another manually humanized target with hidden added owner thought as though it were a pure style-transfer endpoint.
