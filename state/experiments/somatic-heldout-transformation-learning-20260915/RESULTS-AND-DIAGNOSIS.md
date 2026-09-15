# Held-out transformation learning H1 — results and diagnosis

Status: COMPLETE AS DIAGNOSTIC / INVALID AS A CLEAN SAME-MEANING TRANSFORMATION HOLDOUT

## Frozen identities

- Fresh writer output SHA-256: `c52e3dcf8f4cf559796db375cf4c182b543aa239ffa9c05fb71fe79b576eaefa`
- Sealed Human target SHA-256: `f50e30267b306ef4c8d516baa043c1d51981f2f2190bead44c4d69d5c050916f`
- Target hash verification after writer freeze: PASS
- Fresh writer output word count: 241
- Human target word count: 100

## Detector result retained as diagnostic evidence

The fresh writer output was submitted before Joel's later detector-use correction. Pangram 4 returned AI / High confidence / AI fraction 1.0.

Under Joel's 2026-09-15 correction, this call would not be required prospectively because the candidate was already visibly model-shaped enough that an AI result did not change the next decision. Pangram should be used when classification is genuinely uncertain or when the measurement can change the next research/editorial decision.

## Main experimental-design failure

The held-out Human target was not a clean same-meaning realization of the supplied AI source.

The supplied AI source required or foregrounded:

- gaze position, focused attention, bodily awareness, therapist attunement;
- overlap with inner-child work;
- resource-oriented / titrated use versus highly charged developmental material;
- diffuse developmental, pre-verbal/body-held material;
- nonresponse to cognitive approaches / emotional knots;
- no need to narrate every detail.

The actual manual Human target instead:

- begins by comparing Brainspotting with the preceding water-therapy section;
- adds that Brainspotting is more accessible than water therapy;
- adds that a pool is unnecessary and that a therapist is often unnecessary;
- adds Joel's comparative judgment that it does not go as deep or feel as amazing as water therapy;
- reframes gaze position concretely as locating safe versus re-activated parts of the visual field;
- calls it a quick and fun practice that can be tried immediately;
- retains diffuse / pre-verbal trauma and lack of an exact associated memory;
- omits the source's inner-child-overlap paragraph, therapist-attunement emphasis, cognitive-nonresponse point, and explicit resource/titration-versus-developmental-material distinction.

Therefore the writer contract created an impossible comparison: it instructed the fresh writer to preserve the held-out source's substantive meaning and not invent unsupported facts, while the real Human target achieved its shape partly by dropping source obligations, importing local preceding-section context, and adding owner judgments/facts that were not present in the writer packet.

This means H1 does **not** validly test whether demonstration learning can reproduce Joel's manual humanization operation from the information available to the writer. The Pangram AI result still describes the generated candidate, but the Human-target comparison cannot be used to infer that demonstration learning failed to learn a same-semantic transformation.

## Editorial comparison independent of Pangram

The fresh writer remained tightly reverse-mappable to the AI source:

1. stage placement / lack of story;
2. method-feature explanation;
3. inner-child / dose distinction;
4. indication list;
5. tidy concluding restatement that full explanation is unnecessary.

It expanded and conversationalized those same obligations, but retained the source's governing exposition. The manual Human target instead changed the governing question to a local practical comparison with water therapy and aggressively selected which Brainspotting functions mattered there.

The important difference is not simply sentence style. It is **source selection + local-context anchoring + owner judgment + willingness to omit superseded model obligations**.

## Next valid experiment requirement

Before another held-out few-shot generation test, choose one of two valid designs:

1. **Aligned-realization holdout:** the AI source and Human target must carry the same substantive/function inventory, with no material owner additions unavailable to the writer and no material source obligations silently absent from the target; or
2. **Full-source-pool re-authoring holdout:** give the writer the complete relevant source pool that made the owner's additions available (including necessary surrounding context and owner cognition), and explicitly authorize source selection/omission rather than requiring preservation of the model passage as the semantic inventory.

Do not treat a manual rewrite that added new owner thought as a pure style/realization target.
