# Edit Contract, Source–Meaning–Context–Destination Ledger, and Claim-Change Control

Before a substantial rewrite, establish what may change. The size of the rewrite does not determine the preservation contract. Create or update `PROJECT_STATE.md`; the last user-approved artifact plus that state file determine the active revision, baseline, raw comments file, and unresolved decisions.

## Default contract

Unless Joel explicitly authorizes substantive revision, preserve:

- every proposition, allegation, opinion, recommendation, uncertainty marker, causal claim, and controversial position;
- exact memories, quotations, lyrics, anecdotes, catchphrases, coined terms, and distinctive language;
- who acted, who received the action, where it occurred, and when;
- links, media, captions, formatting, and article-specific chronology;
- unresolved causal alternatives, including the distinction between what happened, what action is prudent now, and why the outcome occurred.

Source verification may reveal a problem. It does not silently grant permission to rewrite the claim. Flag the issue and follow the permission matrix.

## Four-plane preservation: source, meaning, required context, and destination

Track four separate questions during P2S/P3/P4 work:

1. **Source:** What exact passage, claim, image, embed, definition, example, or transition existed, and where did it come from?
2. **Meaning:** What proposition, certainty, emotional judgment, attribution, and rhetorical function made it do its job?
3. **Required context:** Which definition, introduction, example, transition, heading, link, caption, media anchor, or neighboring claim must remain for it to make sense?
4. **Destination:** Where does it go in the revision, what job does it perform there, and does the required context still exist?

Wording can survive while meaning fails. A quotation can remain but lose the setup that made it funny; an example can remain after the claim it illustrated was cut; a media block can remain after the sentence introducing it moved; a coined term can survive after its definition disappeared. Treat those as preservation failures. Practical advice can also survive while causal meaning fails—for example, “stop driving” may be justified even when “the prior non-accident was luck” is not established.

Before claiming preservation, omission, or completion, record the exact source span inspected, the preceding and following headings, and whether the source was complete, excerpt-only, scan/PDF-only, full-text, abstract-only, snippet-only, or secondhand. A handoff's next-section excerpt is a routing target, not proof of the complete article boundary.

## P2S — style-only rewrite

Sentence architecture, cadence, paragraphing, transitions, humor, and section order may change. Propositions, factual assignments, allegations, certainty levels, links, media, coined terms, and personal history are locked.

In P2S:

- do not browse or fact-check unless Joel separately requests it;
- do not add safety framing, caveats, new claims, or a more defensible position;
- preserve `I think`, `apparently`, `seemed`, `I believe`, and categorical statements exactly in epistemic force;
- ask about a genuinely blocking ambiguity rather than resolving it by changing meaning.

## Permission matrix to establish once per article or project

Ask only the unresolved questions. Save the answers in the article working notes.

| Scenario | Default | Options Joel may authorize |
|---|---|---|
| Better source supports the same claim | Replace/add link; preserve wording unless source scope requires a flag | Update wording and record change |
| Source weakens, contradicts, or dates the claim | Flag outside the draft; preserve original in style-only mode | Qualify, replace, remove, or retain with explicit label |
| Claim cannot be verified | Flag and leave in place by default | Mark `[VERIFY]`, qualify, remove, or preserve as opinion/anecdote |
| Internal contradiction | Flag both passages | Reconcile only after Joel chooses the intended claim |
| New evidence suggests a useful substantive addition | Suggest outside the draft | Add only with approval |
| Legal, defamation, medical, or acute safety concern | State the exact concern and safest compliant path | Revise within the authorized scope; never silently sanitize the whole article |
| Unique phrase, anecdote, or catchphrase seems dispensable | Preserve | Replace or cut only with permission |
| A linked term, person, method, guide, or practice could be explained more fully | Preserve the concise linked reference when the current passage is understandable without more | Add the smallest useful gloss or a fuller explanation after Joel approves it |
| A surprising event has several plausible explanations | Preserve the observed event, the practical implication, and the unresolved alternatives separately | Prefer one cause only after Joel or discriminating evidence supports it |
| A controversial historical detail may distract or need verification | Preserve it when it carries causal history, moral tension, or narrative logic; flag sourcing separately | Qualify or remove only with Joel’s approval or a source correction that changes the supported claim |

## Source–meaning–context–destination ledger

Create this privately before any P2S, P3, or P4 rewrite of an existing article:

| ID | Source passage/object | Entity/place/time | Exact claim or memory | Actor → action → object | Certainty | Rhetorical function | Required context/antecedent | Audience contract/section shift | Emotional judgment | Attribution status | Link/media | Explanation origin | Link already carries background? | Reader needs explanation here? | Smallest sufficient gloss | Addition approval | Review decision | Decision timestamp | Superseded comment/decision | Change classification | Movement/consolidation destination | Keep-lock status | Destination + function | Locked language | Allowed change |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

The ledger must prevent **entity leakage**: a true detail about one person, community, date, or place being reassigned to another because the material appears nearby.

## Linked-reference and explanation audit

After every insertion or rewrite around a hyperlink, ask:

1. Was this explanation present in the source?
2. Does the current sentence or argument require it?
3. Does the destination page already provide it?
4. Is the explanation proportionate to the reference's role?
5. Does it preserve the local register?
6. Was it approved if substantive and new?

Record explanation origin as: original source; Joel-supplied new material; approved reviewer/source integration; canon fact; model-written explanation; or externally verified correction. A substantive `canon fact` or `model-written explanation` absent from the source requires approval unless it is the smallest orientation necessary to understand the sentence. Once Joel approves a useful addition, lock it against later mechanical deletion.

## Source terminology ledger

| Source term | Exact source meaning | Existing Joel term that overlaps | Adopted article term | Transition sentence present? | Approval |
|---|---|---|---|---|---|

Use this ledger only for genuinely source-specific terms or frameworks. Do not assign a common developmental idea to a reviewer merely because the reviewer supplied an explanation. Name the source's original term before normalizing distinctive terminology; do not erase attribution or repeatedly re-explain the bridge.


## Audience contract and section shifts

Record the project-level audience contract before substantial work:

| Dimension | Current contract | Evidence/source | Deliberate exceptions |
|---|---|---|---|
| Reader role/identity |  |  |  |
| Expected knowledge |  |  |  |
| Relationship to writer/subject |  |  |  |
| Intended action/decision/understanding |  |  |  |
| Stakes/emotional task |  |  |  |
| Register/form of address |  |  |  |
| Technical-vocabulary allowance |  |  |  |
| Publication venue |  |  |  |
| Explicitly excluded audiences |  |  |  |

A hybrid article may contain deliberate section-level shifts, but record the new audience and function at the shift. Do not allow source material, a reviewer, a citation, or a revised paragraph to silently change the reader relationship.

## Review-comment reconciliation

Before applying review comments or interface decisions, preserve the raw export unchanged as `review/source-comments.json` and create a separate ledger from `COMMENT-RESOLUTION-LEDGER-TEMPLATE.md`. Every source comment receives a stable issue ID, classification, status, and exact revised destination.

Then:

1. order the full comment and decision history chronologically;
2. attach each comment to the exact row, side, quote/text hash, semantic block, and artifact version;
3. identify the proposition, certainty, rhetorical function, applicable audience-contract dimensions, required context, and dependent artifacts;
4. treat a later clarification, retraction, correction, or `never mind` as controlling;
5. infer the judgment being protected rather than applying the wording mechanically;
6. record Keep, Remove, Brainstorm, movement, consolidation, and structural-removal states;
7. keep evidence challenges outside the article until substantive authority is granted;
8. run the post-comment orphan, audience, jargon, heading/ToC, native-object, and artifact-family audits;
9. confirm every issue is implemented, partially implemented, needs clarification, not implemented with reason, or superseded/retracted;
10. reduce the unresolved count to zero unless Joel explicitly accepts open issues in `PROJECT_STATE.md`.

**Keep** locks the current passage against casual later rewriting. **Remove** authorizes deletion only after required context and dependencies are repaired. **Brainstorm** requests options and approves none. Rhetoric sliders never alter claims, evidence, certainty, recommendations, attribution, causal meaning, links, or media placement.

For substantial work, the last user-approved article is the default diff baseline. Record its revision ID, filename, and SHA-256 together with the candidate revision. Preserve two comparison baselines: original source vs current revision, and previous delivered revision vs corrected revision. Classify every unit as Rewritten, Moved, Consolidated, Structurally removed, Owner-deleted, or Preserved; show destinations for movement and consolidation.

## Dependency audit after every correction

A correction is structural evidence, not a local typo. Search the whole draft for dependent:

- comparisons and pronouns;
- chronology and causal bridges;
- jokes and captions;
- later conclusions;
- repeated definitions;
- entity assignments;
- first-person interpretations.

Move material when needed. Do not patch a wrong architecture with explanatory glue.

## Orphan audit after every cut, insertion, or reorder

Do not wait until the end. After each structural change, search for:

- a coined term whose first-use definition was cut, moved too late, or separated from the joke/example that depends on it;
- a section introduction that promises material no longer present;
- an example whose claim, comparison, or interpretive target has disappeared;
- a conclusion or takeaway whose evidence was moved elsewhere;
- a transition whose antecedent no longer exists;
- an image, caption, chart, embed, or link whose textual anchor was cut or relocated;
- a sentence referring to “this,” “that,” “same,” “other,” “otherwise,” “also,” “still,” “too,” “yet,” or “but” after the logical relation changed;
- a heading level or table-of-contents branch that became illogical after a section or object moved;
- a repeated issue whose second appearance now performs the same job as the first.

Repair by restoring context, moving the object, rewriting the transition precisely, or cutting the now-orphaned material. Do not add vague glue merely to keep everything.

## Agency audit

For specialized frameworks, state the semantic triple before paraphrasing:

| Actor | Action | Object |
|---|---|---|
| Present-day person acting through inner adult role(s) | reparents | inner child |

Check founder/member, parent/child, guide/participant, speaker/listener, and practitioner/community relations the same way. A fluent sentence can still reverse the idea.

## Corrections control judgment, not only wording

When Joel supplies a better sentence, identify the judgment it protects. For example, a correction may preserve real praise while adding a separate moral limitation, rather than turning the praise into setup for one neat “shadow.” Save the underlying rule in the working notes, then audit parallel passages for the same flattening.

## Purposeful recurrence ledger

An issue may appear more than once when each occurrence has a different function. Record:

| Issue | Location | Function here | What would be redundant |
|---|---|---|---|

A lived contradiction in a place-based section and a membership-design test in a values section are not duplicates. Repetition becomes a problem when the second appearance restates the same claim for the same purpose.

## Section provenance and assistant recheck ledger

Track accepted sections separately from detector results:

| Section ID / exact boundaries | Current text location | Provenance state | Owner approval | Detector status + exact boundary | Fact/link pass | Later recheck required | Recheck result | Supersedes |
|---|---|---|---|---|---|---|---|---|

Allowed provenance states:

- `owner-authored untouched`;
- `natural owner rewrite/publication prose`;
- `detector-targeted owner edit/minimal pair`;
- `owner-edited final — naturalness unknown`;
- `assistant-produced owner-accepted`;
- `owner-final available only in scan/PDF`;
- `superseded assistant candidate`;
- `synthetic detector probe`.

Do not infer natural human-writing status from `owner-edited` or detector success. Joel may deliberately make minimal detector-targeted edits that remain far from his natural prose. Record naturalness separately when known.

Acceptance by moving on or approving a detector result does not establish owner authorship or later line-by-line approval. Every `assistant-produced owner-accepted` section enters a mandatory publication recheck queue for full-context coherence, voice, source boundary, facts/links, banned patterns, neighboring transitions, and omission dependencies. An exact owner edit may change provenance. Pure P1 spelling, punctuation, capitalization, spacing, literal-agreement, and broken-link corrections retain prior detector status when visible semantic wording and tested boundaries do not change; substantive visible or boundary changes do not.

## Cumulative omission audit

Maintain this during live section work:

| Omission ID | Source span | Exact material/function | Change type | Assistant or owner decision | Destination / resolution | Authority | Status |
|---|---|---|---|---|---|---|---|

Change types include omitted, generalized, moved, certainty-changed, actor/cause changed, media-separated, restored, owner-deleted, superseded, and duplicate-function consolidation. Joel's own authoritative deletion is `owner-deleted/resolved`; do not place it in the carry-forward bank or ask about restoring it unless Joel assigns a later destination. Before final assembly, ask Joel only about unresolved assistant-created omissions.

## Consolidation disclosure

Every section or passage consolidation requires an external explanation to Joel. Name what was combined, the destination of every unique function or example, and why wording disappeared: moved intact, merged into the destination, duplicated the same function, or genuinely superfluous. `Consolidated` by itself is not an explanation. A substantive claim, exact memory, distinctive phrase, or authorized recurring function cannot be labeled superfluous without the normal edit authority.

## Substantive change report

After any authorized source-corrective or developmental pass, list outside the article:

- substantive claims added;
- substantive claims deleted;
- certainty strengthened or weakened;
- actors, chronology, or causality changed;
- anecdotes or unique language removed;
- links replaced and why.

No item means `No substantive claim changes.`

## Diff origin labels

For a substantial revision, label each changed passage by origin:

- source-derived consolidation;
- Joel-supplied addition;
- approved reviewer/source integration;
- canon-fact insertion;
- model-written explanation;
- research correction.

Substantive `canon-fact insertion` and `model-written explanation` changes must be conspicuous before approval. An approved explanation becomes locked in later passes unless Joel changes it.

## Artifact-family dependency ledger

When an article has related manuals, apps, diagrams, diffs, transfer-ready payloads, helpers, self-hosted pages, Ghost cards, or sibling documents, maintain one family ledger in addition to the passage ledger. Link it from `PROJECT_STATE.md` and include it in the authoritative ZIP when active:

| ID | Updated source passage/object | Meaning/function | Required context | Destinations that may require update | Updated destinations | Intentionally omitted destination + reason | Status |
|---|---|---|---|---|---|---|---|

A destination is not complete merely because the source article is correct. Check each derivative artifact. Rebuild the Substack transfer-ready payload and helper from the exact final archival HTML after every revision. Prefer one complete payload; verify that every native object is converted at its approved source position and that no prose, heading, link, or media anchor is omitted or duplicated.

When Joel supplies another file or URL during the active task, add it to the current source packet, canonicalize URLs for identity comparison, and re-run only the dependencies it changes. Do not discard already validated sources or restart from an earlier packet.


## Semantic native-object placement ledger

For an existing Substack article, inventory each image, digest preview, YouTube/video block, Share object, Subscribe object, comment card, paywall, and unknown native object:

| Order | Object type | Exact source hash | Canonical URL/node ID | Preceding anchor | Following anchor | Rhetorical function | Approved destination | Archival treatment | Transfer treatment | Destination result |
|---|---|---|---|---|---|---|---|---|---|---|

The raw editor HTML establishes identity and metadata. An approved P3 revision may move the intact object, but the move must be recorded, its anchors and heading logic updated, and the transfer payload rebuilt from the exact revised archival HTML. Object counts are regression evidence, not destination proof.

## Derivative compatibility ledger

For every artifact family with a confirmed destination path, maintain:

| Artifact | Confirmed source version | Target browser/platform | File-opening path | Visible controls and order | Hidden fallbacks | Native-object strategies | Confirmed destination result | Locked invariants | Last regression test |
|---|---|---|---|---|---|---|---|---|---|

For the confirmed Opera/Substack path, the locked invariants are: downloaded local HTML; one visible `Copy Article` control; no visible manual-copy field; one complete payload wrapped in `<div dir="auto" class="body markup">`; only `contenteditable="false"` and `draggable="true"` removed from transferable native objects; the immediate `ClipboardItem` path with a silent off-screen-contenteditable `execCommand("copy")` fallback; images, digest previews, YouTube/video blocks, Share, and Subscribe retained as rich HTML under their per-type status; rendered comments replaced by canonical URLs alone in the same source position; and manual paywall placement shown only when a genuine source marker exists. Splitting the article is not a default repair and requires destination evidence.

### Derivative regression rule

Rebuilding from the newest source is not sufficient. Compare the new derivative with the last confirmed derivative and preserve every locked invariant. A compatibility behavior may change only because Joel requested it, the destination changed, or a new empirical test demonstrated that the previous behavior was defective. Record the reason and the new destination result.

## Argument-dependency ledger

For substantial research, polemic, critique, investigation, or contested factual argument, also maintain:

| Claim ID | Premise | Evidence type | Certainty | Load-bearing? | Supports | Depends on | Counterevidence | Later update | Required global repairs |
|---|---|---|---|---|---|---|---|---|---|

A factual correction can invalidate an explanatory theory or the entire article architecture. When this happens, preserving the old thesis is not claim preservation; it is a new factual distortion.

In P2S/style-only mode, report the failed premise and affected dependencies rather than silently changing the argument. In authorized substantive mode, rebuild all dependent sections and derivative artifacts under `ARGUMENT-AND-EVIDENCE-ARCHITECTURE.md`.

## Deterministic argument-ledger safeguards

When `argument_ledger.py` is used:

1. its source hashes and segment IDs establish provenance anchors only;
2. evidence/claim/destination entries remain analytical assertions that require review;
3. only explicit `depends_on` edges propagate into an impact report;
4. unmapped passages and artifacts remain unaffected unless a human audit identifies a missing dependency;
5. `weakened` means review; it does not invalidate dependent prose automatically;
6. a `global dependency review candidate` is not authority to rewrite;
7. P2S reports the impact outside the draft and preserves the original argument;
8. substantive P3/P4 repair still requires the article's permission matrix;
9. no script output may silently delete a claim, anecdote, joke, caption, link, or derivative artifact;
10. once the decisive case is stable, retire the ledger from active expansion and continue with normal editorial judgment.

Treat missing edges as a reason for a focused human dependency audit, not a reason to map the entire article retroactively.


## Worker-chat state boundary

Changing authoritative state does not automatically close the worker or require a ZIP. Continue related passes in the same chat while the baseline, branch, and current artifact remain clear. Create a compact or full handoff only when Joel requests a transfer, a materially separate outcome should move to another worker, or context ambiguity creates a real accuracy risk. Use a full ZIP for complex multi-file families; a simple current file plus `CONTINUATION.md` may carry a single-file project. A full handoff includes the current section-provenance ledger, cumulative omission audit, and assistant-produced recheck queue. Immediate repair remains in the current worker. The latest authoritative artifact and recorded decisions carry authority forward.

## Author-intent recovery and detector-learning ledgers

Use these privately when AI drafting or polishing may have softened, generalized, normalized, reorganized, or replaced Joel's thought. Read `TRANSFORMATION-CASE-STUDY.md` first.

### Source-pool and semantic-reset ledger

| ID | Original passage + full context | Exact source span + neighboring headings | Source completeness/access level | Source-pool class | Joel's actual central claim | Inherited assumption or wrong thought | Actor → action → object | Cause / permission / accompaniment distinction | Certainty | Heading/attribution/link-context check | Rhetorical function | Exact or distinctive language | High-value example/complication | Optional or omitted material + reason | Process provenance removed | Coherent destination + paragraph function | Model-written bridge | Substantive correction discovered | Permission / propagation status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Classify interview material as: locked claim/correction; distinctive author language; high-value example; optional illustration; purposeful repetition; brainstorming alternative; process provenance; external evidence; redundant explanation; risky/overexplicit detail; model-written bridge; owner-corrected detector-passing text; or extracted text missing link/media context.

## Coherence architecture and raw-language ledger

Before P2S/P3/P4 prose from interviews, notes, or an AI-shaped source, create this private card:

| Field | Required entry |
|---|---|
| Real pressure/question | Why the section exists |
| Reader stake | What the reader needs here |
| Controlling claim/certainty | Exact position and limit |
| Intellectual/lived route | Known first → friction → search/experience → change → stopping point |
| Actor → action → object | Exact agency and purpose |
| Causal/chronological chain | Ordered relations, not mere adjacency |
| Evidence roles | Source/example/experience/opponent and unequal weight |
| Strongest complication | Contradiction, mixed motive, unresolved cost, countermodel |
| Governing movement | One progression that may carry several functions |
| Paragraph jobs | What changes for the reader in each paragraph |
| Stopping point | Last necessary move; predicted recap after it |
| Exact language retained | Span + reason: lock / quotation-memory-formula / identity / semantic precision / temporary placeholder |

Archive all raw wording separately. Any substantial exact span reused from a raw interview or brainstorm note requires a reason; owner-final prose is exempt. Draft from the card in fresh syntax, then restore justified exact language and run the source/meaning/context/destination audit.

A draft fails when it follows question order, maps one answer or source to each paragraph, stitches clauses from several answers, or can be freely reordered despite requiring an argument or lived progression.

### Author-Intent Carry-Forward Bank

Create this active-project bank whenever an author-intent interview produces valuable material that does not belong in the current passage:

| Bank ID | Exact raw answer or wording | Protected proposition | Certainty | Actor → action → object | Evidence/experience layer | Why it does not belong here | Candidate destination | Function there | Required setup/dependencies | Duplication or conflict risk | Status | Integrated location or omission authority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

Allowed statuses: `use-now`, `banked`, `integrated`, `deferred-to-appendix`, `project-context-only`, `needs-destination`, `needs-Joel-decision`, `omitted-with-reason`, `superseded`.

Rules:

1. Give every substantive interview answer one disposition: use now; bank for a named later destination; preserve as project context/evidence; or omit with reason.
2. Preserve Joel's exact raw wording even when later publication prose is selected, consolidated, generalized, or rewritten.
3. `Optional or omitted material + reason` in the source-pool ledger is insufficient when the material may have a later destination. Bank it before omission.
4. Consult destination-relevant entries before drafting later sections. Record the exact integrated location after movement or consolidation.
5. Do not draft in Bank-ID order, follow question order, or empty the bank as a publication checklist. Re-evaluate each item in local context.
6. Before final delivery, resolve every item as integrated, explicitly deferred, project-context-only, superseded, or omitted with reason and required approval.
7. Permanent omission of a substantive claim, correction, certainty marker, actor relation, exact memory, or unusual judgment still follows the permission matrix.
8. Joel's own authoritative deletion is `owner-deleted/resolved`, not `banked`; preserve it in provenance/history only when needed to prevent accidental resurrection.

### Candidate and detector-learning ledger

Create one row after every tested candidate:

| Passage ID and exact boundaries | Candidate/version | Detector result + sentence shading | Exact change from prior candidate | Coherence result + reason | Fidelity result + claim/actor/cause/certainty issue | Locked material + boundary context | Suspected cause | Confidence | Lesson scope: local / repeated / promoted | Semantic correction discovered | Next action: lock / boundary test / author questions / revert / author rewrite / stop |
|---|---|---|---|---|---|---|---|---|---|---|---|

Rules:

1. Treat the interview as a source pool, not a transcript, sentence bank, required inventory, or architecture. Archive exact raw wording, but reuse it in publication only for a recorded reason. Omitting optional material is allowed; changing locked meaning, certainty, actor assignment, causal relation, exact memory, or locked language still requires authority.
2. Author-intent selection is not disposal. Assign every substantive answer a disposition and bank valuable unused material before it is forgotten or forced into the current passage.
3. Before reconstruction, verify the actual claim, cause, actor/action/object relation, chronology, heading, attribution, link context, and whether Joel still wants the passage. Questions based on an AI-shaped passage do not validate the passage's assumptions.
4. Complete the coherence architecture card before prose. Build the outline independently of question and source order; require one governing movement, paragraph jobs, and a deliberate stopping point. Several legitimate functions may coexist.
5. Draft from the architecture card in fresh syntax, then restore exact language that is locked, evidentiary, identity-bearing, semantically precise, or functionally superior. Author-language fidelity permits selection, consolidation, movement, synthesis, natural transitions, and paragraph development. It forbids both clause mosaics and generic normalization.
6. Run the verbatim-dependency and paragraph-chain audits before detector testing. Read the passage without the interview and with its preceding and following paragraphs. Confirm that each paragraph has one intelligible job, a real relation to its neighbors, and that the ending stops where the thought arrives.
7. Separate document-level classification, sentence shading, and split/boundary results. Identify duplicate text, OCR/PDF errors, stripped links, punctuation loss, scan artifacts, and editor overlays before interpreting detector output.
8. A detector lock covers the exact coherent owner-approved tested unit and relevant boundaries, including heading, paragraphing, links, lead-in, exit sentence, punctuation, emoji, and relative order. A green sentence inside generated architecture is not independently protected.
9. Joel's correction supersedes every model candidate and score. Pure P1 corrections retain prior detector status; retest substantive visible or boundary changes before transferring a detector lock.
10. Preserve all candidates. If a later version is less coherent or faithful, revert to the strongest prior coherent baseline. Revision order is not progress.
11. Before counting a coherent local failure as an architecture failure, run the smallest plausible interference tests across the complete boundary: contraction versus expanded negation; nominal/idiomatic caveat versus fully specified verbal disclaimer; flat coordinate-list syntax versus relation-aware syntax with the identical items; phrase order and neighboring boundary. Do not change content during a syntax-only test.
12. Use the reconstruction ceiling after local interference is ruled out where applicable: one surgical reconstruction; one coherent post-interview architecture; and, only after a genuine global failure, one different architecture test. If both architectures fail globally, request Joel's rewrite. No third model architecture or conversational paraphrase loop.
13. Record one compact lesson after each result. A one-off detector movement remains a local hypothesis until it recurs across materially different passages.
14. Return the complete paste-ready passage and report every substantive correction discovered during repair. Apply normal dependency and correction-propagation audits to claim, actor, cause, certainty, heading, attribution, or omission changes.
15. Detector movement never proves authorship, quality, truth, or approval and never authorizes degraded prose.

## Research access, evidence-role, and first-person provenance ledger

| Source | Access level: full / abstract / snippet / secondhand | What Joel personally read or encountered | Article role(s) | Supports | Resists / countermodel | Source domain and limits | Experience preceded source? | Candidate invalidated by fuller source? | Destination |
|---|---|---|---|---|---|---|---|---|---|

Do not write that Joel read, noticed, agreed with, disagreed with, found, or was surprised by a source unless he supplied that history. A collaborative later audit does not retroactively create personal reading provenance. When a full source materially changes an abstract-based treatment, retire the old candidate and reassign the source's roles.

## Layered source-and-interpretation ledger

| ID | Proposition/component | Primary source directly supports | Joel's lived experience | Established theory | Joel's developed synthesis | Proposed mechanism | Practice/exercise rationale | Analogy | External evidence | Competing interpretation | Certainty | Does not establish | Local gloss | Destination |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Do not let one column silently validate another. A source may support an experiential instruction or cessation framing without directly teaching Joel's complete mechanism. A lived event may motivate an interpretation without establishing doctrine. A scientific analogy may clarify a model without proving the spiritual claim.

## Main-article / technical-appendix function ledger

| Issue or evidence cluster | Main-article function | Smallest sufficient treatment | Appendix function | Full treatment retained | Cross-reference | Redundancy risk | Orphan audit |
|---|---|---|---|---|---|---|---|

Move detail by function, not merely length. Preserve the main article's narrative and minimum decisive case; place full source disputes, philology, mechanism, and counterargument in the appendix. Do not repeat the same proof unless the second occurrence performs a different job.

## Semantic correction-propagation audit

For every correction that changes an underlying judgment:

1. state the superseded judgment, not only the replacement sentence;
2. list exact stale phrases and likely nonliteral equivalents;
3. search title, subtitle, opening, section introductions, summaries, headings, definitions, glossary, appendices, comparisons, analogies, jokes, captions, conclusions, calls to action, links, diagrams, and derivative short forms;
4. distinguish direct dependency, analogous judgment, transition risk, orphan risk, and purposeful recurrence;
5. preserve independently supported passages and purposeful recurrences;
6. report exact review targets before rewriting when the task is review-only;
7. after repair, re-audit certainty, attribution, causal wording, term introduction, and main/appendix duplication.

A correction that narrows what one source teaches may require global attribution repair while leaving the broader author-developed model intact. Do not erase the model merely because one citation was over-credited; reassign support precisely.

## Article-purpose and developmental-advice ledger

Before whole-article developmental work, record:

| Field | Current controlling value | Source/authority | Reviewer misunderstanding risk | Status |
|---|---|---|---|---|
| Mystery/problem |  |  |  |  |
| Destination |  |  |  |  |
| Why the route is necessary |  |  |  |  |
| Payoff |  |  |  |  |
| Early promise/stakes |  |  |  |  |
| Distinctive material |  |  |  |  |
| Highest credibility-cost claims |  |  |  |  |
| Intended ending function |  |  |  |  |

Record external advice separately:

| Advice ID | Recommendation | Underlying concern | Joel accepts/rejects/qualifies | Corrected controlling purpose | Analogous recommendations affected | Implemented operation |
|---|---|---|---|---|---|---|

The concern may survive when the operation is rejected. No reviewer recommendation overrides the article-purpose statement or permission matrix.

## Four-plane epistemic ledger

For every substantial changed claim, record:

| Passage/claim | World claim | Joel commitment + certainty | Inferential status | Source role/access | Detector boundary/model/date/result | Separation issue | Resolution |
|---|---|---|---|---|---|---|---|

Inferential status includes observation, memory, quotation, established theory, interpretation, synthesis, mechanism, analogy, speculation, and invitation. A citation does not convert adjacent inference into source support. Detector evidence never changes the first three planes.

For originality/lost-key or abductive claims, add:

| Claim | What would stop publication/refute it | Search actually performed | Material unavailable | Prediction independent and prior? | Competing explanations | Supported conclusion level |
|---|---|---|---|---|---|---|

## Point-and-move edit classification

Use `Point and move` when conviction remains unchanged but evidence is badly timed. Record the early claim, forward pointer, moved evidence, later decision point, former-location transition repair, destination completeness, and whether any wording was falsely hedged or strengthened.

## Correction closure and propagated-master state

A correction uses this state machine:

**captured → classified → applied to master → verified in master → dependency audit complete → detector status determined → closed**

Track:

| Correction ID | Captured | Classified | Applied to master | Verified in master | Dependency audit | Detector status | Closed | Blocking issue |
|---|---|---|---|---|---|---|---|---|

A note, ledger row, candidate section, bibliography entry, or assistant response does not count as application. Maintain one current master after each accepted section change or set `Master status: pending reconstruction`.

## Body-access and master-completeness ledger

Use exact access states:

- `reference known`;
- `body partially retrieved`;
- `body fully retrieved`;
- `body installed`;
- `body verified`.

| Artifact/section | Access state | Exact source/body location | Hash if available | Installed destination | Verification method | Gap |
|---|---|---|---|---|---|---|

Do not claim no upload is needed until full retrieval or authoritative reconstruction is complete. `Complete`, `current`, and `authoritative` require: no assembly-gap markers; every authoritative body present; owner deletions not resurrected; correction register passing; provenance and detector state recorded; and source/link gaps named separately.

A deterministic validator may block completion for repeated high-risk exact-string or semantic errors. It may not repair prose or override Joel.

## Learning-rule and evaluation ledger

Every promoted rule records:

| Rule ID | Supporting exact pairs/triples | Distinct genres/sections | Confidence | Counterexamples | Scope limits | Retirement condition | Holdout result |
|---|---|---|---|---|---|---|---|

Preferred example units are exact human-source → assistant rewrite → owner repair triples, then assistant → owner pairs with full neighbors, detector boundaries, conceptual corrections, rejected candidates, and Joel's quality judgment. Human false positives, AI false negatives, detector-green bad prose, P1 variants, heading/boundary perturbations, movement-only wins, expansions, and compressions belong in the controls.

Use a development set and a never-touched holdout. Blind fidelity, coherence, owner/editor quality, and article-function judgments precede detectors. A rule fails when it causes regression on any controlling quality gate, even if one classifier improves.


## Short-excerpt cold-audit card

Use when Joel asks human / AI / mixed for a short excerpt:

| Exact boundary | Prose-shape verdict | Shape evidence | Content-neutralized architecture | Thought provenance | Fidelity/editorial quality | Topic/truth/provenance considered only after shape? | Percentages avoided unless requested? |
|---|---|---|---|---|---|---|---|

The prose-shape verdict controls the requested classification. The other columns prevent provenance, agreement, accuracy, and epistemic quality from haloing it.

## Controlled detector minimal-pair ledger

| Pair ID | Full boundary + neighbors | Variant A | Variant B | Exact delta | Other changes | Source/owner provenance | Detector/model/version/date | Repeated-run stability | Document result | Sentence shading | Boundary result | Joel preference | Blind fidelity/coherence/editorial ranking | Editorial distinction | Counterexamples | Generalization status | Holdout result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

One-token and one-construction effects remain contextual hypotheses until the underlying editorial operation recurs. Preserve the complete boundary and never reduce the lesson to a universal word association. For contraction/caveat cases, record contraction status, nominal versus verbal realization, and any proposition shift. For list cases, record cardinality, exact item set, order, apparent semantic class/homogeneity, and coordination topology; a syntax-only comparison must keep every item unchanged. A detector win produced by adding or deleting factual content fails the quality gate. Use the short-excerpt anti-halo rules in `FINGERPRINT-PASS.md` and the local-interference rules in `HUMANIZATION-AND-COHERENCE.md`.
