# Comparison admission and executable boundaries

**Status:** pre-registered inputs/assignments only. No baseline generator, separate writer, independent evaluator or Pangram job has executed.

## Primary question
Does showing a writer a **relevant, literal source-verified teaching episode** improve generation of faithful, naturally human-sounding Joel-byline prose, compared with the same revision task without that episode, across varied source families?

The observed golden forgiveness example is a teaching source; it is **never a target** and neither its actual words nor its topic may be copied into a different article. One successful local pair does not establish a portable phrase rule.

## Crucial cohort interpretation
The 30 selected targets are **original registered source paragraphs**. They have mixed or unresolved authorship provenance and may already be high-quality humanized paragraphs. They are excellent *fidelity references* and *unnecessary-revision damage controls*. They are **not 30 verified model-written failures**.

Therefore a direct A/B comparison that asks both arms simply to edit the registered source would test the **quality/risk of editing source prose**, not independently establish AI-to-Human repair.

To test the intended *humanization* capability, use **one common AI-origin starting draft per case** created by a separate, fixed baseline generator from a source-derived factual/function dossier. Admission of that starting draft requires zero unexplained substantive differences from the registered source. The exact original paragraph remains an undisclosed style/fidelity reference, **not** a text the repair writers are allowed to imitate. A source dossier may state facts/functions and direct links, not reproduce a model-shaped sentence plan that bakes in a predetermined prose architecture. Distinguish historical article authorship from the freshly created draft's generation provenance.

If a faithful baseline cannot be produced, record `BASELINE_GENERATION_FAILED` in the denominator; do not silently swap another paragraph after seeing outputs. An already Human result cannot be treated as a failure needing a repair.

## Sequence
1. **Source freeze (DONE).** `COHORT.json` holds exact paragraph, source blob, preceding/following text and literal hyperlinks. Each target was selected from a different H2 section, five per article. Original paragraph hashes were verified against the source checkout in the previous source-selection turn; the present file was re-read from the same current GitHub blobs. No conclusions rely on Pangram labels.
2. **Teaching freeze (DONE).** `TEACHING.json` holds four literal cases and one cross-article allocation per target, all with source authority and correct provenance. `MATCH-QUALITY.json` records pre-result relevance strength. There are **3 strong, 17 medium, 10 weak** matches: weak matches are not to be presented as good retrieval. Any later match improvement must be frozen *before* writer outputs and reported as a separately versioned design.
3. **Meaning/context admission (NOT INDEPENDENT).** A separate source reader verifies links, quotations, headings, antecedents, causal language, humor, protected roles and consent. Sources are not fact-checked in this step. The source author remains the authority on intended meaning.
4. **Common baseline generator (NOT RUN).** Truly separate model context creates one faithful, model-written starting draft per target, without access to the literal owner source text or prior result. Its model, prompt, seed if supported, effective generation settings, realized input/output tokens and exact hashes must be frozen. A cold fidelity check must precede revision, with all failures retained.
5. **Two truly separate writers (NOT RUN).** For the identical admitted baseline+source-function dossier, A receives no teaching examples; B receives the preassigned literal teaching evidence, except where the predeclared match-quality audit makes it inapplicable. Same model/effort/output token cap, counterbalanced call order. Each outputs one first attempt; zero adaptive retries in the primary comparison. The generator cannot be the current conversation pretending to be blind.
6. **Blind outcome review (NOT RUN).** First compare all protected meaning/functions with source gold, then have a genuinely fresh editor assess naturalness without knowing arm or Pangram result. Owner judgments supersede reviewer preference when provided. Keep changed claims, lost humor, illegitimate certainty shifts and 'unchanged' outputs in the denominator.
7. **Pangram (NOT RUN).** Only submit faithful first attempts when a detector measurement changes a decision and a trusted exact-hash cache/reservation route is available. Each API submission is 1–3 paragraphs. Record actual backend/version and window data, preserving both categorical movement and within-window changes. Do not pool uncalibrated GUI vs API numeric metrics.
8. **Analysis (NOT RUN).** The paired 30 are nested inside six article clusters written under one byline. Report author/article dependence; no 30-independent-author claim. Predeclare the primary editorial contrast and detector contrast separately, and descriptive changes by strong/medium/weak example-match strata. A no-flip does not prove a local change had no effect. Do not infer causality from retrospective examples.

## Method escalation
Earlier R17 whole-subsection generation loaded richer calibration and still produced AI-shaped marching prose. Blind repetition of that architecture is not warranted. Compare the planned **single first draft** method with at least one structurally different future option: a small fixed set of varied faithful candidates, selected by an isolated evaluator with no detector result. That option incurs more generation/review cost and may still fail; it is **not** an executed third arm.

## Current gate and next executable step
**Current evidence level:** source and teaching preparation, no measured model transfer. No new Pangram credits spent, no article edits, no false independence claim.

The next true execution step requires a distinct fresh writer and evaluator runtime, not merely calling the same informed conversation 'Arm A' and 'Arm B'. Freeze baseline prompts, setting, budget and source function dossiers there before generation, then archive exact outputs with outcome hashes and all failed/no-change controls. No background work is claimed.
