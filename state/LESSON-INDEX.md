# Pangram / humanization lesson index

Use this file as the starting point for current lesson retrieval.

## Required read order

1. `state/WORKING-LESSONS.md` — consolidated lessons through 2026-08-12.
2. `state/WORKING-LESSONS-SUPPLEMENT-2026-08-13.md` — newer Romance detector, semantic-sanity, architecture, routing, provenance, and large-reconstruction lessons. Newer owner correction / controlled evidence here supersedes older conflicting guidance.
3. `state/WORKING-LESSONS-SUPPLEMENT-2026-08-13-HUMANIZATION-GATE.md` — protected rhetorical function, the standing detector-acceptance gate for Joel humanization requests, trauma-informed language testing, and measured choice-diff rules.
4. `state/WORKING-LESSONS-SUPPLEMENT-2026-08-15.md` — current Romance owner corrections on source-vs-interpretation provenance, conversational speakability, stopping points, and the clipped affirmative-then-reversal hard byline ban.
5. `state/ROMANCE-OWNER-STYLE-BAN-FRAGMENT-REVERSAL-2026-08-15.md` — exact source/scope for the direct Joel hard ban on generated `X. Not really/not quite/not exactly Y.` cadence; owner preference, not Pangram evidence.
6. `state/ROMANCE-OPENING-PERSONAL-PROVENANCE-2026-08-15.md` — current owner-final Romance opening plus owner-reported HIGH→MEDIUM detector controls when explicit personal/source provenance is removed; treat as a rhetorical-function/provenance hypothesis, not a `my` lexical rule.
7. `docs/CHATGPT-OPERATING-GUIDE.md` — current execution/completion contract, including the six-paid-call per-section cap and durable lesson-review fallback.
8. For exact evidence behind a lesson, inspect the cited incident note and experiment/result JSON rather than generalizing from the summary.

## Pangram execution/access gate

For every task that requires a measured Pangram result, read `docs/PANGRAM-ACTIONS-RUNBOOK.md` before deciding whether detector access exists. Missing local environment credentials and a signed-out browser session do not establish unavailability. The canonical fallback uses the repository Actions secret through the proven fixed-batch path on `automation/pangram-fixed-batch`.

For every new paid audit, also follow `docs/CHATGPT-OPERATING-GUIDE.md` and the current `docs/PANGRAM-SECTION-CALL-BUDGET.md` on `automation/pangram-fixed-batch`. The hard budget is six new paid Pangram POSTs per independently tested section per audit. Cache hits, auth probes, polling, and pending-task resumes are free for budget purposes. Before a seventh paid POST, stop and request narrow help from Joel; do not reset the budget by inventing a new batch, chat, or audit ID.

A worker may use the label `pre-Pangram candidate` only after the runbook's local and GitHub routes have both failed with a recorded blocker. The repository secret remains inside Actions; never retrieve, reveal, print, commit, or ask Joel to paste it.

Whenever Joel asks to humanize text, make it pass Pangram, or otherwise makes Pangram success a delivery requirement, this gate applies. Joel's standing completion target is 100% Human on the exact intended delivery boundary: `detector.stage == "STAGE_SUCCESS"`, `detector.version == "4.0"`, `detector.fraction_human == 1.0`, `detector.fraction_ai == 0.0`, and `detector.fraction_ai_assisted == 0.0`. A Human headline or a partial score such as 93% is progress only; it is not a pass.

Section/window measurements are diagnostic unless that unit is the complete requested deliverable. For a full article, the complete exact article boundary must itself satisfy the gate after every accepted edit; section-level 100% results do not aggregate into an article pass.

The normal editorial terminal states are: (1) the exact intended delivery boundary satisfies the 100% detector gate and all editorial/fidelity gates; or (2) the worker genuinely knows no further faithful and coherent repair and makes an unresolved authorial handoff. The six-paid-call section cap creates a mandatory operational suspension even if another faithful repair may exist: stop before the seventh paid POST, preserve the measured state, and ask Joel for narrow help. A budget suspension is not a detector pass and is not completion. The handoff must identify the exact span and boundary; exact `text_sha256`; `fraction_human`, `fraction_ai`, and `fraction_ai_assisted`; detector version; result path; result commit; attempts and measured results; protected claims/functions; and the narrow help needed from Joel. A 100% Human result with semantic, rhetorical, editorial, fidelity, or provenance loss also fails the gate.

## Completion gate

Before reporting any substantive editorial, detector, reconstruction, or experiment pass complete, use `docs/LESSON-CLOSEOUT.md` and the canonical `state/LESSON-LEDGER.json`.

Every new detector result must also be durably registered for semantic review. The current fixed-batch runner writes metadata-only source identity and detector triage into `state/LESSON-INBOX.json` on the evidence ref. A queue item remains unresolved until `main` contains a ledger disposition matching the same source path, source ref, and exact SHA-256.

Every substantive finding must be dispositioned as `promoted`, `provisional`, `article-specific`, `superseded`, or `no-new-lesson`. Promoted findings must update this index plus the current lesson summary. If a direct ledger write is blocked, use the metadata-only `state/lesson-closeout-requests/` route processed by the trusted `lesson-integrity.yml` Action. Run the repository lesson-closeout gate before claiming completion. Do not ask Joel to remind you.

## Important branch note

The default `main` branch contains the canonical lesson summaries above, but many of the newest exact incident notes and Pangram-4 experiment/result files currently live on branch:

`automation/pangram-fixed-batch`

A worker that reads only the default branch will therefore have the current promoted lessons but not all exact experimental evidence. For detector work or disputed findings, explicitly inspect that branch.

Key current evidence on `automation/pangram-fixed-batch` includes:

- `state/HISTORICAL-WHITESPACE-AUDIT-2026-08-12.md`
- `state/PANGRAM-WHITESPACE-SENSITIVITY-2026-08-12.md`
- `state/ROMANCE-OXYTOCIN-LOGIC-REPAIR-2026-08-12.md`
- `state/ROMANCE-IDEALIZATION-INCIDENT-2026-08-12.md`
- `state/ROMANCE-PROGRESS-SIGNALS-INCIDENT-2026-08-13.md`
- `state/ROMANCE-DOCTOR-PATIENT-REPAIR-2026-08-13.md`
- `state/ROMANCE-MONOGAMY-POLYAMORY-INCIDENT-2026-08-13.md`
- `state/ROMANCE-ARTIFICIAL-CHECKLIST-INCIDENT-2026-08-13.md`
- `notes/romance-recap-removal-routing-2026-08-13.md`
- `state/experiments/spiritual-bypassing-invitation-batch-2026-08-13-results.json`
- `state/experiments/spiritual-bypassing-r12-2026-08-13-results.json`
- `state/experiments/spiritual-bypassing-r13-interaction-2026-08-13-results.json`
- `state/experiments/spiritual-bypassing-r14-minimal-alternatives-2026-08-13-results.json`
- exact result JSON under `state/experiments/`

## Authority order

For lesson application:

1. current Joel owner correction / owner-final prose
2. current project edit contract and authoritative article baseline
3. newer controlled experiment with exact boundary/provenance
4. promoted current lesson summaries
5. older incident notes / historical detector outcomes
6. synthetic probes

Detector status is never authorship provenance. Pangram green does not certify natural owner authorship, and Pangram red does not override coherent faithful prose. For every Joel humanization request covered by the standing gate above, the exact intended delivery boundary must actually pass before the humanization task is called complete; a paid-cap suspension remains explicitly unresolved.

## Scope

Do not load every historical experiment indiscriminately. Start with the current lesson summaries and operating guide, then open exact evidence only where the current task needs it.
<!-- closeout-request:spiritual-bypassing-r4-authorial-mechanism -->
- **Authorial mechanism recovery:** if bounded repair stalls on an abstraction, ask for the smallest piece of lived authorial mechanism before further paraphrase; materially new owner input is new semantic evidence and should be tested directly. See `state/WORKING-LESSONS-SUPPLEMENT-2026-08-13.md`.
<!-- closeout-request:spiritual-bypassing-r6-closeout -->
- **Owner-authority rollback after a detector pass:** after reaching the detector gate, restore higher-authority owner prose as far as possible; if the exact rollback breaks the measured boundary, localize and minimally repair rather than retaining a broader model rewrite. See `state/WORKING-LESSONS-SUPPLEMENT-2026-08-13.md`.
<!-- closeout-request:pangram-result-path-durability-2026-08-13 -->
- **Immutable detector-result identity:** fixed-batch results are derived from `experiment_id`, spec-fingerprinted, fail closed on path/spec reuse conflicts before detector access, and lesson-review registration points to the immutable result commit. See the humanization-gate supplement.
<!-- closeout-request:romance-authorial-sufficiency-call-efficiency-2026-08-13 -->
- **Authorial sufficiency / call efficiency:** before repeated detector paraphrases, recover the governing thought from article-wide evidence or request the smallest missing lived mechanism. Show the complete failing span and function ledger, bank valuable non-fitting owner ideas with named destinations, require every paid call to change the next decision, and reserve the fresh exact full-boundary measurement for final certification where possible. See `state/ROMANCE-AUTHORIAL-SUFFICIENCY-CALL-EFFICIENCY-2026-08-13.md`.
<!-- closeout-request:romance-owner-final-survival-2026-08-14 -->
- **Owner-final survival / settled-review lock:** a rolling destination ledger preserves genuinely extra material; it cannot bank away a still-relevant owner-final point. Preserve its current destination unless Joel approves a concrete move, and do not reopen a review he says is settled without materially new contradictory evidence, ambiguity, or his request. See `state/ROMANCE-AUTHORIAL-SUFFICIENCY-CALL-EFFICIENCY-2026-08-13.md`.
<!-- closeout-request:spiritual-bypassing-visible-boundary-2026-08-14 -->
- **Reader-visible detector boundary:** certify the reader-visible text Pangram evaluates, not source markup. Raw Markdown is diagnostic only; strip it to visible plaintext before certification, and for Substack use the rendered reader-visible text surface including surfaced card/embed text.
<!-- closeout-request:spiritual-bypassing-humanization-architecture-2026-08-14 -->
- **Humanization architecture regression:** before detector work and **after every detector-driven edit**, recheck the **heading promise**, **paragraph jobs**, reader's **live question**, **article-wide** duplication/placement, protected functions, fidelity, and whether an existing **owner realization** belongs in the section. A **100% Human** detector result is not acceptable when this architecture regression fails. See `docs/HUMANIZATION-ARCHITECTURE-REGRESSION.md`.
<!-- owner-style-ban:fragment-reversal-2026-08-15 -->
- **Joel byline hard ban — clipped reversal cadence:** do not generate `X. Not really/not quite/not exactly Y.` or close affirmative-beat-then-corrective-fragment variants. Express the actual relation between the thoughts in ordinary syntax. This is direct owner preference, not Pangram evidence. See `state/ROMANCE-OWNER-STYLE-BAN-FRAGMENT-REVERSAL-2026-08-15.md`.
<!-- romance-opening-personal-provenance-2026-08-15 -->
- **Personal provenance can be a real rhetorical function:** in Joel's owner-reported Romance opening controls, removing the clause grounding the guide in his particular life experience/friends/research changed HIGH-confidence Human to MEDIUM; a shorter control stayed HIGH with `my experience` and moved to MEDIUM when only `my` was removed. Treat this as evidence that explicit source-of-knowledge can turn a generic scope disclaimer into lived positioning in the exact boundary—not as a `my` token rule. See `state/ROMANCE-OPENING-PERSONAL-PROVENANCE-2026-08-15.md`.
<!-- closeout-request:romance-talk-old-green-control-2026-08-15 -->
- **Historical detector-result reproducibility:** an old `Human/high` label is not a current control unless the exact intended boundary and detector provenance reproduce. If the old control itself changes under the current detector, stop attributing the regression to the newer edit; preserve the discrepancy and return to editorial/owner authority. See `state/WORKING-LESSONS-SUPPLEMENT-2026-08-15.md`.
<!-- closeout-request:idiolect-retention-research-integration-2026-08-17 -->
- **Authorship-signal retention / edit-dose gate:** after the existing working supplements, read `state/WORKING-LESSONS-SUPPLEMENT-2026-08-17-IDIOLECT-RETENTION.md` and use `docs/IDIOLECT-RETENTION-PROTOCOL.md` for substantial AI-mediated rewrites. A voice-preservation prompt is not evidence; semantic fidelity, Pangram status, and authorship retention remain separate results.
<!-- closeout-request:romance-half-split-sensitivity-20260822 -->
- **Long-document split sensitivity:** changing only a detector half/document boundary can create far-downstream AI windows in byte-identical prose that previously measured Human. Compare exact prior-boundary evidence before rewriting newly red remote passages and keep segmentation stable for controlled prose comparisons. See `state/WORKING-LESSONS-SUPPLEMENT-2026-08-22.md` and `state/ROMANCE-HALF-SPLIT-REMOTE-SENSITIVITY-2026-08-22.md`.
