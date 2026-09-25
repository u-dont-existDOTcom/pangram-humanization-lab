# Current working detector + humanization lessons — Romance continuation, 2026-08-12

Research state only. These are contextual findings and process constraints, not phrase blacklists. Human editorial quality, semantic sanity, fidelity, and source integrity outrank Pangram.

## Blocking execution order

- **Semantic sanity comes before humanization.** Before rewriting, inspect the thought itself: premise, actor/action/object, causality, chronology, certainty, ordinary human dynamics, and whether the supposed contradiction survives contact with reality. Rewriting a bad thought wastes effort and often produces polished nonsense.
- **Touch base with reality before abstract theorizing.** In the love section, repeated abstract attempts missed the ordinary fact that people want to be wanted. A quick lived-reality check would have exposed the missing feedback loop much earlier.
- A contradiction can still be **diagnostically important even if it dissolves under clear reflection**. The initial reaction may reveal a real motive/dynamic; do not confuse “the conflict disappears after thinking” with “the thought experiment is useless.”
- If a cold audit identifies a legitimate weakness, **fix it or explicitly justify why it must stay**. Do not knowingly ship a weakness and call the audit complete.
- Do not be afraid of empirical or strong claims merely because they can be wrong. Good writing sometimes pushes a claim far enough to be falsifiable. The constraint is not “never risk error”; it is **do not invent facts, do not fake certainty, and push the edge without falling off the cliff**. Flag a claim when there is a concrete reason it is materially dubious, not simply because it is empirical.

## Owner prose vs training probes

- In actual Joel article work, **reuse good owner prose freely and substantially only when it is genuinely source-relevant to the exact article claim/function and belongs at that destination independent of Pangram**. Human origin, Pangram-Human status, or stylistic similarity is never insertion authority.
- For training/research that is meant to test model generation ability, first recover the thought and generate a **fresh realization without borrowing Joel’s syntax**. Then compare against owner prose. Copying the human realization can solve the article while teaching almost nothing about generation capability.
- Socratic correction can be valuable when it exposes a systematic blind spot. The durable value comes from extracting afterward: what the model guessed, why it was wrong, what reality check would have caught it, and the correct distinction.

## Human source is not detector filler

Owner correction, 2026-08-29: **do not humanize an article by stitching in unrelated Human prose.** A passage does not become valid production material because Joel wrote it elsewhere, another human wrote it, it is Pangram-green, or it lowers the AI fraction.

Production source recovery must recover the same unsuperseded article claim, memory, quotation, evidence function, instruction, example, or rhetorical job—or an owner-directed cross-article callback that independently belongs at the exact destination. Otherwise the source is calibration/context only.

Consequences:

- Do not build a `Human spine` by collecting green passages from other articles, transcripts, research prose, or unrelated owner material and filling model prose around them.
- Cancer, Romance, community, research, transcript, and other corpus samples may calibrate style or detector behavior; they are not reusable Somatic publication copy unless they independently carry the exact Somatic function being written.
- External studies, official guides, clinical pages, books, and other sources contribute evidence, attribution, and occasional warranted quotations. Their prose style is not a humanization resource and should not be used as a `factual spine` merely because it is human-written.
- Detector improvement caused by adding functionally unrelated Human text is **source contamination, not successful humanization**. Preserve the experiment as evidence and reject the candidate.
- Human→AI minimal-pair research may deliberately start from Human corpus baselines. That experimental use does not authorize importing those baselines into an article.
- Source recovery remains valuable when it retrieves the owner’s natural realization of the **same thought** or restores higher-authority article/source wording for the same protected function. Relevance, provenance, placement, and fidelity are blocking; detector status comes afterward.

The stopped Somatic R17–R58 branch is historical evidence only. In particular, R17 correctly falsified syntax transplantation; R18’s `Human spine` framing is **retired as a production method**; and no later source-recovery result authorizes unrelated Human-text insertion. Any R17–R58 candidate considered again must first pass a source-integrity audit independent of Pangram.

## Do not spend detector work reconfirming untouched human prose

Owner correction, 2026-08-28: in Joel's observed Pangram history, untouched human prose has not been mislabeled AI except in the known technical/academic-paper failure class. Do **not** ask Joel to test, or spend a paid call on, untouched natural owner prose merely to reconfirm that Pangram recognizes it as Human.

The useful production question is whether **model/editorial intervention introduced detector-AI signal**. Therefore:
- treat securely provenanced natural owner prose as the Human source baseline for ordinary/nontechnical Joel-byline work without buying a redundant raw-owner control;
- test the first materially model-touched candidate when the result will change the edit;
- raw-owner detector controls are justified only when the text is in the known technical/academic-paper exception class, provenance/authorship is genuinely uncertain, or there is concrete conflicting detector evidence that cannot be resolved otherwise;
- do not generalize the technical/academic exception to ordinary essays, memoir, relationship writing, spiritual writing, therapy writing, or conversational owner source without evidence;
- a raw-owner control already run may be retained as evidence, but do not turn it into a recurring production gate.

This rule does not mean Pangram proves authorship. It is an empirical workflow rule for Joel's corpus: avoid tests that have no expected information value.

## Pangram findings from this section

- The pronoun instruction `however they fit your life` was detector-sensitive in one opening; `around as you please` and omission did not reproduce the same Pangram regression. Treat this as realization/boundary evidence, not a banned phrase.
- An open-ended conceptual list (`and so forth` or `etc.`) converted one love-definition passage to high-confidence Human where the same closed list did not. This supports list openness/topology as a local variable; the literal words were not causal because both open markers worked.
- Explanatory aftercare can matter: reducing a multi-sentence completion of the selfless-love inference to `It's not about them being yours.` improved Pangram materially in that boundary.
- In the romantic-love passage, a reconstructed Human endpoint reached high-confidence Human. Controlled tests then showed two strong local flips:
  - `Trouble starts when the romantic part is enormous and the selfless part is mostly decorative.` flipped the full passage to AI, while `Trouble starts when there's a lot of romantic love and hardly any selfless love.` stayed Human.
  - `But it is, by its nature, about what I want from one particular person.` flipped AI, while `Romantic love is about...`, `Romantic love is, by its nature, about...`, and `But romantic love is, by its nature, about...` stayed Human.
- Further controls falsified simplistic explanations: sentence packing/splitting was null in the tested ending; abstract category labels alone were not causal; `by its nature` alone was not causal; `Trouble starts` alone was not causal; `mostly decorative` alone was not causal.
- The automated 2×2 Pangram-4 experiment then isolated a **boundary-local matched-clause interaction**. On the fixed Human backbone, A0B0, A0B1, and A1B0 were Human at 0 AI fraction; only A1B1 (`the romantic part is enormous / the selfless part is tiny`) regressed to Mixed at 0.3769716 AI fraction. Exact repeats reproduced all cells. Neither clause was sufficient alone. Do not promote this to a universal phrase rule.
- Broad lexical rules repeatedly fail. Prefer complete-boundary controlled pairs, factor interactions, nulls, counterexamples, and exact repeats. Stop subdividing once the remaining effect is distributed/interactive or the next contrast would be token hunting.
- **Short passages are less reliable detector evidence.** A paragraph can test Human alone yet still be logically defective or contribute to an AI result in a larger boundary. Detector status never rehabilitates bad reasoning.

## Overcompletion vs necessary sequencing — strong local evidence

- Pangram was extremely sensitive to **overcompletion and proper thought sequencing**, but the lesson is not “shorter is better.”
- In the reciprocity passage, two explanatory sentences independently contributed roughly half of the AI regression in owner testing:
  1. `That first answer is useful precisely because it comes before I’ve thought the whole thing through.` — it stepped outside the thought to explain what the preceding reaction was *for*.
  2. `We can both end up waiting for the other person to show desire first while each of us is helping make the other one feel unwanted.` — it diagnosed/repackaged a feedback loop the preceding sentences had already demonstrated.
- Removing both restored **100% high-confidence Human**.
- By contrast, `And it doesn’t stop being true once we’re together.` looked superficially like a generic bridge but **was necessary for clarity**: it performs a real temporal/case transition from initiating reciprocity to maintaining it inside an established relationship. Removing it worsens coherence.
- Therefore the rule is: **do not optimize for less explanation; optimize for the next necessary move in the thought.** A sentence earns its place when it changes the reader’s position (time, case, premise, consequence, or live question). It is suspect when it merely explains why the author just said something, restates an inference the reader has already made, or turns demonstrated dynamics into a neat conceptual diagnosis.
- A thought can be logically complete without every implication being verbalized. Conversely, a Pangram-green truncation can still be intellectually incomplete if a real live question remains. Detector green is never the stopping rule.

## Upstream logic can create downstream “humanization” problems

- When later prose seems to contradict or awkwardly correct an earlier paragraph, inspect the **earlier paragraph’s logic** before rewriting downstream prose.
- In this love section, the sentence `there’s a whole lot of I want you and hardly any I want you to be happy` could imply that **a large amount of eros is itself the problem**. That conflicted with the later discovery that strong expressed erotic desire helps initiate and sustain reciprocity.
- Owner correction: the problem is **not too much `I want you`; it is too little `I want you to be happy` alongside it**. A healthy romance can contain a great deal of both.
- Correcting that upstream framing fixed the larger boundary. An alternative repair was to remove the two following sentences that merely unpacked the already-stated imbalance; they were functionally redundant.
- Do not explain a detector regression as “context,” “complete thought,” “conditional sequencing,” or “article-writer voice” before checking the obvious: **is one paragraph simply saying the wrong thing or talking past its stopping point?**

## Love-section conceptual architecture recovered from owner correction

These are authorial claims/working architecture, not generic psychological doctrine:

- English bundles importantly different things under `love`: selfless/agape/metta/divine love and romantic/erotic `I want you`.
- A good romance **must have both**, in Joel’s current formulation. The problem is eros without enough genuine concern for the other person’s happiness, not strong eros itself.
- The thought experiment “what if she thought she’d be happier with somebody else?” matters even though the apparent conflict can dissolve after reflection. If someone is deeply erotically attached, the initial horror is real and meaningful. Saying “oh well, fine” instantly would not describe deep erotic attachment as Joel means it. It can take effort to move through the horror and assent to the other person’s happiness.
- The horror is part of vulnerability. Romantic attachment exposes part of the self to loss, and that vulnerability can deepen as the relationship deepens.
- **People want to be wanted.** Erotic desire is partly reciprocal and self-reinforcing: showing desire can make the other person feel wanted and increase their desire; feeling wanted can increase one’s own desire. The reverse loop also exists: feeling less wanted can cause withdrawal, which makes the partner feel less wanted, leading to further withdrawal.
- Therefore neither partner can make desire perfectly conditional on already-confirmed reciprocity; if both wait for certainty, nothing gets started. The same feedback dynamic continues after a relationship forms.
- `I want you because I know you'll be happy with me` is an intended strong claim, not an accidental overreach. In Joel’s thought, if I do not think being with me is good for you / can make you happier than the alternative, I do not want the relationship. Ordinary romantic claims such as “I can make you happier than he/she can” illustrate that eros is already entangled with a judgment about mutual good.
- Agape and eros are therefore **intimately entangled**, not two independent forces where agape merely polices eros.
- Agape does at least two jobs inside a healthy romance:
  1. It keeps eros from becoming purely selfish/possessive: the erotic `I want you` includes care about whether being together is actually good for the other person.
  2. It gives eros a **landing pad/base** when reciprocal erotic feedback temporarily fails. If both people pull back because eros seems unreciprocated, genuine care can keep them from simply abandoning each other long enough for eros potentially to rekindle.
- This does **not** mean agape directly grows eros. The intended image is structural: without a base of actual care, eros can freefall. In Joel’s current claim, erotic attachment without genuine care is not real love / is worthless as love.
- Do not flatten this into a tidy `eros = accelerator, agape = brake` model. The point is reciprocal entanglement, vulnerability, mutual good, and stabilization.

## Generation lesson from the love case

- The model repeatedly demonstrated that it can identify anti-patterns after the fact yet still be poor at **writing from lived human dynamics**. The missing moves were often ordinary and obvious once surfaced (`people want to be wanted`) rather than obscure theory.
- Before building an abstract architecture for interpersonal prose, ask: **What would an ordinary person actually feel, do, fear, hope for, or respond to here? What feedback loop exists in real relationships?**
- Let later discoveries revise earlier framing. Do not preserve an upstream sentence merely because it was already Pangram-green if the downstream thought reveals that the earlier sentence was conceptually wrong.
- Do not complete conceptual space merely because it can be completed. But also do not amputate a real unresolved thread just to preserve a Human detector result.

## Architecture can expose previously masked AI-shaped prose

- A detector regression after a structural improvement is **not automatically evidence that the new context falsely contaminated good prose**. First ask whether the new architecture simply made a weak passage easier for the detector—and the editor—to see.
- Romance provided a direct example on 2026-08-26. Two adjacent sections about outside emotional support and not making a partner one's whole world were merged into a stronger single progression. The merge preserved the article's argument but moved a previously Human-scoring ending into a more exposed rhetorical position. Pangram then marked the tail High-confidence AI.
- The first diagnosis incorrectly treated this as a contextual false positive because the tail had previously scored Human. Owner correction was decisive: the earlier boundary had been **hiding genuinely model-shaped prose better**, while the stronger merge exposed it.
- The successful repair kept the stronger merged architecture and rewrote only the exposed tail. It passed after replacing the polished abstraction/completion sequence around `one woman my only portal to beauty, sensuality, inspiration, and softness`, the over-explained alone-time sentence, and the tidy `hidden treasure` close with plainer, more direct prose.
- Durable rule: **do not let prior Human detector status immunize prose from editorial diagnosis after architecture changes.** Prior green evidence proves only that the old exact boundary passed. If the revised architecture is independently better and the newly exposed span also reads model-shaped on a cold editorial pass, keep the better architecture and repair the local defect rather than rolling back the structure to restore the old score.
- Conversely, do not assume every new red window is a genuine exposed defect. Compare both hypotheses: (1) detector boundary/composition sensitivity, and (2) latent prose weakness revealed by better placement. Decide using independent editorial quality, owner judgment, provenance, and controlled rollback/minimum-change evidence—not the window color alone.
<!-- closeout-request:romance-r7-minimum-dose-owner-rollback-20260827 -->

<!-- closeout-request:romance-r7-minimum-dose-owner-rollback-20260827 -->
## Structural approval and wording approval are separate

When Joel approves an assistant-proposed move, consolidation, deletion, compression, or routing change, that approval controls the operation and protected function; it does not automatically lock the assistant sentence realization. A later humanization pass should identify only the surviving assistant-written surface, leave untouched owner prose alone, and prefer restoring actual owner language wherever it can still perform the approved operation. Generate fresh syntax only for relations the approved operation genuinely requires.

Romance R7 is supporting exact-candidate evidence for this production strategy: it changed only surviving assistant realization inside already approved operations, passed bounded preservation/architecture checks with zero unexplained substantive deltas, and Joel reported the exact R7 candidate as 100% Human / high confidence. This owner-reported detector result supports the edit-dose strategy at that boundary; it does not establish phrase-level detector causality.

## Human→AI intervention experiments: model-shapedness is often interactional

The completed 2026-08-28 packet `state/experiments/human-to-ai-minimal-pairs-20260828/` used three genuinely Human Joel baselines and 15 exact, preservation-gated model/editorial candidates. Untouched baselines were not resubmitted. All paid GUI calls used Pangram 4.0, exact UTF-8 History binding, durable pre-click reservations, one headless Brave context per batch, and a reused tab; no completed exact input was repeated.

Durable findings:

- On compact Somatic explanation, paragraph packing, colloquial relationship language, compression without explicit synthesis, and middle-paragraph compression all remained Human. A polished cross-domain transition alone became Mixed at AI `0.3076923192`. Compression + polished abstract cross-domain synthesis became AI `1.0` in two alternate transition realizations.
- On long research-conversational prose, a closed taxonomy and a polished bridge each remained Human alone. Together they became Mixed at AI `0.132098034`. Colloquializing either the bridge or the taxonomy while preserving meaning restored Human.
- On confessional adult/child-trust prose, explanatory completion, sentence equalization, and their combination all remained Human.

Therefore do not blacklist `same principle`, colons, three-item lists, transitions, compression, or any other isolated surface. The operative risk is often **stacked editorial closure**: several locally tidy operations compress, label, connect, and finish a thought in the same boundary. Preserve natural owner source when it is actually source-relevant to the target function, prefer the next necessary concrete move, and test interactions only when single-feature cells are null and the combination is decision-relevant.

R09 supplies the production anchor: its byte-identical R08 paragraph was owner-localized Human/high, while its appended 66-word model/editorial required-functions paragraph was AI/high. Keep R08 frozen; retain the protected functions but redistribute or re-realize them rather than defending the compact package.

## 2026-09-19 — Local saturation is not a global dead end

A difficult target can saturate under one generator/representation family without invalidating the broader humanization program. Inner Child Therapy supplied the direct contrast on consecutive days: `Also Look Outward` converged under a stable-boundary red-region controller from AI 0.53295 -> 0.42430 -> 0.0 and was owner-accepted, while `Write It. Don't Send It Yet.` produced six materially varied all-red realizations under the tested generator family.

Interpret the latter as **local saturation**, not proof that models cannot generate Human prose or that earlier methods stopped working. When no reliable Human island exists, create one through progressive forward construction: generate only the next natural beat, freeze owner/editorially accepted model-generated prefix text, continue from that prefix, then run the complete natural boundary through preservation and Pangram. Once real red/green localization exists, return immediately to the proven residual-repair controller instead of inventing another whole-paragraph architecture after each failure.

Exact method note: `state/generation/LOCAL-SATURATION-NOT-GLOBAL-DEAD-END-20260919.md`.

## 2026-09-21 — Relational generation and post-generation tell repair are different phases

Inner Child checking P3 exposed a representation error: a contemporaneous help map had been turned into a pre-writing sentence allocation (`S1=function A ... S5=function E`), then the resulting prose was criticized for doing exactly one function per sentence. Do not use the help-trace requirement as the generator's sentence plan.

Owner correction: let thoughts interact through source-grounded examples, self-talk, parenthetical realization, and uneven attention; then use the Human-facing tell catalog **after** literal prose exists. The tell ledger must be executed, not merely reported.

Evidence boundary:
- fresh autonomous relational-thought Railway generation passed a human-facing reader but still measured Pangram AI 1.0 on the tested 67-word P3;
- production switched to Joel's source-relevant seat-belt/checker substrate;
- post-generation tell repairs removed deferred-homework implication, checker-monitoring ambiguity, a second-ending slogan, and chronology ambiguity;
- the final owner-derived P3 measured Pangram Human 1.0 alone (86 words), with P1+P2 context (167 words), and in the complete section (318 words).

Therefore the promoted production lesson is **owner-derived substrate + post-generation tell repair can work**. Fresh autonomous transfer remains unproven. Do not expose HT01–HT14 as a writer checklist merely because the repair ledger succeeded.


## 2026-09-21 — Superseded RT2 tell-clean conclusion

The earlier RT2 interpretation said that the current tell catalog was proven incomplete because a supposedly tell-clean 57-word repair still measured Pangram AI 1.0. **That inference is superseded.**

Joel's owner re-audit found obvious surviving AI-shaped operations: scene-skinned source-function staircase, interchangeable didactic props, generic therapeutic abstraction, simulated spontaneity, image -> explanatory aftercare, and equalized semantic efficiency. The premise that RT2 was actually tell-clean was false.

Therefore RT2 does **not** establish that a genuinely tell-clean passage can still be detector-AI, and it does not prove catalog incompleteness. Catalog incompleteness remains possible on other evidence; this control cannot establish it.

Retain the narrower language rule: do not say `there are no AI tells` when the evidence is only `our current ledger/reviewer did not identify any`.

See `state/generation/INNER-CHILD-CHECKING-RT2-RETROSPECTIVE-TELL-LEDGER-20260921.md`.


## 2026-09-21 — A cute scene can hide the same AI staircase

Owner correction to the checking RT2 audit: the supposed `tell-clean` Railway-derived paragraph still contained obvious AI tells.

The failure was mesoscale. Pan -> cooking -> checker -> carrot/dinner looked more Human because it used one coherent scene, self-talk, and fragments, but the scene still walked through the protected functions in order. The semantic staircase had been **skinned with a scenario**, not dissolved.

Additional missed tells included generic therapeutic abstraction, fake-spontaneity markers used as stage transitions, and image -> explanatory aftercare.

Do not treat:
- concrete example;
- self-talk;
- fragments;
- colloquial filler;
- recurrence;

as evidence by themselves. Audit whether they changed the underlying thought topology.

New T4 hypothesis: **causal surplus / non-interchangeable detail**. Joel's seat-belt example accumulates refusal -> crash -> injury -> blame -> guilt. Railway's pan/carrot details mainly illustrate functions and could be swapped out cheaply. Test this on another target before promoting it.

Consequently, RT2 no longer supports the claim that the tell catalog is proven incomplete. The catalog may be incomplete, but this control did not isolate that because the `tell-clean` premise was false.

## 2026-09-22 — Freshness is not critic competence

The Inner Child dangerous-present-adult campaign exposed a process false positive before Pangram: a fresh critic returned `DEFINITE_AI_REMAINS: NO` even though Joel later identified obvious cumulative instruction-manual/listicle cadence and missing reader-purpose structure.

The critic had noticed several ingredients as separate `mixed` findings but did not aggregate them into the known cumulative AI-N16 pattern. Earlier calibration had shown only that the critic could accept a known-good same-register paragraph. That tested specificity, not sensitivity.

Production correction:
- fresh critic packets must include the natural reading boundary plus intended reader/local purpose, not target text alone when audience/continuity can matter;
- critic order is adversarial first: strongest AI-shape case before positive Human-facing features;
- mixed findings must be aggregated at paragraph/section scale;
- protected meaning cannot justify preserving model-shaped realization;
- reader model, why-now, and antecedent checks are blocking;
- before non-detection can gate detector admission, the same materially current critic configuration must blindly accept a same-register known-good control **and** detect a same-register owner-rejected known-bad control.

A bare `no definite AI tells` result is therefore non-gating. This is an audit-admission rule, not a detector-causality claim.

See `state/generation/INNER-CHILD-SAFETY-FRESH-CRITIC-FALSE-PASS-20260922.md` and the canonical Joel Articles `docs/HUMANIZATION-FRESH-CRITIC-GATE.md`.


## 2026-09-22 — SUPERSEDED: Human-surplus hard gate

Benchmark v1 scored **14/20 overall, 10/10 Human, 4/10 AI** and correctly showed that model-simulated concrete detail, judgment, unresolvedness, social address, and metaphor cannot be treated as automatic Human votes.

The first correction overreached by turning content-neutralized scaffold analysis into a veto and requiring Human evidence to materially break that scaffold.

An untouched v2 holdout then scored **10/20 overall, 1/10 Human, 9/10 AI**. The rule had mostly inverted the error direction.

Therefore:
- model-simulated Human-looking devices are not automatic positive evidence;
- a clean/efficient functional skeleton is also not automatic AI evidence;
- genuine Human prose may be compact, instructional, causal, polished, and easy to summarize by sentence function;
- content-neutralization is a diagnostic stress test, not a classifier;
- do not require Human prose to contain inefficiency, digression, or functionally unnecessary surplus.

The oscillation between v1 and v2 crosses the method-escalation threshold. Do not add another abstract prohibition stack. Develop a materially different **literal contrastive** classifier against provenance-secure Human/AI examples, then require a new untouched 20/20 holdout before production gating.

Exact evidence:
- `state/generation/critic-benchmark-20260922/V1-RESULT-AND-RUBRIC-DIAGNOSIS.md`
- `state/generation/critic-holdout-v2-20260922/RESULT-AND-METHOD-DIAGNOSIS.md`


## 2026-09-23 — Stop global prose judges; use specialized defect audits

The dangerous-present-adult process failure triggered a sequence of blinded GPT-5.6/GPT-6 Sol critic experiments. The global-judge family did not generalize:

- abstract authorship rubric v1: 14/20;
- hard content-neutralized scaffold veto v2: 10/20;
- literal contrastive absolute classifier holdout v3: 10/20 after 11/12 development;
- matched pairwise realization-defect chooser: 5/8.

These failures have different error directions and survive materially different prompting architectures. Do not respond by adding more global anti-pattern rules or more few-shot pairs.

The production question is narrower than hidden authorship: **does this literal realization still contain a concrete editorial/model-shape defect that should block a paid Pangram call?**

A specialized-audit decomposition performed materially better on the owner-correction-relevant axes:

- reader-purpose / pragmatic act: 2/2;
- cumulative instruction-manual/listicle cadence: 4/4, including two Human controls showing that lists/advice alone are not the defect;
- antecedent/referent coherence: after correcting malformed controls, 4/4 on the same `ask` sentence with/without its source setup plus self-contained/corrupted Human controls.

Combined current scoped controls: 10/10.

Promoted process lesson:
- use narrow observable defect auditors, one axis per request;
- calibrate each axis on positive and negative examples for that exact defect;
- owner/editorial realization judgment is the relevant label, not hidden model provenance;
- a narrow FAIL identifies a repair candidate; it does not prove AI authorship;
- an auditor that fails its own controls is non-gating;
- absence of narrow FAILs is not a certificate and still requires a direct natural-boundary editorial read;
- Pangram remains downstream and cannot rescue a failed unpaid audit.

For the Inner Child dangerous-adult case, unpaid review should have blocked before Pangram on at least three independently observable defects: instruction-manual cadence, missing reader-purpose/pragmatic setup, and the orphaned `ask` reference after removal of the source's `voice / ask / answer` setup.

Exact evidence: `state/generation/specialized-audit-dev-20260923/SPECIALIZED-AUDIT-RESULT.md`.


## 2026-09-23 — Claude Opus 5.5 improves the one-call global tell ledger, but uncertainty must remain blocking

A direct OpenRouter comparison tested the original production question rather than hidden authorship: give the model the full current tell inventory and require one PRESENT / ABSENT / UNCERTAIN row per tell, with no overall Human/AI vote.

Two independent temperature-0 runs reused the same frozen prompt and six owner-grounded cases.

Across 24 scored tell cells:
- Claude Opus 5.5: **17/24 exact**, **0 wrong-polarity calls**, **7 UNCERTAIN**, with identical status on **11/12** cells between repeats;
- GPT-6 Sol: **13/24 exact**, **9 wrong-polarity calls**, **2 UNCERTAIN**, with identical status on **8/12** cells between repeats.

Opus varied only on one Human cadence control, moving from ABSENT to UNCERTAIN. GPT varied on four cells and repeatedly made confident polarity reversals, including false ABSENTs on owner-known defects and false PRESENTs on Human controls.

Therefore Claude is materially better in this bounded comparison as a **global catalog sweep**, but it is not a sole certifier. Treat UNCERTAIN as unresolved, never as ABSENT. The full tell ledger remains authoritative; use focused/narrow audit or direct editorial review to resolve PRESENT/UNCERTAIN findings. No global Human/AI vote may override individual tell rows.

Current evidence supports Claude Opus 5.5 as the preferred fresh global-sweep model over GPT-6 Sol while the tested model/prompt configuration remains relevant. Opus cost about 3x more in these runs. This is a bounded six-case repeatability result, not universal model-ranking evidence.

Exact evidence:
- `state/generation/global-tell-model-comparison-20260923/RESULT.md`
- `state/generation/global-tell-model-comparison-20260923/REPEATABILITY.md`.


## 2026-09-23 — Max reasoning materially improves the full tell sweep

On the same frozen six-case / 12-cell global tell-ledger benchmark, explicit `reasoning.effort=max` with a 48,000-token completion ceiling materially changed performance without changing the tell definitions:

- Claude Opus 5.5 max: **11/12 exact**, **0 wrong polarity**, 1 UNCERTAIN;
- GPT-6 Sol max via Venice: **8/12 exact**, 3 wrong polarity, 1 UNCERTAIN;
- GPT-6 Astra max via Venice: **7/12 exact**, 4 wrong polarity, 1 UNCERTAIN.

Opus max correctly found every owner-known positive defect in the scored set, including readiness manual cadence, both dangerous-adult defects, and all six RT2 tell cells. Its only miss was a conservative UNCERTAIN on the Human seat-belt cadence control.

This materially weakens the hypothesis that the tell definitions themselves are broadly defective. Preserve the current catalog for now. The original recommendation to prefer max by default is **superseded by the later reasoning-effort ladder**: use xhigh as the current high-rigor default and reserve max for decision-changing unresolved cases. Treat UNCERTAIN as unresolved; broaden positive/negative calibration across the rest of the tell catalog before changing definitions.

Sol and Astra remain useful cheaper/free-credit alternatives, but on this bounded task max reasoning did not make either as safe as Opus: both retained confident wrong-polarity calls.

Exact evidence: `state/generation/global-tell-model-comparison-20260923/MAX-EFFORT-RESULT.md`.


## 2026-09-23 — Jev is useful as cheap tell triage, not as a clearing gate

On the same frozen six-case / twelve owner-grounded tell cells, TypeSafe Jev 1.13 via OpenRouter Decisions scored **9/12 exact** at about **$0.00073 total**.

It correctly handled readiness/manual cadence, dangerous-adult manual cadence, four RT2 tell cells, and all three Human cadence controls. But it made three confident false-ABSENT calls on owner-known defects: dangerous-adult abrupt complication, RT2 scene-skinned staircase, and RT2 equalized semantic efficiency.

Therefore Jev is useful only as an optional cheap typed **positive-triage/advisory** layer:
- Jev PRESENT may prioritize a tell for inspection;
- Jev ABSENT does not clear a tell;
- Jev cannot override Opus max, a calibrated narrow audit, or direct editorial judgment.

Exact evidence: `state/generation/global-tell-model-comparison-20260923/JEV-RESULT.md`.


## 2026-09-23 — Tell calibration coverage is the next bottleneck, not tell-definition rewrite

Current scored evidence is uneven:
- T02 has strong two-sided owner/editorial controls;
- T03–T09 are positive-only;
- T01 and T10–T12 are unscored.

Opus 5.5 max reached 11/12 on the existing grounded cells with zero wrong-polarity calls. That argues against wholesale tell rewrites.

Next method step:
- preserve current definitions;
- add two-sided controls tell-by-tell;
- start with T11, T01, and T10 where owner-correction evidence already points to literal examples;
- split the RT2 T04–T09 cluster into independent controls;
- revise a tell only if repeated max-effort errors remain after good positive/negative controls exist for that exact tell.

Exact evidence: `state/generation/GLOBAL-TELL-CALIBRATION-COVERAGE-20260923.md`.


## 2026-09-23 — OpenRouter Opus xhigh is the API-fallback full-ledger effort; max is escalation

A reasoning-effort ladder reused the exact same six-case / twelve-cell global tell benchmark and unchanged tell definitions.

Primary preserved runs:
- low: **7/12 exact**, 5 UNCERTAIN, 0 wrong polarity, ~$0.155;
- medium: **9/12 exact**, 3 UNCERTAIN, 0 wrong polarity, ~$0.291;
- high: **8/12 exact**, 4 UNCERTAIN, 0 wrong polarity, ~$0.322;
- xhigh run 1: **11/12 exact**, 1 UNCERTAIN, 0 wrong polarity, ~$0.450;
- xhigh run 2: **10/12 exact**, 2 UNCERTAIN, 0 wrong polarity, ~$0.481;
- max: **11/12 exact**, 1 UNCERTAIN, 0 wrong polarity, ~$2.996.

The effort ladder is not perfectly monotonic, but xhigh is the lowest tested effort that repeatedly enters the same fail-safe regime as max while costing roughly one-sixth as much.

Current **OpenRouter API fallback** routing:
- **xhigh** = default high-rigor Opus 5.5 API global tell-ledger sweep;
- **max** = escalation only when xhigh leaves a decision-changing tell UNCERTAIN or editorially disputed;
- lower API efforts are not current clearing defaults because they leave materially more cells unresolved.

This does not establish Claude Code subscription-CLI effort routing. Recalibrate effort separately on the provider-native CLI once its authentication is restored.

Do not rewrite the tell catalog because lower-effort runs were less decisive. The next bottleneck remains two-sided tell calibration coverage.

Exact evidence: `state/generation/global-tell-model-comparison-20260923/OPUS-EFFORT-LADDER-RESULT.md`.


## 2026-09-23 — GPT subscription CLI saves API spend but does not replace Opus for the full tell ledger

The same frozen six-case / twelve-cell tell benchmark was run through clean local Codex subscription CLI sessions at xhigh, with user/project rules ignored, neutral `/tmp` workspaces, ephemeral sessions, read-only sandboxing, structured output, and no tool use.

Results:
- GPT-6 Sol CLI: **9/12 exact**, 1 UNCERTAIN, **2 wrong-polarity** calls;
- GPT-6 Astra CLI: **8/12 exact**, 1 UNCERTAIN, **3 wrong-polarity** calls.

Sol CLI improved somewhat versus Sol max through Venice (8/12, 3 wrong polarity), confirming that provider surface can affect behavior. But both GPT CLI models still confidently flagged known-Human cadence controls as defective; Astra also missed the dangerous-adult abrupt-complication defect.

Therefore:
- provider-native subscription CLI remains the preferred execution route when authenticated/capability-equivalent;
- CLI economy does not imply evaluator adequacy;
- Sol CLI may be a secondary/advisory cross-check;
- Astra CLI currently adds no tell-ledger value over Sol CLI;
- neither GPT CLI model should clear the full tell ledger against stronger owner/editorial/Opus evidence.

Claude Code CLI exists with low/medium/high/xhigh/max controls but was unauthenticated during this test. Its effort ladder must be calibrated separately after re-login; OpenRouter Opus effort results cannot be transferred mechanically to the CLI route.

Exact evidence: `state/generation/global-tell-model-comparison-20260923/CODEX-CLI-XHIGH-RESULT.md`.
