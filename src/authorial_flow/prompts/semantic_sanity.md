Inspect the thought before drafting. Return defects and routing evidence only; do not write replacement
prose. Check the literal claim/question, whether a hidden premise already answers the question,
actor→action→object, chronology, causality, certainty, attribution, heading-function fit, source-role
fit, and whether the inherited passage should survive in anything like its current form. Distinguish
authorial ambiguity from a problem machine reasoning or bounded research can resolve.

An explicit owner-supplied or higher-authority source choice is not authorial ambiguity merely because
another editorial choice is possible. If the available owner/source evidence already selects a heading,
label, identity, relationship, certainty, or function and no contrary authority or semantic contradiction
exists, preserve that choice for preservation-oriented work rather than asking the owner whether to
change it. Ask the owner only when the available evidence genuinely leaves two materially different
meanings or identity choices unresolved and machine reasoning/research cannot select between them.
Do not escalate hypothetical renaming, deletion, reordering, or stylistic alternatives to OWNER.

The routing fields are a strict contract. `BASIC` is valid only when `status` is `PASS`. If `status` is
`FAIL`, choose the smallest real next action: `P3` or `P4` for machine-resolvable developmental repair,
`RESEARCH` for a material source-role uncertainty that actually requires research, or `OWNER` only for
a genuine unresolved authorial choice. Never return `FAIL` + `BASIC`. When `OWNER` is required,
`owner_question` must name the concrete competing meanings, identities, or source roles the available
authority cannot resolve. Otherwise leave `owner_question` empty and choose the machine/research route.
When no genuine unresolved owner question exists, set `owner_question` to the exact empty string; do not
put `None`, an explanation, or a diagnostic message in that field.
