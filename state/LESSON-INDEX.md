# Pangram / humanization lesson index

Use this file as the starting point for current lesson retrieval.

## Required read order

1. `state/WORKING-LESSONS.md` — consolidated lessons through 2026-08-12, plus promoted cross-cutting additions appended as they are learned.
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
<!-- closeout-request:pangram-async-api-history-boundary-2026-08-22 -->
<!-- closeout-request:pangram-async-api-history-boundary-2026-08-22 -->
- **Async API History boundary:** do not clear an ambiguous async Pangram API reservation from web-History absence. First prove a known-success control from the same transport/configuration is recoverable there; the current async route failed that control, so resolve repeats from task-id/cache/ledger or other transport-appropriate exact evidence. See `state/PANGRAM-ASYNC-API-HISTORY-BOUNDARY-2026-08-22.md`.
<!-- closeout-request:owner-language-handoff-context-20260822 -->
- **Owner-language handoff context:** when asking for fresh owner prose, translate internal detector/preservation state back into the reader-visible article sequence: exact heading, placement, immediate before/after paragraph jobs, requested thought, and untouched neighboring functions. Do not hand the owner an internal label like `Talk — 112 words` and expect them to reconstruct the section. See `state/OWNER-LANGUAGE-HANDOFF-CONTEXT-2026-08-22.md`.
<!-- closeout-request:production-humanization-preflight-20260823 -->
- **Production humanization preflight / research-mode separation:** before spending a production Pangram call, diagnose and coherently repair all credible model-shaped features in the natural boundary, then repeat unpaid cold AI-shape audits until no substantive AI-looking problem remains that the editor actually believes. Use paid Pangram primarily to validate a fully considered candidate. Reserve one-variable/minimal-pair/factorial testing for explicit detector research or a genuinely narrow decision-changing uncertainty. See `state/PRODUCTION-HUMANIZATION-PREFLIGHT-VS-DETECTOR-RESEARCH-2026-08-23.md` and `state/WORKING-LESSONS-SUPPLEMENT-2026-08-22.md`.
<!-- closeout-request:somatic-r04-job2-end-model-only-stop-20260824 -->
- **Replicated model-only regeneration stop rule:** if two materially different, preservation-clean holistic production rewrites of the same large natural boundary both remain Pangram AI 1.0 / High confidence across the full boundary, stop broad model-generated author-imitation variants. Require fresh owner language or an independently human same-content realization before further detector-driven rewriting; otherwise leave detector certification unresolved rather than manufacturing pseudo-owner prose. See `state/WORKING-LESSONS-SUPPLEMENT-2026-08-22.md`.
<!-- closeout-request:somatic-r07b-contextual-owner-window-20260824 -->
- **Contextual AI-window / owner-prose protection:** a long Pangram AI window may contain near-direct current owner prose while adjacent owner passages in the same exact boundary classify Human. Do not treat every sentence in a red window as causal or authorize rewriting higher-authority owner wording because of window color; use the window as contextual/distributed localization evidence and require an independent editorial/factual reason or genuinely new owner realization before changing protected prose. See `state/WORKING-LESSONS-SUPPLEMENT-2026-08-22.md`.
<!-- closeout-request:romance-architecture-exposes-masked-ai-20260826 -->
- **Architecture can expose previously masked AI-shaped prose:** when a stronger reorganization makes a formerly Human-scoring span turn red, test two hypotheses rather than defaulting to boundary sensitivity: detector composition effects versus a genuinely weak passage that the old boundary masked. Prior Human status is not immunity. If the new architecture is independently better and the exposed span also fails a cold editorial read, keep the better architecture and repair the local prose. Romance 2026-08-26 supplied the direct case: rolling back the merge would have preserved worse architecture; minimally rewriting the exposed tail preserved the stronger structure and restored the detector pass. See the appended `Architecture can expose previously masked AI-shaped prose` section in `state/WORKING-LESSONS.md`.
<!-- closeout-request:romance-r7-minimum-dose-owner-rollback-20260827 -->

<!-- closeout-request:romance-r7-minimum-dose-owner-rollback-20260827 -->
- **Structural approval ≠ wording approval:** after an assistant move/consolidation/deletion/compression is owner-approved, humanize only the surviving assistant realization; preserve untouched owner prose and prefer minimum-dose rollback to actual owner language over fresh imitation. Romance R7 supplies owner-reported Human/high exact-candidate evidence without implying phrase causality. See `state/ROMANCE-R7-MINIMUM-DOSE-OWNER-ROLLBACK-2026-08-27.md`.
<!-- closeout-request:human-to-ai-minimal-pairs-20260828 -->
- **Stacked editorial closure / feature interactions:** isolated completion, sentence equalization, taxonomy closure, bridging, compression, or relationship language may remain Human while combinations cross Pangram's boundary. In the controlled 2026-08-28 packet, compact Somatic compression + polished cross-domain synthesis was AI `1.0` in two alternate realizations; a long conversational taxonomy + polished bridge became Mixed while colloquializing either component restored Human. Diagnose complete operation packages and boundaries, preserve owner source, and do not create phrase blacklists. See `state/experiments/human-to-ai-minimal-pairs-20260828/LESSONS.md` and the appended section in `state/WORKING-LESSONS.md`.

<!-- closeout-request:local-saturation-not-global-dead-end-20260919 -->
- **Local saturation ≠ global humanization dead end:** an all-red target only falsifies the tested target + generator/representation family. Compare against durable recent successes before escalating globally. When no green island exists, use progressive forward construction to earn a stable prefix, then return to the proven red-region convergence controller. See `state/generation/LOCAL-SATURATION-NOT-GLOBAL-DEAD-END-20260919.md`.

<!-- closeout-request:inner-child-episode008-railway-p3-saturation-20260919 -->
- **Railway Agent P3 target saturation:** on Inner Child Episode 008 P3, 20 owner-authorized Railway generations produced seven structurally varied detector-worthy candidates; all seven measured Pangram 4.0 AI 1.0 with exact History binding. Stop this Railway target lane at the 20-generation bound; do not generalize to other Railway targets. See `state/generation/INNER-CHILD-EPISODE008-RAILWAY-P3-SATURATION-20260919.md`.

<!-- closeout-request:inner-child-checking-owner-derived-tell-ledger-20260921 -->
- **Relational generation vs post-generation tell repair:** do not preassign one sentence per protected function. Generate from a shared thought/scene, then apply the Human-facing tell catalog to the literal prose and execute the tell repairs. Inner Child checking P3 provides Pangram-Human production evidence for owner-derived substrate + tell repair at 86/167/318-word boundaries, while fresh autonomous relational-thought generation on the same target remained Pangram AI 1.0. Treat this as post-generation repair evidence, not autonomous-transfer skill. See `state/generation/INNER-CHILD-CHECKING-OWNER-DERIVED-TELL-LEDGER-RESULT-20260921.md` and `state/generation/HUMAN-FACING-TELL-CONSTRUCTION-LIBRARY-v1-20260920.md`.


<!-- closeout-request:inner-child-checking-tell-clean-counterexample-20260921 -->
- **SUPERSEDED — RT2 did not establish tell-clean ≠ detector-clean:** owner re-audit found obvious surviving AI-shaped operations, so the tell-clean premise was false. Do not use RT2 as proof that the current catalog is incomplete. Retain only the narrower rule that critic non-detection is not proof of absence. See `state/generation/INNER-CHILD-CHECKING-RT2-RETROSPECTIVE-TELL-LEDGER-20260921.md`.


<!-- closeout-request:inner-child-rt2-scene-skinned-staircase-20260921 -->
- **Scene-skinned staircase:** a coherent concrete scenario can still preserve the same one-function-per-beat AI topology. Audit paragraph-level source-function order, fake spontaneity, interchangeable didactic props, and image→aftercare before calling prose tell-clean. The RT2 control no longer establishes catalog incompleteness because its tell-clean premise was false. See `state/generation/INNER-CHILD-CHECKING-RT2-RETROSPECTIVE-TELL-LEDGER-20260921.md`.

<!-- closeout-request:inner-child-safety-fresh-critic-false-pass-20260922 -->
- **Freshness ≠ critic competence:** before a fresh critic's non-detection can gate Joel production Pangram work, give it the natural reading boundary plus intended reader/local purpose, aggregate mixed findings, keep protected cognition separate from realization, and require blind same-register known-good **and** known-bad calibration. Known-good acceptance alone tests specificity, not sensitivity. See `state/generation/INNER-CHILD-SAFETY-FRESH-CRITIC-FALSE-PASS-20260922.md`.


<!-- closeout-request:humanization-critic-provenance-benchmark-v1-20260922 -->
- **SUPERSEDED — global Human/AI critic calibration:** the 20/20 hidden-authorship idea is no longer the production target. Abstract v1 scored 14/20, hard-veto v2 10/20, seven-pair absolute contrastive holdout v3 10/20 after 11/12 development, and matched pairwise realization-defect choice 5/8. Stop the global-judge family rather than adding more examples/rules. See `state/generation/critic-benchmark-20260922/V1-RESULT-AND-RUBRIC-DIAGNOSIS.md`, `state/generation/critic-holdout-v2-20260922/RESULT-AND-METHOD-DIAGNOSIS.md`, `state/generation/critic-holdout-v3-20260923/RESULT-AND-TARGET-CORRECTION.md`, and `state/generation/critic-pairwise-dev-20260923/PAIRWISE8-RESULT.md`.

<!-- closeout-request:humanization-specialized-defect-audits-20260923 -->
- **Specialized defect audits, not global authorship verdicts:** decompose unpaid pre-Pangram review into narrow observable axes. Current GPT-6 Sol controls reproduce the dangerous-adult owner corrections at 10/10 across reader-purpose (2/2), instruction-manual/listicle cadence (4/4), and corrected antecedent/referent coherence (4/4). Calibrate each axis on positive/negative controls for that exact defect; a failed axis auditor is non-gating, a narrow FAIL is a repair candidate rather than proof of AI authorship, and absence of FAILs still requires direct editorial reading. See `state/generation/specialized-audit-dev-20260923/SPECIALIZED-AUDIT-RESULT.md`.


<!-- closeout-request:global-tell-opus55-vs-gpt6-20260923 -->
- **Global tell sweep — Opus 5.5 vs GPT-6 Sol:** two direct OpenRouter repeats on the same frozen six-case / 12-cell benchmark produced Opus 5.5 **17/24 exact, 0 wrong polarity, 7 UNCERTAIN, 11/12 status-repeatability** versus GPT-6 Sol **13/24 exact, 9 wrong polarity, 2 UNCERTAIN, 8/12 status-repeatability**. Use Opus as the current preferred fresh full-catalog sweep when available, but treat UNCERTAIN as unresolved and resolve with narrow audit/editorial review. This supplements rather than replaces the full tell ledger. See `state/generation/global-tell-model-comparison-20260923/RESULT.md` and `state/generation/global-tell-model-comparison-20260923/REPEATABILITY.md`.

<!-- closeout-request:global-tell-max-effort-20260923 -->
- **Max-effort global tell sweep — default superseded by effort ladder:** same frozen six-case / 12-cell benchmark, unchanged tell definitions: Opus 5.5 max **11/12 exact, 0 wrong polarity, 1 UNCERTAIN**; GPT-6 Sol max via Venice **8/12, 3 wrong polarity**; GPT-6 Astra max via Venice **7/12, 4 wrong polarity**. Preserve the current tell catalog for now. Later effort-ladder evidence makes OpenRouter Opus xhigh the routine **API-fallback** high-rigor default and max an escalation path; it does not establish Claude Code CLI effort routing. See `state/generation/global-tell-model-comparison-20260923/MAX-EFFORT-RESULT.md` and `state/generation/global-tell-model-comparison-20260923/OPUS-EFFORT-LADDER-RESULT.md`.


<!-- closeout-request:global-tell-jev-20260923 -->
- **Jev typed tell ledger:** TypeSafe Jev 1.13 scored **9/12 exact** on the same six-case / twelve-cell owner-grounded tell benchmark at about **$0.00073 total**, but made three confident false-ABSENT calls. Use Jev only as optional cheap positive triage/advisory: PRESENT can prioritize inspection; ABSENT cannot clear a tell. See `state/generation/global-tell-model-comparison-20260923/JEV-RESULT.md`.


<!-- closeout-request:global-tell-calibration-coverage-20260923 -->
- **Tell-level calibration coverage:** current scored evidence is uneven: T02 has strong two-sided owner/editorial controls; T03–T09 are positive-only; T01 and T10–T12 are unscored. Opus 5.5 max reaching 11/12 on existing grounded cells argues against wholesale tell rewrites. Expand two-sided controls tell-by-tell first; revise a definition only after repeated max-effort errors persist with good positive/negative controls for that exact tell. See `state/generation/GLOBAL-TELL-CALIBRATION-COVERAGE-20260923.md`.

<!-- closeout-request:global-tell-opus-effort-ladder-20260923 -->
- **OpenRouter Opus reasoning-effort ladder:** same frozen six-case / 12-cell benchmark with unchanged tell definitions: low 7/12, medium 9/12, high 8/12, xhigh 11/12 then 10/12, max 11/12; the preserved Opus runs all stayed at zero wrong-polarity calls. For the **OpenRouter API fallback route**, use Opus 5.5 xhigh as the routine high-rigor full-ledger sweep and reserve max for decision-changing unresolved/disputed tells. This does not establish the Claude Code subscription CLI effort setting; recalibrate separately once CLI auth is available. The next bottleneck is tell-level calibration coverage, not a wholesale definition rewrite. See `state/generation/global-tell-model-comparison-20260923/OPUS-EFFORT-LADDER-RESULT.md`.
