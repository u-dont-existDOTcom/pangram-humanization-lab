# Humanization gate supplement — 2026-08-13

Read after the other current `WORKING-LESSONS*.md` summaries.

## Protected rhetorical function and detector acceptance are separate gates

When humanizing, identify the source's rhetorical functions before editing the wording. Reader agency, trauma-informed invitation, non-coercive choice, pacing around sensitive material, exact claim/certainty, lived memories, humor/idiolect, chronology, causality, and severe-claim agency can be intentional functions even when their current wording resembles familiar AI patterns.

Durable rule: **diagnose function separately from realization.** Do not delete a function merely because its current realization looks like generic warmth, reassurance, invitation, recap, or explanatory aftercare. If the realization is detector-red, search for a faithful realization that preserves the function.

Whenever Joel asks to humanize text, make it pass Pangram, or otherwise makes Pangram success a delivery requirement, this gate applies. The exact intended delivery boundary must measure 100% Human: `detector.stage == "STAGE_SUCCESS"`, `detector.version == "4.0"`, `detector.fraction_human == 1.0`, `detector.fraction_ai == 0.0`, and `detector.fraction_ai_assisted == 0.0`. A `Human` headline, `prediction_short == "Human"`, or partial score such as 93% or 99% is diagnostic progress only; it is not a pass. This owner-specific acceptance target supersedes general guidance that tiny differences inside a Human classification need not control editorial choice.

Section/window measurements are diagnostic unless that unit is the complete requested deliverable. For a full article, the complete exact article boundary must itself satisfy the gate after every accepted edit; section-level 100% results do not aggregate into an article pass.

### Certify the reader-visible representation, not source markup

The detector boundary is the **reader-visible** text Pangram will actually evaluate. For Markdown article work, **raw Markdown is diagnostic only**: strip Markdown syntax, link destinations, bullets/markup that are not visible as prose, and test the resulting **visible plaintext** for certification. For Substack, use the rendered reader-visible text, including embed/card text if Pangram surfaces it. A raw Markdown pass does not certify the rendered article.

This rule is grounded in the Spiritual Bypassing incident: the raw Markdown source measured 100% Human, while the normalized 1,482-word visible plaintext reproduced the Pangram GUI at about 88.3% Human. The detector was not meaningfully disagreeing with itself; the two tests supplied different representations. Preserve both hashes when doing representation research, but only the reader-visible one can satisfy the publication gate.

The repair task has only two terminal states: (1) the exact intended delivery boundary satisfies the 100% detector gate and all editorial/fidelity gates; or (2) the worker genuinely knows no further faithful and coherent repair and makes an unresolved authorial handoff.

A separate cost-control rule can suspend the repair before either terminal state. Each independently tested section/boundary has a hard budget of at most six **new paid Pangram POSTs per audit**. Cache hits, auth probes, polling GETs, and resuming an already-paid pending task do not count. Ambiguous POST attempts and corrective paid POSTs do count. Before a seventh paid POST for that section, stop, preserve the exact measured state, and ask Joel for narrow help. This is a mandatory operational suspension, not a detector pass or completion. Never invent a new batch, workflow, chat, or audit ID solely to reset the same section's budget.

The unresolved authorial handoff or paid-cap suspension must identify the exact failing span and measured boundary; exact `text_sha256`; `fraction_human`, `fraction_ai`, and `fraction_ai_assisted`; detector version; result path; result commit; attempted faithful approaches and their measured results; protected claims/functions; paid API calls used for that section and available estimated/reported credit usage; and the narrow help needed from Joel.

Editorial quality and fidelity remain the authority over what the prose is allowed to mean. An unmeasured or partially Human candidate is not a completed Pangram-humanization delivery. A 100% Human result with semantic, rhetorical, editorial, fidelity, or provenance loss also fails the gate.

Do not infer that Pangram access is unavailable merely because the current worker has no local `PANGRAM_API_KEY`, the local key is rejected, or the Pangram web dashboard is signed out. Before labeling a candidate pre-Pangram, complete the access-resolution gate in `docs/PANGRAM-ACTIONS-RUNBOOK.md`, including the repository-secret GitHub Actions route based on `automation/pangram-fixed-batch`. Only report access unavailable after both the direct/local route and the secret-backed Actions route are unusable, and record the exact blocker. Never retrieve, print, commit, or ask Joel to paste the repository secret.

An unmeasured candidate remains a `pre-Pangram candidate`; never report it as a completed humanization pass.

## Trauma-informed language: test, do not presume

Do not assume that invitational or trauma-informed language is detector-hostile. Test the actual full boundary.

In the Spiritual Bypassing article experiment on 2026-08-13, a full article classified `Human` while retaining situated reader-agency language, including optional source material, non-prescriptive framing around another person's experience, gentler alternatives, and `Your path is yours to shape.` The owner-selected B variant measured 93.127918% Human on Pangram 4.0. Under the standing exact-100% completion gate this is measured progress, not a detector pass. These fragments were present inside the measured full boundary; they were not independently proven causal.

Several additional opening-level permission formulations caused the same full article backbone to classify Mixed. That is article/boundary-specific interaction evidence, not a phrase blacklist and not evidence that permission language generally fails.

Durable rule: **preserve the trauma-informed function, test the realization, and interpret results at the measured boundary.** Do not predict that a category of language will fail, and do not preserve a detector-red realization merely because its function matters; find another faithful realization within the paid-call budget, then request narrow authorial help if the section cap is reached.

## Choice-diff rule

For detector-required humanization, label a version `passes` only from an actual measurement of that exact text that satisfies the standing detector gate. Default to the single best measured faithful version. Offer multiple measured choices only when they preserve meaningfully different owner-valued functions, tones, or tradeoffs. Do not generate decorative alternatives merely because several phrasings could be tested.

## Exact evidence

Current raw evidence is on branch `automation/pangram-fixed-batch`, including:

- `state/experiments/spiritual-bypassing-invitation-batch-2026-08-13-results.json`
- `state/experiments/spiritual-bypassing-r12-2026-08-13-results.json`
- `state/experiments/spiritual-bypassing-r13-interaction-2026-08-13-results.json`
- `state/experiments/spiritual-bypassing-r14-minimal-alternatives-2026-08-13-results.json`
- `state/candidates/spiritual-bypassing-owner-selected-B.json`

The detector version and exact text hashes live in those result records. Preserve the full records rather than extracting phrase rules.
<!-- closeout-request:pangram-result-path-durability-2026-08-13 -->
### Bind detector evidence to immutable experiment identity
Fixed-batch result identity must be mechanical, not a workflow naming convention. Derive the canonical result path from `experiment_id`, fingerprint the exact batch spec, reject a mismatched output path or changed-spec reuse before detector access, and allow an identical completed experiment to reuse its result without another paid call. Commit the exact result before lesson-review registration and bind the review obligation to that immutable result commit. A mutable branch plus a reusable pathname is not durable provenance.
