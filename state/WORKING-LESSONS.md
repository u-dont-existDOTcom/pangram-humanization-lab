# Current working detector + humanization lessons — Romance continuation, 2026-08-12

Research state only. These are contextual findings and process constraints, not phrase blacklists. Human editorial quality, semantic sanity, and fidelity outrank Pangram.

## Operational GUI bridge lesson — 2026-08-27

- Keep Chat as the editorial/reasoning authority and automate only fixed-data request → existing local headed GUI runner → durable evidence. Never put autonomous rewriting or request-provided execution inside the desktop daemon.
- A GitHub mailbox is coordination and storage, not the detector transport. The actual measurement remains authenticated headed Playwright/Brave on the owner machine.
- Separate the append-only request branch from the daemon-owned code/result branch. This eliminates the normal two-writer push race without weakening result-branch durability checks.
- Write a global content-addressed paid intent as well as the audit ledger event. Treat either reservation across all audits as ambiguity even if a crash occurred before the GUI runner wrote its own reservation file. Exact, reservation-time-bound, unique History recovery must precede any repeat.
- Accept cache evidence only after strong binding: source coordinates and hashes, exact reader-visible SHA/word count, local GUI transport, Pangram 4.0 success, exact UTF-8 stored-History identity, `response.overall`, and intact report-body/PDF hashes.
- Named reader-visible extraction profiles belong to fixed audited code. Requests may select a trusted name but may never carry selectors, transforms, shell fragments, code, browser settings, or arbitrary runner arguments.
- A user service with `PartOf=graphical-session.target` is the correct lifecycle on a linger-enabled Linux desktop: it inherits the live Wayland/X11, D-Bus, keyring, and SSH-agent environment and stops outside the graphical session.
- Treat browser launch/control-pipe timeouts as retryable pre-submission failures, not terminal request results. Keep the queue cursor behind the immutable request, durably publish the failure, verify browser-child cleanup, and let the same request resume. The live acceptance path recovered this way and then verified the authenticated headed detector without filling or submitting text.

## Blocking execution order

- **Semantic sanity comes before humanization.** Before rewriting, inspect the thought itself: premise, actor/action/object, causality, chronology, certainty, ordinary human dynamics, and whether the supposed contradiction survives contact with reality. Rewriting a bad thought wastes effort and often produces polished nonsense.
- **Touch base with reality before abstract theorizing.** In the love section, repeated abstract attempts missed the ordinary fact that people want to be wanted. A quick lived-reality check would have exposed the missing feedback loop much earlier.
- A contradiction can still be **diagnostically important even if it dissolves under clear reflection**. The initial reaction may reveal a real motive/dynamic; do not confuse “the conflict disappears after thinking” with “the thought experiment is useless.”
- If a cold audit identifies a legitimate weakness, **fix it or explicitly justify why it must stay**. Do not knowingly ship a weakness and call the audit complete.
- Do not be afraid of empirical or strong claims merely because they can be wrong. Good writing sometimes pushes a claim far enough to be falsifiable. The constraint is not “never risk error”; it is **do not invent facts, do not fake certainty, and push the edge without falling off the cliff**. Flag a claim when there is a concrete reason it is materially dubious, not simply because it is empirical.

## Owner prose vs training probes

- In actual Joel article work, **reuse good owner prose freely and substantially**. It need not be reused only when it is strictly “better”; good natural owner language is part of the authoritative source pool.
- For training/research that is meant to test model generation ability, first recover the thought and generate a **fresh realization without borrowing Joel’s syntax**. Then compare against owner prose. Copying the human realization can solve the article while teaching almost nothing about generation capability.
- Socratic correction can be valuable when it exposes a systematic blind spot. The durable value comes from extracting afterward: what the model guessed, why it was wrong, what reality check would have caught it, and the correct distinction.

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
