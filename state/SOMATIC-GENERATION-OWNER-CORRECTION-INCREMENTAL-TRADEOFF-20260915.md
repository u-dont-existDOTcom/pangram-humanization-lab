# Somatic generation research — owner correction on incremental generation

Date: 2026-09-15
Status: **ACTIVE RESEARCH CORRECTION / DO NOT REINTRODUCE AS NOVEL METHOD**

Joel corrected a recurring research drift: the project has already tried many variants of `generate only the next locally live thought`, isolated-sentence writing, semantic-persistence writing, and controller-mediated incremental generation. Do not present that family again as a newly discovered solution.

## The fundamental tradeoff

A genuinely incremental writer that does not know the future semantic commitments can preserve local emergence, but it can also wander away from what Joel is trying to say.

A controller that preserves fidelity by keeping the full target meaning and revealing obligations as needed reintroduces the same future-target pressure that the incremental scheme was meant to remove. Even if the writer sees only a subset at one moment, the controller's routing decisions encode the destination and can recreate checklist-shaped or editorially inevitable prose.

Therefore the unresolved problem is **not** `how to hide future obligations better`.

Do not propose another variant of:

- one-sentence-at-a-time continuation;
- hidden future obligation release;
- semantic-persistence controller;
- fresh-writer/local-thought sequencing;
- role-separated controller/writer where the controller owns the full target;

unless a materially new mechanism directly addresses the fidelity/emergence tradeoff rather than renaming it.

## Correct research goal

The Somatic article is already manually humanized and is a positive-control corpus. The owner outcome is to learn a method by which a model can transform or generate faithful prose that is Human-shaped **without requiring Joel to manually rewrite it**.

The article itself is not an unfinished humanization target in this lane.

## Next-method requirement

The next experiment must allow the model to know the complete intended meaning while changing the generation mechanism in some other structural way. Candidate directions may include empirically learned whole-passage transformation from aligned AI→owner-humanized examples, held-out evaluation, a genuinely different model/generator, or another architecture that does not depend on pretending the future target is absent.

Do not add more anti-pattern rules merely because a whole-passage model draft fails Pangram. Compare a structurally different generation mechanism.
