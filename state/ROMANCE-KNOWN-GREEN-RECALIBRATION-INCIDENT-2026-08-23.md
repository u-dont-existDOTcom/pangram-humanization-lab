# Romance known-green recalibration incident — 2026-08-23

Status: **promoted lesson candidate**. Human editorial quality and fidelity still outrank Pangram; this incident narrows how style heuristics may be used against exact detector evidence.

## Exact known-green baseline

Romance r22:
- Markdown SHA-256 `f0f9a47eba2ac9ab1a56bdd6793316d41e7c23072b0b0c030285caf5e12f83c9`;
- Part 1 SHA-256 `5ed333800b9ae7b402f26aa03e751ef8296c7e27ab70e39bc39bb9896b23e62d`: Pangram 4.0 Human `1.0`, AI `0.0`, AI-assisted `0.0`, zero AI windows;
- retained Part 2 SHA-256 `9e4c6a522c95741c7dfc9e040b2dcc40773427cbc0aef8f45211de77208b0c85`: Pangram 4.0 Human `1.0`.

The task handoff explicitly said not to reopen settled/remote passages merely because an older aggregate once highlighted them.

## Failure sequence

During canonical reconciliation, the assistant:

1. treated registered canonical authority as a reason to restore older wording whenever an r22 rewrite lacked direct/explicit owner acceptance;
2. then treated familiar editorial anti-patterns (`balanced explainer`, `paired caveat`, `taxonomy`, `source ladder`, `therapy voice`, `mini-essay`) as if they were a sufficiently reliable classifier of detector-AI prose;
3. drafted six new `holistic humanization` proposals to remove those supposed AI shapes.

## Owner-supplied test of the six proposals

Joel tested the concatenated six proposals in Pangram 4.0. His supplied 6-page report records:
- 2,347 words;
- **59.5% AI Generated**;
- **40.5% Human Written**;
- multiple high-confidence AI runs.

Notable displayed runs include:
- 62-word high-confidence AI block in the rewritten attachment explanation;
- 126-word high-confidence AI block in the rewritten interview/fantasy/ordinary-life explanation;
- 550-word high-confidence AI block spanning rewritten spiritual-practice / `Not A Performance` / early `Two Pillars` material;
- 392-word high-confidence AI block covering essentially the rewritten `After leaving` section.

The six-proposal bundle is therefore rejected as a humanization improvement.

## Lesson 1 — known-green is a calibration anchor

When exact current prose has measured Human on the intended natural boundary, a worker's style theory cannot by itself reclassify that prose as `AI-shaped`.

Editorial heuristics remain useful for finding actual writing problems. But distinguish:

- `this logic/flow/qualification is weak` from
- `Pangram will probably call this AI`.

The second claim needs detector evidence, especially when exact recent evidence already says Human.

## Lesson 2 — heuristics are not a substitute detector

Balanced explanation, paired caveats, mini-essay structure, source ladders, taxonomy/checklist shape, and therapy voice are bounded hypotheses learned from real cases. They are not universal AI signatures.

If a rewrite designed from those heuristics performs materially worse than the known-green source, reject the rewrite and narrow the heuristic rather than treating the detector result as noise by default.

## Lesson 3 — green does not mean editorially perfect

Joel added an important correction: the older/canonical version may still contain a **better editorial feature even if its detector status is AI or unknown**.

Therefore reconciliation should not choose whole versions using a single detector axis.

For older vs known-green prose:

1. keep exact known-green wording as the detector baseline;
2. compare the older realization for better ideas, logic, transitions, examples, jokes, qualifications, evidence framing, or owner-voice features;
3. surface those **feature deficits** in the green realization for owner choice;
4. a valuable feature may be transplanted or freshly realized without reverting the whole old passage;
5. detector safety applies to the resulting wording, not to whether the abstract editorial feature is allowed to be considered useful.

This prevents two opposite errors:
- `old is canonical, therefore old prose is better`;
- `new is Human, therefore the old prose has nothing worth recovering`.

## Production implication

For exact known-green prose, the production preflight question `Would an AI result surprise me?` must be interpreted against the measurement: the current exact text is already a calibration anchor.

A worker may still propose changes for real editorial/fidelity reasons. Once changed, however, the new wording is an unmeasured candidate and the known-green source should remain recoverable as the baseline.

Do not spend production Pangram calls merely to make already-green prose conform to a theory of what Human prose ought to look like.
