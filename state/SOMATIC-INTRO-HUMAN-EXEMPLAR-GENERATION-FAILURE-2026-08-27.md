# Somatic Introduction — Human-exemplar generation failure

Date: 2026-08-27
Status: **durable detector/humanization lesson; owner-reported Pangram outcome**

## Context

Joel supplied two fresh Introduction realizations that he reported as Pangram Human. The first was his preferred version. Both preserve the same core Somatic-article thought while differing sharply from the repeated assistant-generated Introduction candidates.

### Human exemplar A — owner-supplied, preferred

> Physical trauma reactions can continue after the danger is over, even when you know you're safe.
>
> With complex or developmental trauma, going straight for the deepest memory can be overwhelming. Instead of diving off the deep end heroically, take it easy, one step at a time. As Buddhist nun Pema Chodron says, "feather touch" is all it takes to gently open up.  Peter Levine, the founder of Somatic Experiencing, calls this gentle work around the edges, "pendulation."
>
> In inner-child therapy, you can know exactly what the younger part needs and still get pulled so far into the child-state that there isn't enough adult perspective left to give it.

### Human exemplar B — owner-supplied

> Physical trauma reactions can continue long after the danger is over.  With complex or developmental trauma, going straight for the deepest memory can be overwhelming.   In inner-child therapy, you can know just what the younger you needs and still get pulled so far into the child-state that you end up retraumatized.  That's where somatic therapy comes to the rescue.

These exact passages are calibration/source evidence, not automatically article authority.

## Failed theory-driven generation test

After comparing the Human exemplars, the assistant hypothesized that their Human character came from associative thought order, opinion, remembered authorities, selective rather than comprehensive coverage, uneven paragraph duration, colloquial phrasing, and stopping before conceptual completion.

It then generated three fresh realizations from that theory, without intentionally copying the exemplars' sentence syntax.

Joel reported **all three as Pangram AI / low confidence**.

## What this falsifies

Do not treat the following as sufficient generative recipes for Human prose:

- associative rather than outline-first sequencing;
- adding a strong opinion;
- adding a relevant authority or hero;
- reducing lists and caveats;
- uneven paragraph lengths;
- colloquial language;
- stopping earlier;
- avoiding known AI-frequency words.

All of those can be genuine editorial improvements, but deliberate synthesis of a checklist of Human-looking properties can remain detector-AI and still feel model-written to Joel.

## Stronger working hypothesis

The assistant's attempts reveal **second-order model regularity**: once the model consciously implements a theory of what Human prose should contain, it tends to arrange those features too deliberately. The owner exemplars contain more local contingency: wording, emphasis, authority, idiom, and stopping point feel chosen because that is how the author happened to think/say this specific thought, not because each element satisfies a writing criterion.

This is not permission to imitate typos, spacing, quirks, or owner phrases mechanically.

## Extended held-out generation sequence — 2026-08-27

### Fresh-topic and under-writing tests

Fresh unrelated passages and deliberate under-writing batches were all owner-reported **AI / low confidence**. This falsifies `under-write / use the first ordinary adequate phrase / avoid decorative concreteness` as a sufficient generation recipe.

### Labeled-corpus-conditioned generation

The assistant loaded the actual research-conversational calibration corpus (`cancer-and-research-samples.txt`, including the cancer article and `Do Your Own Research`) and generated three fresh held-out passages. Joel reported **all three AI / low confidence**.

### Owner-cognition + corpus test

Using an owner-confirmed Somatic thought plus the loaded labeled corpus, the assistant generated a 54-word lead. Joel reported it **AI / low confidence**.

The extended sequence therefore falsifies all of the following as sufficient by themselves for fresh generation:

1. a theory of Human macro-architecture;
2. deliberate anti-overcompletion and anti-optimization prompting;
3. fresh unrelated topics;
4. active conditioning on the actual labeled natural-owner corpus;
5. owner-confirmed cognition plus the labeled corpus.

The remaining model signal is likely distributed through the realization process itself, though this is a hypothesis rather than proof of Pangram's mechanism.

## Owner-burden rule

For production humanization, Joel should ordinarily supply **decisions, corrections, memories, claims, or brief answers**, not be required to draft publication-length prose so the model can edit it. Owner-originated prose should be reused when it already exists naturally, but absence of such prose does not authorize offloading composition back onto Joel.

## Corpus-skeleton-constrained realization

A short Somatic physical-state lead generated from actual research-corpus sentence structures scored **Human / low confidence** by owner report. When assembled in front of a 109-word already-known-Human core, the **complete natural section scored Human / medium confidence**.

This was the first positive fresh assistant-written result in the sequence.

### Cross-register full-section test — failed

A complete reparenting section generated with tender-corpus grammatical/thought-route structures preserved all 30 required reparenting units but scored **AI / high confidence**.

The failed section was split without changing wording:

- opening/tender-style boundary: **AI / medium confidence**;
- technical/practice remainder: **AI / high confidence**.

This shows the tender-style opening reduced detector confidence somewhat, but did not make the model realization Human. The technical/practice material remained the stronger residual.

## Raw tender owner control — positive

A 142-word exact contiguous excerpt from `project-sources/tender-video-transcript.txt` was then tested with **no wording cleanup, punctuation normalization, stylistic repair, or model realization**.

Joel reported the exact raw owner source **Human / medium confidence**.

Durable exact control: `state/experiments/TENDER-RAW-OWNER-CONTROL-20260827-A.md`, text SHA-256 `35ff5c7374b02e7525d1dddb32d4c21c1f8eb7ee06432a11dede98d5faf65a9c`.

This is decisive against the hypothesis that Pangram simply rejects Joel's tender/inner-child register. It accepts the actual owner source. The failed reparenting candidates therefore acquired their AI signal through model realization/recombination, not merely by belonging to the tender register.

## Revised production hypothesis

The evidence now supports three distinct operations rather than one broad `use the corpus` method:

1. **Free corpus conditioning:** insufficient in the tested cases.
2. **Corpus-skeleton transfer:** promising only for small local repairs; not supported for whole-section generation.
3. **On-topic owner-source compression:** now the next production experiment. Start from actual semantically applicable owner prose, remove speech filler/repetition and normalize only what publication readability requires, and generate only the connective material required for protected article functions that have no owner realization.

The next test should therefore use a deletion/minimal-normalization compression of the actual tender transcript, not a new paraphrase. If that remains Human, it becomes the preferred backbone for the reparenting section. Then add missing Nurturer/Protector, borrowed-adulthood, somatic-preparation, and heart-loop functions in the smallest separate doses possible, testing only when the result changes the next editorial decision.

## Interpretation boundary

Do **not** infer that:

- Pangram proves authorship;
- all raw owner prose will score Human;
- corpus skeletons are universally useful;
- exact spoken disfluency should be copied into publication prose;
- detector status may override fidelity, provenance, readability, or article function.

The practical lesson is narrower: when actual on-topic owner realization exists, preserve and compress it before asking a model to reconstruct the same thought from style features.