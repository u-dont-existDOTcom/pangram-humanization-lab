# Romance Casual short-boundary suffix interaction — 2026-08-23

Status: detector-method evidence / article-specific control. Editorial authority and semantic fidelity outrank Pangram.

## Boundary

Romance section: `Can Casual Sex or a Situationship Actually Be Honest?`

Owner manually tested the same short natural boundary in Pangram 4 GUI.

## Sequence of controls

1. Original boundary: 211 words. Pangram showed about 40% AI, with the first two sentences and the final STI/attachment paragraph highlighted while the middle was Human.
2. Assistant-generated replacement of only the highlighted beginning/end caused the entire boundary to become high-confidence AI. This falsified the assumption that the highlighted spans were straightforward causal rewrite targets.
3. Owner restored the original and deleted only: `Oxytocin, vasopressin, and the rest can start attaching you anyway.` Owner reports this flipped the top to Human and reduced the boundary to about 20% AI. This is the first positive causal lead in the series, but it does not identify whether the cause is named-hormone wording, redundant mechanism-after-thesis structure, sentence topology, or another interaction.
4. From that improved version, owner then deleted the final two sentences: `You can both mean it when you say this is only sex and still have one of you get attached afterward.` and `If you’re both really numb or robotic about sex, maybe not.` The resulting boundary was 168 words; Pangram GUI showed 59% AI with `confidence limited — short text`, and the previously Human middle/pregnancy material became highlighted.

## Interpretation

- The final two sentences were not simple causal AI text despite having been highlighted in the original 211-word result. Their presence was contextually protective/stabilizing for the preceding middle under Pangram's boundary-level classification.
- A highlighted span can therefore be noncausal or even compensatory within a ~200-word natural section, not only in 10k-word half-document segmentation experiments.
- The unchanged middle flipping after suffix deletion is direct evidence of bidirectional/nonlocal boundary interaction. Do not infer prose defect from highlight location alone.
- The oxytocin/vasopressin sentence remains a genuine causal lead because its deletion improved the same boundary while the rest was restored, but more controlled tests are needed before attributing cause to vocabulary or scientific explanation style.
- The 168-word test carries Pangram's own short-text confidence limitation and should be treated as strong interaction evidence, not a stable percentage ranking.

## Next high-information controls

Use the improved baseline: original 211-word boundary minus only the oxytocin/vasopressin sentence, with both final sentences restored.

Then isolate the protective suffix one sentence at a time:
1. delete only the final `If you’re both really numb or robotic about sex, maybe not.` sentence;
2. if needed, restore it and delete only `You can both mean it ... attached afterward.`

Separately, if preserving the named-hormone claim matters, test syntax/topology variants of that single sentence while holding the rest of the improved boundary fixed. Do not rewrite the Human middle.
