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

### Attempt 1

> Physical trauma can keep surfacing after the danger has passed.
>
> With complex or developmental trauma, I don't see anything heroic about going straight for the worst memory if it overwhelms the person. Pema Chodron's “feather touch” is a better rule. Peter Levine calls the gentle back-and-forth near the edge “pendulation.”
>
> In inner-child therapy, you can know what the younger self needs and still get swallowed by the child-state. Once that happens, the adult perspective needed for reparenting is gone.

### Attempt 2

> Complex trauma is easy to make worse by trying too hard. The danger can be over for years while the body still reacts. Don't charge straight into the deepest memory just because it feels brave. Pema Chodron calls for a “feather touch”; Peter Levine's Somatic Experiencing uses “pendulation” around the edges. Inner-child work has the same trap: you can understand the younger self perfectly and still lose the adult perspective once the child-state takes over.

### Attempt 3

> Pema Chodron's “feather touch” is a surprisingly good instruction for trauma work. Complex or developmental trauma does not need a heroic excavation of the worst memory; the body can still be reacting long after the danger is finished. Peter Levine calls the gentle work at the edge “pendulation.”
>
> In inner-child therapy, you can know exactly what the younger self needs and still get pulled into the child-state so completely that the adult perspective disappears.

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

The assistant's three attempts reveal **second-order model regularity**: once the model consciously implements a theory of what Human prose should contain, it tends to arrange those features too deliberately. In this case:

- Pema Chodron and Peter Levine became a matched authority pair rather than memories that happened to arise in the thought;
- the assistant still gave every authority a clean explanatory job;
- claims were still compressed into polished verdict sentences;
- the transitions remained semantically optimized and rhetorically controlled;
- the ending still closed the implication cleanly;
- even when paragraph lengths varied, the conceptual units remained engineered.

The owner exemplars contain something the generated attempts did not reproduce: **local contingency**. Particular wording, emphasis, authority, idiom, and stopping point feel chosen because that is how the author happened to think/say this specific thought, not because each element satisfies a writing criterion.

This is not permission to imitate typos, spacing, quirks, or owner phrases mechanically. It supports a production rule: when natural owner language already exists and is good, reuse it substantially. For stubborn detector sections, source restoration or owner rewriting can be more reliable than asking a model to infer and synthesize a Human style from examples.

## Production consequence

For the Somatic Introduction, do not spend further Pangram calls on theory-driven assistant variants until there is a candidate Joel judges editorially natural enough that an AI result would genuinely surprise him. The two owner-supplied Human examples are the current calibration anchors. If Joel selects or revises one for publication, treat that owner realization as higher authority than assistant reconstruction and preserve its exact thought route unless he requests editing.

## Extended held-out generation sequence — 2026-08-27

The initial theory failure was followed by progressively stronger held-out tests. Joel supplied the Pangram labels manually; these are owner-reported detector outcomes, not API receipts.

### Fresh-start variants after the first failure

Three additional trauma-introduction variants were generated from the stronger `local contingency vs optimization` hypothesis. Joel reported **all three AI / low confidence**. This showed that merely trying to make the realization less symmetrical, less polished, or less complete did not remove the model signal.

### Fresh-topic zero-shot tests

The assistant then generated unrelated short passages about recognition/attention, grounding, and error-finding from fresh AstroHD-derived topics. Joel reported **all three AI / low confidence**.

Joel independently rewrote the grounding passage as:

> People talk about grounding as though it has to be a spiritual practice. Sometimes a foot massage is grounding for me. So is good food or music that relaxes your body. I suspect we make this stuff unnecessarily mystical because “my nervous system likes pleasant physical things” sounds too simple. That's kind of ironic, considering that simplicity is a huge part of grounding.

Joel reported this exact passage as **Human / low confidence**.

He then changed only `relaxes your body` to `makes your body unclench`; the passage flipped back to **AI / low confidence**.

This is a useful complete-boundary minimal pair, but it does **not** establish `unclench` as a banned word. It supports the narrower observation that a model-favored vivid/somatic realization can alter the detector label even when it appears editorially more concrete. The Human wording is plainer and less optimized.

### Deliberate under-writing tests

The assistant next tried to suppress vividness, rhetorical payoff, and coverage-completion. One passage over the detector floor was reported **AI / low confidence**; two others were under 50 words and therefore were not graded.

A corrected batch of three passages, each safely over 50 words and deliberately plain/under-written, was then tested. Joel reported **all three AI / low confidence**.

This falsifies `under-write / use the first ordinary adequate phrase / avoid decorative concreteness` as a sufficient generation recipe.

### Labeled-corpus-conditioned generation

Joel correctly pointed out that the Joel Articles project already contains a labeled natural-owner corpus specifically for voice calibration. The earlier fresh-generation experiments had mostly used rules distilled from that corpus rather than actively loading the relevant labeled prose before generation. This was recorded as a process error.

The assistant then loaded the actual research-conversational calibration corpus (`cancer-and-research-samples.txt`, including the cancer article and `Do Your Own Research`) and generated three fresh held-out passages while conditioning on those natural-owner samples.

Joel reported **all three AI / low confidence**.

This is important negative evidence: loading the labeled owner corpus improved stylistic calibration but did not, by itself, make fresh model-originated prose detector-Human.

### Owner-cognition + corpus test

The next hypothesis was that the remaining signal came from the model inventing not only wording but also the observation, example, emphasis, and conclusion. The test therefore moved to an actual Somatic article thought supplied/confirmed by Joel:

- section thought: sometimes the therapy is not the problem; the body may not be in a state where it can respond well;
- Joel confirmed that this is the intended idea;
- when asked for a concrete example, he said any of sleep deprivation, pain, inflammation, gut/toxin issues, overstimulation, etc. could work and no one example specifically came to mind.

Using that owner-confirmed cognition plus the loaded labeled corpus, the assistant generated this 54-word lead:

> The same therapy can work one day and do almost nothing another day, depending on what else is going on physically. If you're underslept, in pain, inflamed, dissociated, or reacting badly to a medication or substance, you're not in the same state. Sometimes fixing that first matters more than pushing harder on the therapy.

Joel reported it **AI / low confidence**.

## Revised conclusion after extended sequence

The extended sequence now falsifies all of the following as sufficient by themselves for fresh generation:

1. a theory of Human macro-architecture;
2. deliberate anti-overcompletion and anti-optimization prompting;
3. fresh unrelated topics that avoid contamination from prior failed prose;
4. active conditioning on the actual labeled natural-owner corpus;
5. owner-confirmed cognition plus the labeled corpus.

The remaining model signal is therefore likely to be **distributed through the realization process itself**, not reducible to a small list of stylistic properties. Pangram may be responding to interactions among lexical probability, syntax, connective choice, sentence-level semantic packaging, rhythm, and other model-generation regularities. This remains a hypothesis, not proof of detector mechanism.

The observed `relaxes your body` → `makes your body unclench` flip also shows that even one model-favored realization can matter on a short boundary. Do not infer that every model edit contaminates a passage or that Pangram proves authorship; treat this only as exact-boundary evidence.

## Transformation-dose ladder — research use only

A transformation-dose ladder can still answer a detector-research question: how much model editing can a known-Human owner passage tolerate before the boundary changes? If run, begin from owner-originated text of sufficient length, test exact owner text, then D1 mechanical cleanup, then one D2 repair, increasing one controlled step at a time.

**Do not confuse that research design with the production workflow.** Joel explicitly corrected the assistant after it proposed that he draft 60–100 rough words for a section: if Joel has to originate the prose for every difficult passage, he could simply write the article himself. The purpose of the Joel Articles system is for the assistant to perform the writing/editing work using the labeled owner corpus and owner decisions as calibration, not to shift composition labor back onto Joel.

### Owner-burden rule

For production humanization:

- Joel should ordinarily supply **decisions, corrections, memories, claims, or brief answers**, not be required to draft publication-length prose so the model can edit it;
- owner-originated prose should be reused when it already exists naturally, but absence of such prose does not authorize offloading the writing task back to Joel;
- if fresh generation remains detector-AI, change the assistant's generation method or use more constrained corpus-derived realization methods before asking Joel to write the section;
- asking Joel to write a passage is appropriate only when he independently wants to supply wording, when an irreducibly personal memory/voice choice cannot be inferred, or when he explicitly chooses owner drafting as the efficient route.

## Next production-generation strategy

The next materially different assistant-side experiment should be **corpus-skeleton-constrained realization**, not free generation and not owner drafting:

1. retrieve several verified natural-owner sentences/paragraphs that perform the same rhetorical functions as the target passage;
2. preserve their grammatical/syntactic skeletons and connective behavior rather than merely extracting abstract style rules;
3. substitute only the target article's authorized claims/objects, avoiding fake autobiography or copied irrelevant content;
4. recombine minimally and audit for semantic fidelity and accidental phrase transplantation;
5. test the resulting natural boundary.

This is intentionally more constrained than `read corpus, then write in Joel's style`: it reduces the amount of fresh model realization where the previous experiments suggest the detectable signal may be entering. It must still produce coherent article prose and must not become a mechanical catchphrase/template collage.