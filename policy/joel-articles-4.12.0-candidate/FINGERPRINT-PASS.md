# Fingerprint Pass — Adversarial Voice, Meaning, and AI-Shape Audit

## Limits

This audit identifies mismatch, genericity, excessive structural density, evidence weakness, and unsupported persona. It cannot prove authorship and is not a quality score. Prefer an independent model; a same-model audit must state lower confidence. Report only unless Joel requests repair.

StoryScope-derived patterns are a qualitative lens. The study examined model-generated fiction, not this genre, Joel's complete style, or edited human–AI collaboration.

## -1. Cold organization check before provenance or detector evidence

Before considering topic, truth, provenance, or detector output, inspect the passage's information organization sentence by sentence.

For each sentence ask: **What would an actually interested reader want to know next?** If the next sentence repeatedly supplies a different, outline-determined function, flag model/content-writer organization. Also inspect whether every sentence strongly predicts the role of the next; whether categories are exhaustively completed; whether each source/example gets one neat contribution; whether multiple sentences perform the same interpretive function; and whether the passage continues after curiosity has ended.

Keep two axes separate:

1. **author-specific semantic density** — real names, dialogue, history, self-implication, odd judgments, memories, and lived/source-specific material;
2. **realization/organizational predictability** — how much the prose packages that material into a generic explanatory sequence.

A Pangram-green region may contain a lot of Joel's actual thought while still being model-realized. Do not promote it to a natural-human gold standard without independent owner judgment.

## 0. Identify the genre before judging explicitness

Name the article's form and what it legitimately requires:

- polemic/manifesto: visible thesis and strong contrast;
- practical guide: sequencing, lists, frameworks, and repetition for navigation;
- research article: qualifications, definitions, and source-heavy structure;
- personal essay: greater implication, association, and unresolved meaning;
- hybrid: section-by-section calibration.

Flag explicitness only when its density exceeds the genre's function.

## 0A. Short-excerpt anti-halo audit

When Joel asks whether a short excerpt sounds human, AI, or mixed, evaluate wording and architecture cold before topic, factual accuracy, provenance, detector output, agreement with Joel, or the quality of its epistemic distinctions.

Give three independent judgments:

1. **Prose shape:** human-shaped / AI-shaped / mixed.
2. **Thought provenance:** Joel-specific / generic / unknown.
3. **Fidelity and editorial quality:** strong / mixed / weak.

Only prose shape controls the human/AI/mixed verdict. Give that verdict first.

Run content-neutralization: replace names, technical terms, doctrines, and facts with placeholders. Ask whether the remaining architecture is portable across unrelated topics. Do not count accuracy, caution, calibrated uncertainty, evidentiary restraint, doctrinal specificity, fairness, or first-person grammar as evidence of human voice.

For short analytical prose, inspect clusters: completed abstract inference; nested hedging; immediate prophylactic caveat; comprehensive closure of possible overreadings; first-person epistemic framing without visible reasoning; symmetrical claim–limitation architecture. “I take this as evidence” is not visible reasoning by itself. Look for encounter, friction, revision, observation, failed expectation, or live uncertainty.

Do not use pseudo-precise percentages for very short excerpts unless Joel requests them. Use the controlled minimal-pair ledger in `EDIT-CONTRACT-AND-LEDGERS.md` for exact detector records.

## 0B. Controlled minimal pair MP-001 — unnecessary precision upgrade

Retain this as a full-boundary detector-learning case, not a universal token rule.

| Field | Record |
|---|---|
| Boundary | Complete passage of approximately 300 words |
| Variant A | `asked just the right question` |
| Variant B | `asked exactly the right question` |
| Other visible changes | None reported |
| Detector | GPTZero; preserve exact model/version/date with the original test record |
| Result | Variant A: strong-confidence human; Variant B: strong-confidence AI |
| Editorial distinction | Conversationally sufficient modifier versus explicit analytical precision |
| Interpretation | `just` reports what caught Joel's attention with ordinary looseness; `exactly` retrospectively labels the decisive question and closes the interpretation more completely |
| Generalization status | High-value candidate pattern; never `just = human` or `exactly = AI` |
| Replication target | Other unnecessary precision upgrades in complete passages |

The broader category is natural under-specification that accurately reflects how the thought occurred versus model-style over-explication of the relationship between ideas. Log exact boundaries, delta, detector metadata, repeated runs, owner preference, blind quality ranking, counterexamples, and holdout status in `EDIT-CONTRACT-AND-LEDGERS.md`.

## 0C. Controlled micro-case MP-002 — contraction and caveat realization

Retain the complete near-death-comparison paragraph as one under-100-word boundary. In the reported GPTZero 4.8b tests on 2026-08-06, only the caveat sentence changed:

| Variant | GPTZero result |
|---|---:|
| `They aren't proof of my experience` | 5% AI; high-confidence human |
| `They are not proof of my experience` | 20% AI; moderately human |
| `They don't prove what happened to me` | 27% AI; moderately human |
| `They do not prove what happened to me` | 49% AI |

The interface warned that the passage was under 100 words, and the screenshots document one visible run per variant rather than repeated-run stability. Treat the numbers as local evidence.

Two effects appear to interact. Expanding the contraction raised the AI score inside both constructions. Separately, the fully articulated verbal disclaimer (`prove what happened to me`) scored more AI-like than the shorter nominal caveat (`proof of my experience`). This supports a broader watch for formal grammatical completion plus comprehensive inference management; it does not support `contractions = human`, `do not = AI`, or a ban on explicit caveats. The nominal form may also shift the proposition slightly, so fidelity must be judged before detector benefit.

## 0D. Controlled micro-case MP-003 — flat coordination × apparent semantic class

Use the complete passage beginning `The main question for me and for the Buddha...` as the boundary. The owner reported these results across GPTZero and Pangram:

- `automatic action, skilled performance, play, and split-brain patients` — high-confidence human on both detectors;
- removing `play`, leaving `automatic action, skilled performance, and split-brain patients` — Pangram about 80% AI and a substantial GPTZero regression;
- `automatic action, play, and split-brain patients` — human;
- `skilled performance, play, and split-brain patients` — human;
- `automatic action, skilled performance, dreaming, and split-brain patients` — human;
- `automatic action, dreaming, and split-brain patients` — 100% human in the reported test;
- keeping the same three scientific phrases but replacing the flat list with relation-aware syntax (`automatic action and skilled performance, along with research on split-brain patients`) — human.

This falsifies a simple `three-item lists are AI` rule. The local signal is the interaction between canonical flat coordination and items that appear to form one neat conceptual class. Cardinality, technical vocabulary, and any single phrase are insufficient explanations. Record list cardinality, exact items, apparent class/homogeneity, order, and coordination topology as separate variables.

Editorial repair should express the real relations among the existing items. Never add an irrelevant outlier, remove true evidence, or distort the research history merely to break a detector pattern. Phrase and construction lists are statistical watchlists, not authorship dictionaries; ordinary human phrases can become detector-sensitive because models overproduce them.

## 1. Provenance, fact assignment, and current-voice fit

Classify each section:

- **A — Joel-specific:** supplied names, memories, objects, mechanisms, jokes, positions, or judgments that depend on his actual material.
- **B — current-voice compatible but generic:** follows the profile but could be generated from the thesis alone.
- **C — unsupported persona:** invented first-person experience, belief, feeling, relationship, motive, certainty, realization, or scene.
- **D — corpus mimicry:** imports wording, affectionate address, architecture, research-catalog density, or tics without being called for.
- **E — legacy regression:** claim stacking, speculative certainty, caps/exclamation intensity, or superseded habits.
- **F — evidence failure:** unsupported, overstated, stale, mis-cited, or category-confused claim.

Any C is critical. D, E, and F severity depends on scope and consequence.

Also record section origin: owner-authored untouched; owner-edited final; assistant-produced owner-accepted; owner-final available only in scan/PDF; or superseded assistant candidate. Detector score and owner acceptance do not establish authorship. Assistant-produced accepted sections require a later full-context recheck.

## 2. Register audit

Map intended and actual register:

- heavy/irreverent;
- direct/tender;
- research-conversational;
- practical guide;
- neutral connective prose.

Flag false tenderness, academic stiffness, bureaucratic harm reduction, humor by quota, quote-card humor, expanded non-contracted assistant prose in conversational sections, or maximum intensity everywhere.

## 3. Structural-density audit

Judge concentration, not isolated devices. Locate:

- thesis-return frequency: how often an example is immediately recruited to prove the thesis;
- interpretive aftercare after anecdotes, images, quotations, jokes, or absurd events;
- polished paragraph endings in succession;
- repeated epigrams, antitheses, reversals, or social-media-ready lines;
- mirrored “X does this; Y does that” architecture beyond the article's real central contrast;
- uniform section lengths, emotional temperature, and ending force;
- nearly all headings behaving as slogans rather than a mix of imaginative and navigational headings;
- frameworks presented as complete, non-overlapping, or able to absorb every exception;
- all complications being converted into proof of the model;
- a conclusion restating meaning the article already earned;
- appendix/preface orientation following why detail moved → permission to skip → invitation to continue → contents summary;
- research-summary architecture assigning one sealed academic function to each paragraph while closing every loop.

Ask whether 5–15% of interpretation could be removed without losing the argument.

## 4. Framework permeability and unresolved problems

For every major model, check:

- where categories overlap, leak, or become one another;
- whether exceptions and failure modes are visible;
- whether the model is presented as a diagnostic aid rather than reality's natural compartments;
- whether at least one important unresolved danger is named when one genuinely exists;
- whether proposed safeguards are admitted to be incomplete where appropriate;
- where power, status, exclusion, or harm could still accumulate.

Do not demand fake uncertainty. One real unknown is more valuable than generic caveats.

## 5. Repetition and canonical sweep

- Apply the canonical banned list and twice-within-three-paragraph redundancy rule.
- Count distinctive words, metaphors, images, sentence forms, connectors, rhetorical questions, and paragraph-ending devices appearing three or more times.
- Distinguish intentional refrain from accidental duplication.
- Check whether a reviewer concern is restated in several framings rather than once with locations.

## 6. Architecture, causality, and closure

Check for:

- default hook → anecdote → thesis → list → objection → uplift;
- sample architecture copied into unrelated material;
- cosmetic revision that preserves an identified AI-shaped skeleton;
- insight, healing, or choice replacing institutions, power, biology, relationships, history, chance, or other people;
- doom-presupposing agreements or prophetic endings;
- manufactured redemption, consensus, or uplift;
- excessive symmetry or perfectly completed causal chains;
- a cautionary aside that closes an unexplained anomaly with “luck,” coincidence, pathology, or another culturally conventional answer the evidence did not establish.

## 7. Specificity and humor integrity

Check whether details are true, relevant, and discovered in the material rather than installed to simulate personality. Humor should arise from concrete absurdity, self-implication, unexpected specificity, or the plain ridiculousness of events.

Flag portable jokes, repeated punchline forms, humor that substitutes for mechanism, and jokes that interrupt serious safety material rather than clarify or relieve pressure.

## 8. Tender-register integrity

Flag clinical scripts, purple grief, unsupported bodily symbolism, affectionate nicknames used as branding, raw transcript filler, solemnity that suppresses natural humor, softness that erases protective firmness, or jokes that displace danger.

## 9. Meaning-preservation audit

For rewrites, reconcile:

- every entity, place, and time with the fact-and-meaning ledger;
- every first-person thought, feeling, realization, and motive with provenance;
- every actor/action/object relation in specialized frameworks;
- every certainty marker;
- every comparison and pronoun after reordering;
- every exact memory, lyric, catchphrase, and coined term;
- every politically or historically specific detail whose causal history, moral tension, or explanation of the next action would be lost if it were genericized;
- every substantive addition, deletion, reassignment, causal change, or certainty change with edit permission.

## 9A. Rhetorical function, context, and orphan audit

For every substantial cut or reorder, check whether the surviving passage still has:

- the same rhetorical job;
- the definition, setup, antecedent, contrast, or evidence it requires;
- the media/link/caption it introduces or explains;
- a destination that preserves rather than repurposes its meaning.

Count orphaned definitions, introductions, examples, transitions, takeaways, and media anchors. Audit `otherwise`, `also`, `still`, `other`, `same`, `too`, `yet`, and `but` around inserted material.

## 9B. Mixed truth, scope, and recurrence

Check whether:

- adding a moral complication preserved genuine praise;
- a local observation was inflated to a broader geography or population;
- communal warmth was allowed to coexist with exclusion, conformity, or violence;
- each repeated issue performs a different function;
- controversial values are framed as compatibility/membership architecture when they actually govern shared life;
- Joel's corrections changed the underlying judgment throughout the draft rather than only one sentence.


## 9C. Review-comment, audience, and plain-language integrity

When the draft follows an annotated review, check whether:

- the complete comment chronology was reconciled;
- later retractions, clarifications, and `never mind` instructions superseded earlier comments;
- comments were interpreted as judgments rather than mechanical replacements;
- Keep locks survived later passes;
- Remove decisions received dependency and orphan repair;
- Brainstorm states were not treated as approval;
- moved or consolidated material is shown with its destination rather than falsely presented as deleted;
- structural removals account for every unique function;
- the project-level audience contract remains stable;
- any section-level audience shift is deliberate, signaled, and functionally necessary;
- role drift occurred toward clinician, lawyer, manager, investor, policymaker, reviewer, insider, or another unintended role;
- expertise drift replaced accessible explanation with specialist shorthand;
- goal drift changed a guide, essay, report, or argument into another genre without approval;
- relationship drift changed peer/witness/author contact into lecturer, therapist, institutional, or marketing voice;
- scope or action drift changed who the article serves or what it helps them do;
- register, assumed-knowledge, stakes, or venue drift made the prose sound like a journal article, legal memo, corporate deck, grant application, sales page, or internal document;
- source vocabulary and priorities were imported without translation from the source's audience;
- clearer original language was replaced by unnecessary domain jargon;
- unexplained technical, foreign, legal, academic, clinical, corporate, or insider terms appear before the reader needs them;
- native editor overlay text appears as prose;
- both original-vs-current and previous-delivery-vs-corrected baselines exist when required;
- when a multi-file family was the requested delivery, it was packaged as one ZIP; a continuation handover was included only when an actual worker transfer was requested or planned.

Treat any prestige shorthand or disciplinary abstraction as a watch item, not an automatic ban. Ask what concrete thing it names, whether it improves precision for the intended reader, and whether the source's audience has silently replaced the article's.

## 10. Research and evidence integrity

Check for corpus claims treated as facts, missing in-article links, vague attribution, abstract-only study descriptions, invented first-person source reactions, full sources patched into obsolete abstract-based candidates, mechanism or anecdote presented as effect, exercise rationale presented as evidence, association presented as causation, outcome collapse, stale/retracted evidence, recommendation strength exceeding evidence, and claim density too high for the distinctions provided. Also check for evidence streams called independent when one was retrofitted to another; sources forced into one advocacy role despite supplying a countermodel; source breadth inflated into a larger thesis; established theory mislabeled as private interpretation or credited with the complete synthesis; aggregate evidence treated as an automatic case decision; author-developed syntheses presented as validated complete systems; explanatory levels blended; warnings broader than support; scope modifiers dropped; flexibility framed as no standards; prerequisites becoming permanent avoidance; abstract practical language without actors/actions/thresholds; generic research-summary architecture; and a practical guide converted into an uneven literature-review appendix. Health-specific applications remain governed by `FACTS-HEALTH-FORMATTING.md`.

## 11. Idiolect, visuals, and delivery

- Is each catchphrase approved, exact, contextually earned, and suitable for written rather than only spoken use?
- Does each image prove, clarify, pace, humanize, or aid scanning?
- Are generated images clearly illustrative rather than documentary?
- Are raw media islands byte-identical when required?
- Was each native object inventoried by semantic type, exact source identity, order, anchors, rhetorical function, approved destination, transfer treatment, and destination result?
- Was the original raw editor body used as the sole authority rather than TXT, PDF, screenshots, rendered HTML, a prior helper, counts, or hashes?
- Were archival source fidelity, transfer conversion, and destination result reported separately?
- Did the transfer payload use `div[dir=auto].body.markup`, remove only known editor locks, and avoid whole-document parse/reserialization?
- Were rendered Substack comment cards replaced by canonical URLs in the same source positions inside the complete payload rather than copied as rendered child HTML or automatically split into extra steps?
- Were images, digest previews, YouTube/video, Share, Subscribe, comments, and paywalls checked independently?
- Did paywall instructions appear only when a genuine raw-source marker exists?
- Was the actual downloaded-file-in-Opera-to-Substack path tested or explicitly left unverified?
- For substantial revisions, were complete final HTML and the implemented interactive side-by-side review produced? After a repair, were both original-vs-current and previous-delivery-vs-corrected baselines generated? Was any quick static diff clearly secondary rather than substituted for the interactive artifact?
- Were HTML/web deliverables kept as downloadable/code-view files rather than auto-rendered or opened?
- When several related review files were delivered, were they packaged in one current ZIP with an authoritative-file statement? If an actual worker transfer was requested or planned, was the least burdensome sufficient handoff included?

## 11A. Linked-reference, explanation, and terminology audit

Count and inspect:

- new explanations adjoining links;
- canon facts imported into article prose;
- linked references expanded beyond the source;
- peripheral terms receiving full definitions;
- model-written explanations not explicitly approved;
- useful approved explanations that should remain locked;
- source terms silently renamed;
- imported terms conflicting with Joel's established framework;
- adopted replacement terms introduced without a bridge;
- source attribution lost after terminology normalization;
- common developmental ideas over-attributed to a reviewer or lecturer merely because they supplied the explanation.

Distinguish redundant background, necessary local orientation, a useful substantive addition requiring approval, and an approved addition now locked. Do not mechanically delete all new explanation.

## 11B. Derivative compatibility and transfer-conversion audit

Check that the regenerated derivative was compared with the last confirmed derivative; every locked compatibility invariant remains; the payload was rebuilt from the exact final archival editor body; the confirmed one-paste wrapper and immediate ClipboardItem plus silent contenteditable fallback remain; no asynchronous pre-clipboard work was introduced; only known editor locks were removed; comments remain canonical URLs at the same source positions; rich object types retain complete metadata; visible control count, labels, and order are unchanged unless authorized; paywall instructions are source-triggered; the real browser/file-opening path was tested or explicitly left pending; source-hash equality was not treated as runtime proof; and every deliberate compatibility change has a recorded reason and destination result.

## Output

### Verdict

For a short human/AI/mixed request, state the cold prose-shape verdict first, then thought provenance, then fidelity/editorial quality. Do not let Joel-specific content or strong reasoning halo the prose-shape judgment.

For a full draft, state the strongest evidence that the draft is genuinely current-Joel-specific, then the strongest evidence that it is generic, imitative, over-determined, or evidentially weak.

### Highest-risk findings

| Location | Class | Severity | Finding | Why it conflicts with voice, meaning, genre, or evidence | Fix direction |
|---|---|---:|---|---|---|

Use `critical`, `high`, `medium`, or `low`.

### Counts

- Approximate A/B/C/D/E/F ratio
- Thesis echoes
- Examples followed by unnecessary interpretation
- Polished paragraph endings / total paragraphs
- Consecutive epigram or quote-card runs
- Repeated mirrored/binary constructions
- Flat semantically homogeneous coordinate lists / relation-aware list rewrites
- Formal expanded negations where natural contractions fit
- Fully specified evidentiary disclaimers versus idiomatic local caveats
- Slogan headings / total headings
- Distinctive constructions appearing 3+ times
- Unnatural expanded forms where contractions fit
- Unsupported or weak claims
- Missing in-article links
- Orphaned definitions/examples/transitions/media anchors
- Transition-word logic failures
- Scope inflations
- Function-duplicate recurrences
- Praise-erasing reversals
- Link echoes / unnecessary linked-reference expansions
- Unapproved canon-fact or model-written explanations
- Terminology bridges missing, attribution lost, or common ideas over-attributed
- Heading-hierarchy or table-of-contents nesting failures
- Native-object placement/anchor mismatches
- False-positive or missing paywall steps
- Derivative compatibility or transfer-conversion regressions
- Audience drift by type: role / expertise / goal / relationship / scope / action / register / assumed knowledge / stakes / venue
- Unsignaled section-level audience shifts
- Source-audience register imported without translation
- Unexplained technical, foreign, legal, academic, clinical, corporate, or insider terms
- Clear original wording replaced by unnecessary domain jargon
- Distinct explanatory systems or levels blended without support
- Review comments applied mechanically
- Unreconciled later retractions or superseded decisions
- Moved/consolidated passages falsely shown as deleted
- Native-editor overlay text treated as prose
- Missing previous-delivery-vs-corrected baseline
- Missing required multi-file delivery ZIP or requested/planned continuation handoff
- Unresolved anomaly converted into luck/coincidence/pathology without discriminating evidence
- Contentious specific detail genericized or deleted while its narrative function remained necessary

### Framework and unknowns

For each major framework, state permeability, exceptions, failure modes, and any important unresolved problem.

### Register map

List intended and actual register by section.

### Preserve

Name the lines, details, jokes, evidence distinctions, images, and passages that must survive repair.

### Confidence

State independent-model or same-model audit and the main uncertainty.

### Voice check for Joel

List only exact passages whose authenticity remains genuinely uncertain. Explain each uncertainty briefly and ask Joel to inspect those locations. If none remain, state `No specific voice uncertainty to review.`

### Revision status, when repair was requested

State current quality, strongest improvement, largest remaining weakness, best next pass, expected marginal benefit, over-editing risk, and substantive claim changes or `none`.

## 12. Artifact-family and platform-delivery audit

- Did the review artifact preserve comments, selected-text notes, Keep/Remove/Brainstorm, reasoning, Humor/Technical depth/Length/Bluntness controls, local persistence, search, changed-only filtering, and JSON/Markdown exports?
- Was `interactive_review.py` used, self-tested, and browser interaction-tested rather than merely described in a Markdown specification?

Check:

- every changed source passage/object is reconciled across related manuals, apps, diffs, helpers, self-hosted pages, Ghost fragments, and sibling artifacts—or intentionally omitted with a recorded reason;
- the Substack helper source SHA-256 and editor-body SHA-256 match the exact final archival source;
- its one complete payload covers the editor body exactly once after recorded comment/paywall conversions;
- the payload wrapper is `div[dir=auto].body.markup`;
- only known editor locks were removed and fragile markup was not globally reserialized;
- only controls required by the confirmed browser/file-opening path are visible;
- self-hosted HTML has no previous-host scripts, CSS, analytics, metadata, assets, ads, comments, upload bars, or other provider chrome;
- self-hosted IDs are unique, anchors resolve, owned metadata is present, and mobile/print checks pass;
- Ghost output contains no document tags, has one unique root, namespaced classes, root-scoped selectors, no inappropriate fixed sidebar, correct full-width behavior, and fixed-pixel critical navigation typography where needed;
- a real Ghost or Substack destination result is distinguished from source validation;
- newly supplied files and canonical-equivalent URLs were merged into the active source packet;
- no native embed was invented from a normal page URL.

## 10A. Argument and evidence architecture

Flag:

- an unmarked load-bearing premise;
- evidence and explanatory narrative blended together;
- public availability treated as actual knowledge;
- character or legacy used as proof;
- asymmetric skepticism toward favored and disfavored explanations;
- chronology converted into unsupported causality;
- one vivid detail dominating stronger evidence;
- cumulative evidence ignored or exaggerated;
- dependent repetitions mistaken for independent corroboration;
- a later admission or correction failing to update title, opening, analogy, jokes, conclusion, or derivative artifacts;
- peripheral evidence bloating the minimum decisive case;
- a definitive short form drafted before the full audit;
- uncertainty deferred to an end disclaimer;
- an argument that collapses after jokes, insults, political labels, character claims, and legacy appeals are removed;
- hidden source-access failures.

When one appears, identify the premise, dependency, evidentiary classification, and required global repair. Route documentary allegations to `CONTROVERSIAL-TOPIC-EVIDENCE-AUDIT.md`.

## 10B. Deterministic-ledger integrity and over-editing audit

When a deterministic ledger was used, check:

- source packet/file hashes and provenance IDs correspond to the active packet;
- factual judgments were not inferred from indexing alone;
- every propagated impact follows an explicit edge;
- dependent repetitions from one source were not counted as independent evidence;
- `weakened` premises were reviewed rather than mechanically invalidated;
- alternative-support (`any`) claims were preserved when another independent support survived;
- the report did not modify prose or override edit permissions;
- claim/evidence/destination caps were treated as brakes rather than quotas;
- ordinary paragraphs were not mapped merely to make the ledger look complete;
- the graph did not replace narrative, voice, or mixed human material;
- the minimum decisive case contains only claims explicitly selected after the full audit;
- the ledger stopped expanding once remaining research was peripheral.

Flag any automatic global rewrite, implied dependency, or sentence-by-sentence mapping as an over-editing failure.

## 13. Coherence-first author-intent and detector-repair audit

Read `HUMANIZATION-AND-COHERENCE.md` and `TRANSFORMATION-CASE-STUDY.md`. When prose is being repaired after AI drafting or polishing, report:

- source condition: Joel-shaped with local model polish / mixed throughout / generated from the premise upward;
- whether duplicate text, OCR/PDF corruption, stripped links, missing punctuation, scan artifacts, or editor overlays were separated from detector findings;
- whether the interview was treated as a source pool or as a transcript/required inventory;
- whether Joel still endorsed the inherited central claim, cause, actor assignment, heading, attribution, and passage purpose;
- whether the literal question promised by the heading was stated before author-intent questions or prose;
- whether a motive heading such as “Why I’m publishing/writing this” was replaced by a novelty summary, literature survey, or thesis preview;
- every substantive semantic correction discovered during detector repair;
- the source-pool classification of retained and omitted material;
- whether optional examples, brainstorming, repeated explanations, risky detail, and process provenance were selected rather than accumulated;
- whether the outline was built independently of interview-question order;
- whether the coherence architecture card was completed before prose, including heading-function promise and motive/obligation when relevant;
- whether prior knowledge was distinguished from what later research merely sharpened, verified, or made more precise;
- whether the source world was mapped by real failure modes, chronology, personal dependence, mistaken deference, revised attribution, and unequal importance rather than one contribution per name;
- whether the governing movement is intelligible even when the section carries several functions;
- whether raw-source preservation was separated from publication reuse;
- every substantial exact raw-source span reused and its reason;
- whether the draft was composed in fresh syntax or assembled as a clause mosaic;
- whether the paragraph chain passes: inheritance, relation, forward pressure, and removal consequence;
- the central claim, causal model, strongest complication, audience, progression, evidence levels, and honest stopping point;
- the rhetorical function of each retained paragraph or item;
- whether the candidate reads as coherent finished prose without consulting the interview;
- whether it remains coherent with the paragraph before and after it;
- whether first-person experience, doctrine, interpretation, mechanism, and external evidence remain distinguishable;
- every model-written bridge, synthesis, metaphor, paragraph ending, caveat, or conclusion added after elicitation and whether it is necessary;
- whether concreteness, abstraction, first person, humor, headings, paragraph length, or unusual syntax were used because the thought required them rather than as detector superstitions;
- whether expansion restored missing publication motive, duration, source classes, dependence, admiration, self-doubt, or changed judgment;
- whether an exact abstract conclusion was simplified or blamed when the real defect was the missing route leading to it;
- document classification, sentence shading, and split/boundary results as separate signals;
- the exact owner-approved tested lock, including relevant heading, paragraph, link, lead-in, exit sentence, punctuation, emoji, and neighboring order;
- whether Joel corrected a passing candidate, with pure P1 corrections recorded without retest and substantive visible or boundary changes retested before re-locking;
- whether all candidates were preserved and a regressing candidate was abandoned in favor of the strongest coherent faithful baseline;
- whether the reconstruction ceiling was respected;
- whether the cumulative detector-learning ledger was updated after every test and one-off lessons remained local;
- whether the complete paste-ready passage was returned;
- whether the exact source span and neighboring headings were verified before omission/completion claims;
- whether owner deletions were resolved rather than banked;
- whether the next available section was located and advanced without making Joel resend it;
- whether assistant-produced/owner-accepted sections entered the recheck queue;
- whether two globally failing architectures stopped before a third model paraphrase;
- whether provisional author options were distinguished from closed model taxonomies;
- detector result as diagnostic evidence only.

Critical process failures include transcript collage, clause mosaic, unexplained verbatim dependency, architecture-after-prose, heading-function substitution, publication-motive erasure, invented research epiphany, question-order drafting, source-landscape flattening, source-role symmetry, proposition-route substitution, question-frame contamination, wrong-thought preservation, dead recap, score-over-owner, false P1 detector fragility, sentence-color literalism, boundary amnesia, candidate-regression drift, process-provenance leakage, abstract-thesis scapegoating, and detector-approved inaccuracy.

The target is Joel's actual thought expressed as coherent finished prose. A candidate fails this audit even with a strong detector score when it is inaccurate, incoherent, semantically softened, or built around the wrong inherited argument.

### Additional counts

- Author-intent interviews triggered
- Semantic-reset gates run
- Inherited claims/headings/actors/causes rejected or corrected
- Heading-function substitutions found
- Motive sections replaced by novelty summaries
- Invented source-triggered epiphanies
- Source landscapes flattened into equal-weight inventories
- Source-pool items retained / omitted by class
- Transcript-collage or question-order failures
- Process-provenance leaks
- Model-written bridges added after elicitation
- Coherence-audit failures before detector submission
- Candidates preserved and candidate regressions reverted
- Exact blocks locked with boundary context
- Pure P1 owner corrections recorded without unnecessary retest
- Substantive owner-corrected passing blocks retested
- Document / sentence / boundary tests distinguished
- Mechanical extraction defects separated
- Detector-learning ledger rows completed
- One-off lessons incorrectly promoted
- Reconstruction ceilings exceeded
- Complete paste-ready passages returned
- Section provenance states and unresolved assistant rechecks
- Source-boundary overclaims
- Owner deletions incorrectly banked or resurrected
- Third-architecture paraphrases after two global failures
- Source statements Joel was made to repeat
- Placement questions returned without recommendations
- Provisional author lists misclassified as closed taxonomies
- Generic appendix/meta-orientation architectures
- Invented first-person research reactions
- Abstract-based candidates not retired after full-source reset

## 14. Layered attribution and correction-propagation audit

For doctrinal, philosophical, scientific, or interpretive arguments, distinguish:

1. what the primary source directly says or supports;
2. what Joel reports experiencing;
3. Joel's developed interpretation or synthesis;
4. a proposed causal or cognitive mechanism;
5. analogy or explanatory metaphor;
6. external scientific or historical evidence;
7. unresolved alternatives and what would change the conclusion.

After a substantive correction, search exact wording and nonliteral equivalents across title, subtitle, opening, section introductions, summaries, headings, definitions, glossary, appendices, diagrams, captions, analogies, conclusions, links, and derivative short forms. A local wording repair does not pass if the superseded judgment remains elsewhere.

For main-article plus technical-appendix designs, record the function of each recurrence. The main article should carry the smallest evidence and explanation needed for the present decision; the appendix may carry the full textual or technical case. Repetition is justified only when the rhetorical function changes.

### Additional counts

- Author-intent interviews triggered
- Author-supplied exact/near-exact phrases preserved
- Model-written bridges added after elicitation
- Locked passing blocks altered
- Detector split tests used
- Source / experience / interpretation / mechanism conflations
- Corrections propagated only literally
- Main/appendix duplications without function change
- First-use terms missing or over-explained

## 15. Developmental architecture, epistemic planes, and detector-quality audit

Check:

- whether a developmental diagnosis was separated from implementation and Joel's decision;
- whether the operational article purpose states mystery/problem, destination, route, payoff, and early stakes;
- whether distinctive material appears before generic theory or the highest credibility-cost claims where appropriate;
- whether the heading tree and table of contents show the real argument for skimmers;
- whether the ending performs the intended function rather than merely occupying the last position;
- whether each section remains intelligible to a reader arriving at its heading without duplicating the full proof;
- whether repeated distinctive terms change semantic valence and need distinction rather than deletion;
- whether the world claim, Joel commitment/certainty, inferential status, and detector evidence remain separate;
- whether citations visually absorb nearby interpretation, synthesis, mechanism, or speculation;
- whether originality/lost-key claims state what would count against them and what was actually searched;
- whether abductive support is presented as proof, especially when the “prediction” was added after the observation;
- whether evidence timing was repaired through point-and-move rather than fake hedging;
- whether first-person experience slid into mechanism, ontology, universality, or reader prediction;
- where the article spends skeptical-reader credibility and whether sequencing lets the reader evaluate the costliest claims;
- whether detector improvement was accepted despite worse fidelity, coherence, article function, editorial quality, or owner preference;
- whether a current master was propagated after accepted changes and every correction completed the closure state machine;
- whether a filename/hash/citation/status record was mistaken for a fully retrieved, installed, and verified body;
- whether `complete`, `current`, or `authoritative` was claimed despite assembly gaps, missing bodies, resurrected owner deletions, failed correction checks, or provenance/source/link gaps;
- whether one vivid owner correction was promoted into a universal rule without cross-case evidence, counterexamples, scope limits, or holdout survival.

### Additional developmental/epistemic counts

- Article-purpose fields missing
- Early-stakes failures
- Distinctive-material delays
- High-cost claims before earned credibility
- Heading-tree misrepresentations
- Ending-function mismatches
- Section-autonomy failures
- Full proofs duplicated where a pointer would suffice
- Semantic-valence conflations
- Epistemic-plane collapses
- Citation-absorbed inferences
- Self-sealing originality claims
- Abductive-support-to-proof inflations
- Point-and-move opportunities replaced by hedging
- Experience/mechanism/ontology/universality/prediction slides
- Detector-only wins with quality regression
- Corrections not closed in the propagated master
- Reference/body-access overclaims
- Master-completeness overclaims
- One-off lessons promoted without holdout support
