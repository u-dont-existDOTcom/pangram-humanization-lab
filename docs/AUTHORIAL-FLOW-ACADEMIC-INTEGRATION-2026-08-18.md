# Authorial Flow: academic integration pass

Status: **research synthesis and experimental design; not a promoted humanization rule.**

Date: 2026-08-18

This note integrates writing-process, discourse, and process-oriented authorship research into the current authorial-state/recurrent-composition work tracked in issue #41. It does **not** claim that the repository can observe hidden cognition or reconstruct private chain-of-thought. The target is observable and task-relevant: how previously externalized text, available source material, revisions, and local rhetorical pressure constrain what becomes sayable next.

## Bottom line

The current recurrent-authorial-flow direction is worth continuing. The literature independently supports its most important premise: writing can be knowledge-constituting rather than merely the transcription of an already completed plan. In Galbraith and Baaijen's dual-process account, one process synthesizes content from the writer's implicit semantic organization while another reflectively manipulates retrieved content to satisfy rhetorical goals. Their work also reports evidence that advance outline planning can suppress the knowledge-constituting component.

The literature also corrects three possible overreaches in our current hypothesis:

1. **Local emergence is not the only legitimate human mode.** Deliberate rhetorical planning is real and useful. The system should distinguish local/constitutive and reflective/rhetorical modes rather than treating all advance planning as model-shaped.
2. **Keystroke events are observations, not cognition labels.** A pause may be planning, rereading, revision, lexical retrieval, or something else. Bursts and revisions are similarly ambiguous. Any process model must keep observed behavior separate from inferred cognitive state.
3. **Writer-specific process signatures are plausible but task-confounded.** Recent work finds substantial within-writer stability across repeated writing tasks, while other work shows that genre, task, and cognitive demand materially change pause, revision, and timing features. A Joel flow profile therefore has to be register/task conditioned and held out by source/task, not learned as one universal average.

## Research strands and what they change

### 1. Knowledge-constituting versus reflective writing

**Galbraith & Baaijen (2018), _The Work of Writing: Raiding the Inarticulate_, Educational Psychologist 53(4), 238–257. DOI: 10.1080/00461520.2018.1505515.**

The proposed dual-process model distinguishes:

- an active **knowledge-constituting** process, in which content is synthesized under constraints representing the writer's implicit understanding; and
- a reflective **knowledge-transforming** process, in which retrieved content is deliberately manipulated to satisfy rhetorical goals.

The practical implication for this project is not "never plan." It is: **do not make a completed rhetorical outline the only state from which generation can occur.** The writer needs a mode in which emerging text changes what is salient next.

**Baaijen & Galbraith (2018), _Discovery Through Writing: Relationships with Writing Processes and Text Quality_, Cognition and Instruction 36(3), 199–223. DOI: 10.1080/07370008.2018.1456431.**

Their experimental account is particularly relevant to the static-card failure in issue #41. A condition that specifies an overall goal without fixing the sequence of ideas leaves room for sentence production to be guided by the writer's implicit organization. This supports our move away from a pre-solved card toward recurrent local composition.

**Project consequence:** keep the current `MORE` mechanism and recurrent accumulation. Add a mode distinction rather than one universal generation policy:

- `CONSTITUTIVE`: no destination or remaining-content inventory visible to WRITER; output-so-far can change what becomes salient next.
- `REFLECTIVE`: a local rhetorical goal is legitimately active and may reorganize material.
- `UNKNOWN`: do not force a cognitive interpretation.

The mode is a task representation, not a claim about hidden cognition.

### 2. Idea generation is dynamic and depends on what preceded it

**van den Bergh & Rijlaarsdam (2007), _The Dynamics of Idea Generation During Writing: An Online Study_, in _Writing and Cognition_.**

Their work uses a more fine-grained account of generating activities and explicitly treats generation as conditional on preceding cognitive activity and position in the writing process. Different kinds of generation occur at different moments and have different relationships with final text quality.

**Project consequence:** a bare edge `A -> B` is not enough. Record both:

- a conventional **discourse relation** describing how B relates to preceding text; and
- a project-specific **generation function** describing what B does to the live thought.

Initial generation-function vocabulary should stay small and revisable:

`CONCRETIZE`, `COMPLICATE`, `TEST`, `QUALIFY`, `COUNTEREXAMPLE`, `REFRAME`, `ANALOGIZE`, `RECALL`, `SELF_IMPLICATE`, `APPLY`, `RESOLVE`, `REOPEN`, `OTHER/UNKNOWN`.

These labels are hypotheses for analysis, not a normative sequence the generator must follow.

### 3. Discourse organization carries authorship information

**Feng & Hirst (2014), _Patterns of local discourse coherence as a feature for authorship attribution_, Literary and Linguistic Computing / Digital Scholarship in the Humanities 29(2), 191–198. DOI: 10.1093/llc/fqt021.**

Cross-sentence entity-grid coherence features alone were often competitive with standard stylometric features on their literary corpus, and the combined representation performed best.

**Ferracane, Wang & Mooney (2017), _Leveraging Discourse Information Effectively for Authorship Attribution_, IJCNLP, 584–593.**

Their discourse-augmented attribution model found non-trivial authorship signal in RST-style discourse information.

These studies do **not** establish that a person's reasoning process can be read from final prose. They do establish that organization above the sentence/surface level can be author-discriminative.

**Project consequence:** LUAR/surface idiolect and authorial flow should remain separate axes, but final-text discourse features can provide an intermediate product-level measurement between them.

For the low-level relation layer, reuse established discourse taxonomy instead of inventing everything. PDTB 3.0 provides four coarse relation classes — `TEMPORAL`, `CONTINGENCY`, `COMPARISON`, `EXPANSION` — with finer senses underneath. We should preserve `UNKNOWN/NO_REL` and avoid forcing every edge into a precise sense.

### 4. Process-oriented idiolect is plausible, but evidence is early

**Litvinova (2020), _Process-Oriented Characteristics of an Idiolect for Authorship Attribution of Heterogeneous Texts: a Pilot Study_, CEUR Workshop Proceedings Vol. 2780.**

This is unusually close to the research question here because it combines linguistic information with typing-process information. The pilot reports that sequential process-oriented markers — including pause-before/after POS classes and revision-event sequences — discriminated authors better than non-sequential production markers after addressing a strong text-type effect.

The study is explicitly a small pilot (three selected authors for the reported attribution experiment) and says the result cannot be generalized.

**Project consequence:** treat "author-specific flow" as a testable hypothesis, not an established fact. The correct next move is to gather repeatable within-author process evidence and compare it against task-matched controls.

### 5. Writers do show behavioral process stability — but not invariance

**Dux Speltz et al. (2026), _Writing traits: examining the consistency of behavioral patterns in writers’ composing processes_, Journal of Writing Research.**

Thirty writers completed three argumentative tasks. Seventeen observed measures yielded four factors: pausing, revising, reading one's own text/lookback, and linearity. Sixteen participants stayed in the same behavioral cluster across all three tasks; overall stability was substantially above chance.

**Conijn, Roeser & van Zaanen (2019), _Understanding the keystroke log: the effect of writing task on keystroke features_, Reading and Writing 32, 2353–2374. DOI: 10.1007/s11145-019-09953-8.**

Several process features changed across copy, email, and academic-summary tasks. Mean interkeystroke timing was comparatively stable, while revision counts, total time, words, and between-word/sentence timing were more task-sensitive.

**Zhang et al. (2025), _Applications and Modeling of Keystroke Logs in Writing Assessments_, Educational Measurement: Issues and Practice 44(2), 5–19. DOI: 10.1111/emip.12668.**

The second of two studies explored stable personal characteristics directly from raw keystroke logs rather than only handcrafted features.

**Project consequence:** any learned profile needs at minimum:

- source/task separation between train and test;
- register metadata;
- repeated sessions;
- task-matched human and AI controls;
- reporting of within-register and cross-register performance separately.

Do not average memoir, research exposition, polemic, casual Q&A, and other registers into one assumed cognitive style unless validation shows that the feature survives the register shift.

### 6. Process observations must be aligned to linguistic units

**Galbraith & Baaijen (2019), _Aligning Keystrokes with Cognitive Processes in Writing_, in _Observing Writing: Insights from Keystroke Logging and Handwriting_. DOI: 10.1163/9789004392526_015.**

Their central warning is the alignment problem: pauses, bursts, and revisions do not have a unique cognitive interpretation. Aggregation can erase the context needed to understand what an observed event means.

**Mahlow, Ulasik & Tuggener (2022; issue 2024), _Extraction of transforming sequences and sentence histories from writing process data_, Reading and Writing 37, 443–482. DOI: 10.1007/s11145-021-10234-6.**

Their open-source approach links raw process data to evolving text versions through `transforming sequences`, `text history`, and `sentence history` rather than reducing the process to global counts.

**Ulasik, Mahlow & Piotrowski (2025), _Sentence-centric modeling of the writing process_, Journal of Writing Research 16(3), 463–498. DOI: 10.17239/jowr-2025.16.03.05.**

This extends the sentence-history approach into a sentence-driven model that preserves the distinction between chronological production and non-linear revision of the text-so-far.

**Project consequence:** if we add natural-writing capture, retain event chronology and sentence/text histories. Do **not** turn a five-second pause into a hard label such as `THOUGHT_OCCURRED`.

## Revised architecture

The project should use three explicitly separate evidence planes.

### Plane A — product / semantic flow

What can be inferred from the text itself:

- semantic move boundaries;
- discourse relation between neighboring or linked moves;
- generation-function annotation;
- source support / claim fidelity;
- unresolved versus resolved edges;
- revisits, reframes, counterexamples, aftercare, and stopping behavior visible in the product.

This plane works on old natural writing and AI candidates even when no process trace exists.

### Plane B — observable composition trace

When a natural writing session is captured:

- chronological insert/delete/replace events;
- cursor displacement / return to earlier text;
- pause durations as raw observations;
- production bursts;
- text-so-far versions;
- sentence histories and transforming sequences;
- optional owner annotation after the fact.

This plane must preserve raw event evidence and uncertainty.

### Plane C — task-relevant authorial-state hypothesis

A bounded experimental representation used to guide or explain generation:

- current live pressure;
- available source fragments;
- unresolved conflict;
- locally active rhetorical goal, if any;
- likely next generation function;
- `CONSTITUTIVE`, `REFLECTIVE`, or `UNKNOWN` mode.

Plane C is **not** hidden chain-of-thought and is never allowed to override source fidelity.

## Changes to issue #41 experiment

The first three pilots already supplied useful negative and positive evidence:

1. Static authorial-state card -> became a compact, pre-solved outline.
2. Sequential local generation with full source visible -> the source inventory itself became a latent outline.
3. Recurrent accumulation with `MORE` -> first positive sign that multiple available ideas can interact before any sentence is emitted.

The next condition should therefore be **Recurrent Source-Gated Live Selection (RSG-LS)**.

### CONTROLLER

CONTROLLER sees:

- the complete authoritative source/claim ledger;
- all source elements already revealed;
- prose-so-far;
- fidelity/protected-function requirements;
- previously rejected or deferred selections.

CONTROLLER does **not** write prose. On each turn it chooses at most one unrevealed source element. Selection is based on what the existing prose makes live now, not source order and not remaining coverage.

Preferred reasons for revealing an element:

- concretizes the current abstraction;
- complicates or falsifies the live belief;
- supplies a needed example/evidence;
- creates a consequential distinction;
- activates a memory or self-implication already licensed by source;
- tests the current claim;
- changes the meaning of what has already been written.

CONTROLLER may return `STOP` if no unrevealed element is presently licensed by the live thought. It must not reveal an element merely because it remains unused.

### WRITER

WRITER sees only:

- prose-so-far; and
- the cumulative set of source elements revealed so far.

It does not see the unrevealed inventory, source order, paragraph plan, target conclusion, or controller rationale.

WRITER returns:

- `MORE` if the available material has not generated an actual thought worth expressing; or
- the natural amount of prose that has become sayable.

It must not paraphrase the newest element merely to discharge it.

### FIDELITY GATE

After each written move, a separate source-aware gate checks claim/certainty/actor/causality/chronology/function fidelity. Flow acceptance cannot excuse unsupported meaning, and fidelity cannot excuse a dead transition.

## Measurements for the next pilot

Do not optimize one scalar score yet. Record a trace and report components separately:

- `reveal_count` and `write_count`;
- `MORE` frequency;
- number of revealed elements accumulated before each emitted move;
- **immediate-discharge flag**: did the writer merely paraphrase the most recently revealed element? (reviewer annotation, not a lexical heuristic);
- controller selection reason / generation function;
- low-level discourse relation of the emitted move;
- source-order adherence versus reordering;
- fidelity-gate result;
- live-edge/flow judgment;
- overcompletion / explanatory-aftercare count;
- stopping quality;
- owner blind preference where sampled;
- LUAR/SVM/idiolect result only as a separate authorship axis;
- Pangram only after non-billable gates justify a paid call.

The important causal test is not whether RSG-LS produces prettier prose. It is whether it repeatedly reduces source-to-sentence serialization and premature completion **without losing source fidelity**.

## Validation path

### Stage 1 — feasibility

Run the existing relationship-spirit source packet through RSG-LS until a terminal stop. Preserve the exact turn trace. Compare it with the static-card and full-source recurrent pilots already recorded in issue #41.

### Stage 2 — repeated product-level test

Use multiple source packets across substantially different registers. Freeze source/claim ledgers before generation. Randomize/blind conditions. Compare:

- current comprehensive architecture;
- static authorial-state card;
- recurrent source-gated live selection;
- ordinary generation plus post-hoc humanization.

A condition must win on flow without losing semantics before detector spend.

### Stage 3 — natural-process capture

Collect opt-in, session-bounded writing traces from the owner across at least three tasks/registers. Capture chronological edits and text versions, not system-wide keystrokes. Build sentence histories/transforming sequences and preserve task metadata.

### Stage 4 — personalized flow validation

Test whether process/product-transition features distinguish held-out owner sessions from task-matched controls and whether the signal survives register shifts. Only then consider a learned `authorial-flow profile` useful enough to condition generation.

## What not to conclude

- A high LUAR score does not establish preserved reasoning logic.
- A discourse relation classifier does not reveal why the author thought of B after A.
- A pause is not a thought label.
- A process signature that identifies a person is not necessarily the part of the process that makes their prose good.
- A flow-preserving model should not mechanically imitate quirks, hesitation, or inefficient revision.
- Human writing can be deliberately planned. The target is not "less structure" but preservation of the author's own route between local states and reflective reorganizations.

## Decision

Continue the current authorial-flow line. Replace the static authorial-state card as the leading experimental condition with recurrent source-gated live selection, while retaining the static card as a control. Add product-level discourse/generation-function traces now; add opt-in natural-process capture as a separate validation layer rather than pretending the current prose-only judges can recover cognition.
