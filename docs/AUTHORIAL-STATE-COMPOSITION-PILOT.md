# Authorial-state composition pilot

Status: **experimental; not a promoted humanization rule.**

This is the smallest test of the hypothesis tracked in issue #41: AI-shaped prose may partly originate upstream of wording because the model organizes the thought into a completion-heavy, outline-like representation before realizing it as sentences.

The pilot does **not** claim access to or control over hidden chain-of-thought. It changes only the task-relevant intermediate representation supplied to the generator.

## Why this differs from the normal coherence card

A normal architecture card is intentionally comprehensive: governing movement, paragraph jobs, causality, evidence roles, stopping point, and so on. That is useful for editorial diagnosis, but it may also encourage a generator to pre-complete the intellectual structure before it begins writing.

The authorial-state card is intentionally **incomplete and local**. It represents what is salient *now*, not a complete map of what the finished passage should contain.

Do not turn it into an outline.

## The authorial-state card

Build this from source evidence only. Fragments are preferred. Do not write polished prose.

```text
CURRENT PRESSURE
What is bothering, pulling, confusing, amusing, hurting, or demanding attention right now?

CURRENT BELIEF
What does the author presently think is probably true, in ordinary language?

WHAT DOESN'T FIT
What resists that belief, complicates it, or makes the author hesitate?

WHAT IS SALIENT FROM EXPERIENCE / SOURCE
One or two concrete memories, observations, quotations, facts, mechanisms, or encounters currently in mental reach. Not the full evidence inventory.

SELF-IMPLICATION
Where is the author personally implicated, mistaken, embarrassed, desirous, afraid, hopeful, amused, or changed? Use only sourced material.

UNRESOLVED EDGE
What is genuinely unknown, unsettled, or not yet reconciled?

NEXT LIVE MOVE
What would this mind most naturally notice, ask, remember, test, admit, or say next? This is not a paragraph job or planned conclusion.

STOPPING CUE
What would make the present thought feel complete enough to stop without a recap? Do not pre-write the ending.
```

Fields may be blank. Do not fill them for symmetry. Do not invent missing states.

## Composition instruction

Generate from the card and source material with these constraints:

1. **Stay inside the current thought.** Do not write from the standpoint of already knowing the finished argument.
2. **Do not outline while composing.** Do not ensure that every card field appears in the prose.
3. **Do not preview the conclusion.** Let later claims become available only when the preceding prose earns them.
4. **Preserve local uncertainty.** Do not resolve a contradiction merely because a clean synthesis is available.
5. **Follow salience, not completeness.** Give more space to what actually matters in the source; do not balance categories or examples for symmetry.
6. **Allow associative movement when sourced.** A memory, joke, research finding, or side observation may become the next move if it is genuinely how the thought connects.
7. **Do not add humanizing decoration.** No fake hesitations, typos, slang, personal details, arbitrary fragments, or idiolect tics.
8. **Do not explain a thought after it has landed.** If the stopping cue is reached, stop. No summary paragraph unless the source/function actually requires one.
9. **Preserve the author's real language where it is owner-final, identity-bearing, semantically precise, or naturally superior.** Otherwise compose fresh syntax.
10. **Never silently alter claims, certainty, actors, causality, chronology, attribution, or protected rhetorical function.**

## Minimal A/B test

Use one source passage for which the source/meaning/function ledger is already reliable.

Produce only two candidates initially:

### Control C — comprehensive architecture

Use the current canonical coherence-architecture workflow and compose normally.

### Test D — authorial state

Use the authorial-state card above. Do not give the generator the comprehensive paragraph-job/ending architecture during composition.

Both candidates must use the same:

- source material;
- claim/certainty constraints;
- protected functions;
- factual evidence;
- target length range if one is genuinely required;
- model/version and decoding settings where controllable.

## First-pass scoring — no paid Pangram calls

Before any detector spend, compare C vs D on:

1. semantic/editorial fidelity;
2. blind prose-shape judgment;
3. overcompletion / explanatory-aftercare count;
4. false symmetry / taxonomy count;
5. stopping-point quality;
6. amount of post-generation repair needed;
7. Tier-A idiolect-retention direction, if a valid held-out profile exists;
8. Joel's blind preference if he wants to compare them.

Proceed to Pangram or Tier-B attribution only if D shows a meaningful advantage without fidelity loss.

## What would count as an interesting result

Evidence for the hypothesis would be a repeated pattern in which D, compared with C:

- needs less post-hoc humanization;
- produces fewer recap/aftercare sentences;
- preserves unresolved thought more naturally;
- has less symmetrical or pre-completed architecture;
- is preferred blind by Joel;
- and/or retains more authorship signal.

One passage cannot establish the hypothesis. Treat the first passage as a feasibility test.

## Important failure mode

If the authorial-state card itself becomes a stylized checklist that the model mechanically serializes into prose, it has failed. The card should function as a **temporary working state**, not as nine required content slots.

If that happens, reduce the representation further rather than adding more style instructions.
