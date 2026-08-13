# ChatGPT Operating Guide — Pangram Humanization Lab

This private repository is the canonical detector-research store for Joel Rosenblum article humanization work. Fresh chats should inspect GitHub directly rather than asking Joel to paste logs/results already committed here.

## Start here

**Always begin with `state/LESSON-INDEX.md`.** It is the canonical retrieval entry point and controls the current lesson read order, authority order, branch-specific evidence routing, and the lesson-closeout requirement. Do not hard-code an older lesson sequence from memory.

After the index directs you:
1. read the current promoted lesson summaries it names;
2. open the relevant case-study / incident note under `state/` only as needed;
3. inspect the relevant `cases/<case-id>/history.json` and round `plan.json`, `review.json`, `stats.json` when interpretation depends on exact experimental evidence;
4. for detector disputes or newer incidents, follow the branch instructions in `state/LESSON-INDEX.md` and inspect the cited branch rather than assuming `main` contains every raw experiment.

If the case ID is unknown, inspect recent commits for `state: rXX analysis` / `state: rXX deterministic stats` and open the changed case path.

## Division of labor

Joel/model does the human editorial work. The lab does repetitive detector science: controlled probe design, blind semantic/editorial review, Pangram submit/cache/poll, preregistered exact repeats, interaction analysis, falsification, stopping rule, and durable GitHub evidence.

Do not send Joel through manual chains of one-off detector variants when the lab can run them.

## Humanization execution and completion gate

Whenever Joel asks to humanize text, make it pass Pangram, or otherwise makes Pangram success a delivery requirement, this gate applies. Detector validation is part of the task definition, not an optional postscript.

Before rewriting, identify any **protected rhetorical functions** in the source. These are functions that must survive even when the wording changes: reader agency and permission, trauma-informed invitation, non-coercive choice, pacing around sensitive material, exact claim/certainty, severe-claim agency, lived memories, humor/idiolect, links/media, chronology, causality, and other owner-intended functions. Do not classify a function as expendable merely because its current realization resembles a known AI pattern such as generic warmth, reassurance, invitation, recap, or explanatory aftercare. Diagnose the function separately from the wording.

For trauma-informed or other sensitive writing in particular:
- **do not assume invitational language is detector-hostile; test it;**
- distinguish functional permission/choice language from empty performed coziness or generic therapeutic scaffolding;
- if the exact wording is detector-red, preserve the function and test a minimal alternative realization before deleting it;
- do not treat Pangram as a reason to soften or remove the owner's intended argument, but do treat a requested Pangram pass as a hard delivery constraint. Joel's standing acceptance target is 100% Human on the exact intended delivery boundary. Keep iterating through faithful, coherence-preserving realizations until that target is reached or the current section reaches its paid-call cap and requires narrow authorial help.

A requested humanization pass is **not complete** until all of the following are true:
1. semantic sanity, coherence, fidelity, and protected-function audits pass;
2. the exact intended delivery boundary has an actual Pangram result from the current required detector/version;
3. the result has `detector.stage == "STAGE_SUCCESS"`, `detector.version == "4.0"`, `detector.fraction_human == 1.0`, `detector.fraction_ai == 0.0`, and `detector.fraction_ai_assisted == 0.0`;
4. any detector-driven change has been re-audited for semantic and rhetorical loss;
5. the user-facing diff labels detector status only from measured results, never prediction or intuition.

Section/window measurements are diagnostic unless that unit is the complete requested deliverable. For a full article, the complete exact article boundary must itself satisfy the gate after every accepted edit; section-level 100% results do not aggregate into an article pass.

A `Human` headline, `prediction_short == "Human"`, or partial score such as 93% or 99% Human is progress only. It is not a pass. This owner-specific acceptance rule supersedes general advice that tiny score differences within a Human classification need not control editorial choice.

The repair task normally has two editorial terminal states: (1) the exact intended delivery boundary satisfies the 100% detector gate and all editorial/fidelity gates; or (2) the worker genuinely knows no further faithful and coherent repair and makes an **unresolved authorial handoff**. A section reaching its six-paid-call budget creates an additional mandatory **operational suspension**: stop before a seventh paid POST and ask Joel for narrow help on that section. This suspension is not a detector pass and is not completion. It is required even if another faithful repair might exist, because Joel explicitly set the spending cap. After Joel supplies materially new authorial guidance or explicitly starts a new audit, the work may resume under the new audit budget; never invent a new audit ID merely to buy more attempts.

An unresolved authorial handoff or paid-cap suspension must report the exact failing span and measured boundary; exact `text_sha256`; `fraction_human`, `fraction_ai`, and `fraction_ai_assisted`; detector version; result path; result commit; attempted faithful approaches and their measured results; protected claims/functions; and the narrow question or raw author input needed from Joel. Do not call that state complete or passing.

A 100% Human result with semantic, rhetorical, editorial, fidelity, or provenance loss also fails the gate.

Do not infer that Pangram access is unavailable merely because the current worker has no local `PANGRAM_API_KEY`, a local key is rejected, or the Pangram web dashboard is signed out. Before labeling a candidate pre-Pangram, complete the access-resolution gate in `docs/PANGRAM-ACTIONS-RUNBOOK.md`, including the repository-secret GitHub Actions route based on `automation/pangram-fixed-batch`. Never retrieve, print, commit, or ask Joel to paste the repository secret.

Only after both the direct/local route and the secret-backed Actions route are unusable may the prose be delivered as an explicitly labeled **pre-Pangram candidate**. Record the exact blocker. Never call the humanization complete, never say a version “passes,” and never substitute an internal stylistic judgment for the detector call.

When preparing a choice diff, default to the single best passing faithful version. Show multiple measured choices only when alternatives preserve different owner-valued functions, tones, claims, or tradeoffs. Do not manufacture options merely because several detector-green phrasings exist. If a choice is below the standing 100% gate, label its measured score precisely rather than calling it a pass.

## Learning closeout is a completion gate

Before reporting any substantive editorial/detector/reconstruction/experiment pass complete:

1. identify each actual new finding;
2. ensure every new detector result has been durably registered in the metadata-only `state/LESSON-INBOX.json` review queue on its evidence ref;
3. disposition it in the canonical `state/LESSON-LEDGER.json`, directly or through a metadata-only request in `state/lesson-closeout-requests/`;
4. use `promoted`, `provisional`, `article-specific`, `superseded`, or `no-new-lesson` as appropriate;
5. for anything promoted, update `state/LESSON-INDEX.md` and a current `state/WORKING-LESSONS*.md` summary;
6. run the repository closeout check/audit and verify it passes;
7. only then claim completion.

The review queue stores source identity and detector triage metadata, not tested article prose. If a direct chat-side ledger write is blocked by the connector safety classifier, the existing trusted `lesson-integrity.yml` workflow processes the small metadata-only closeout request on `main`. If even that request cannot be written, leave the queue item pending and report the unresolved durable obligation rather than silently losing it.

Read `docs/LESSON-CLOSEOUT.md` for exact commands and cross-branch handling. Do not ask Joel to remember or periodically police this process. GitHub CI and the weekly audit are the backstop.

## Paid-call safety and accounting

For every new humanization audit that may make paid Pangram calls, assign a stable `audit_id`, and give each independently tested boundary a stable `section_id`. The budget key is `audit_id + section_id + detector model + expected version`.

**Hard limit: at most 6 new paid Pangram POSTs per section per audit.** A whole-article acceptance boundary counts as its own section. Splitting the same section across new batches, workflows, chats, or retries does not reset its budget. Never create a fresh audit ID solely to bypass the cap.

Before any new Pangram submission:
- inspect exact-text cache and pending task state;
- reuse completed matching results;
- resume checkpointed task IDs instead of re-POSTing;
- preserve ambiguous POST failures without automatic repost;
- preserve wrong-version/terminal raw responses as evidence;
- keep GitHub durable before another paid call.

Count toward the six-call section cap:
- every new detector POST;
- an ambiguous POST attempt that may have reached Pangram;
- a corrective paid POST after a preserved wrong-version task.

Do not count toward the cap:
- content-addressed cache hits;
- authentication probes;
- polling GETs;
- resuming an already-paid pending task.

Before the seventh paid POST, the runner must fail closed, write `state/handoffs/pangram/<audit_id>-<section_id>.json`, and request narrow help from Joel. Do not silently raise the cap.

Every audited result must report, per section:
- exact `paid_api_calls`;
- `cache_hits` and `pending_resumes`;
- `estimated_credits` and `estimated_cost_usd` when the API does not expose authoritative billing metadata;
- `paid_calls_to_human`, `estimated_credits_to_human`, and the first Human measurement key when applicable.

The optimization target is not merely staying under six. Track calls-to-Human and estimated credits-to-Human across audits so the median paid detector cost per successful section can be monitored. Promoted lessons should drive those numbers down over time.

Code-only CI must not spend Pangram. The proven automation workflow separates regression tests from explicit detector execution; detector jobs should run only for an intentional experiment input/dispatch.

As of the current tracked-client repair, the proven async path uses `x-api-key`, explicit `model: "pangram-4"`, expected terminal `version: "4.0"`, task-ID checkpoint before polling, content-addressed cache reuse, fail-closed behavior after ambiguous submit, persistent per-section call accounting, and pre-POST Git sync of the call reservation. Read current code/README before assuming this has not changed.

## Local runtime

Normal location on Joel's Zorin machine:

`~/Téléchargements/pangram-humanization-lab-v2`

Typical update/resume:

```bash
cd ~/Téléchargements/pangram-humanization-lab-v2
git pull --ff-only
./INSTALL-AND-RUN.sh
```

For new endpoint pairs, use the current repo README/CLI help rather than an old remembered invocation.

## Interpretation

- Human editorial quality, semantic sanity and fidelity outrank Pangram as editorial authorities; for every Joel humanization request covered by the standing gate above, the detector pass is nevertheless a hard acceptance gate.
- Exact submitted boundary matters; short samples are less reliable.
- Preserve nulls and counterexamples.
- Test interactions; do not infer magic words from one case.
- Pangram green does not justify stopping if a real thought thread remains.
- Pangram red does not justify worse prose or altered meaning; keep searching for a faithful passing realization within the paid section budget.
- For controlled research probes, stop once the local hypothesis is adequately discriminated; avoid token hunting. This research stopping rule never overrides the six-paid-call section cap.

## Promotion boundary

Raw/cached detector evidence and experiment histories stay here. Promote only durable editorial lessons into the current canonical lesson summary/index, with provenance, tested boundary, what was falsified, repeats/version, and whether the finding is local or cross-case replicated. If/when the separate canonical `u-dont-existDOTcom/joel-articles` repository is available, durable article-skill lessons should also be synchronized there according to its repository map.
