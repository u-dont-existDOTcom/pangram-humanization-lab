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

When Joel asks to **humanize**, **make it pass Pangram**, or otherwise makes Pangram success a delivery requirement, detector validation is part of the task definition, not an optional postscript.

Before rewriting, identify any **protected rhetorical functions** in the source. These are functions that must survive even when the wording changes: reader agency and permission, trauma-informed invitation, non-coercive choice, pacing around sensitive material, exact claim/certainty, severe-claim agency, lived memories, humor/idiolect, links/media, chronology, causality, and other owner-intended functions. Do not classify a function as expendable merely because its current realization resembles a known AI pattern such as generic warmth, reassurance, invitation, recap, or explanatory aftercare. Diagnose the function separately from the wording.

For trauma-informed or other sensitive writing in particular:
- **do not assume invitational language is detector-hostile; test it;**
- distinguish functional permission/choice language from empty performed coziness or generic therapeutic scaffolding;
- if the exact wording is detector-red, preserve the function and test a minimal alternative realization before deleting it;
- do not treat Pangram as a reason to soften or remove the owner's intended argument, but do treat a requested Pangram pass as a hard delivery constraint. Joel's standing acceptance target is 100% Human on the exact intended delivery boundary. Keep iterating through faithful, coherence-preserving realizations until that target is reached or the worker genuinely does not know a further faithful fix and requests narrow authorial help.

A requested humanization pass is **not complete** until all of the following are true:
1. semantic sanity, coherence, fidelity, and protected-function audits pass;
2. the exact intended delivery boundary has an actual Pangram result from the current required detector/version;
3. the result has `detector.stage == "STAGE_SUCCESS"`, `detector.version == "4.0"`, `detector.fraction_human == 1.0`, `detector.fraction_ai == 0.0`, and `detector.fraction_ai_assisted == 0.0`;
4. any detector-driven change has been re-audited for semantic and rhetorical loss;
5. the user-facing diff labels detector status only from measured results, never prediction or intuition.

A `Human` headline, `prediction_short == "Human"`, or partial score such as 93% or 99% Human is progress only. It is not a pass. This owner-specific acceptance rule supersedes general advice that tiny score differences within a Human classification need not control editorial choice.

Do not stop merely because the current candidate is the best so far. If the worker genuinely cannot identify another faithful and coherent repair, pause as an **unresolved authorial handoff** and report the exact failing span and boundary, current score and result hash, attempted approaches and their results, protected claims/functions, why no further faithful fix is known, and the narrow question or raw author input needed from Joel. Do not call the pass complete. A section/API-call budget may pause paid calls for explicit escalation, but it cannot accept a partial score or close the task; state whether a known faithful next repair remains.

Do not infer that Pangram access is unavailable merely because the current worker has no local `PANGRAM_API_KEY`, a local key is rejected, or the Pangram web dashboard is signed out. Before labeling a candidate pre-Pangram, complete the access-resolution gate in `docs/PANGRAM-ACTIONS-RUNBOOK.md`, including the repository-secret GitHub Actions route based on `automation/pangram-fixed-batch`. Never retrieve, print, commit, or ask Joel to paste the repository secret.

Only after both the direct/local route and the secret-backed Actions route are unusable may the prose be delivered as an explicitly labeled **pre-Pangram candidate**. Record the exact blocker. Never call the humanization complete, never say a version “passes,” and never substitute an internal stylistic judgment for the detector call.

When preparing a choice diff, default to the single best passing faithful version. Show multiple passing choices only when alternatives preserve different owner-valued functions, tones, claims, or tradeoffs. Do not manufacture options merely because several detector-green phrasings exist.

## Learning closeout is a completion gate

Before reporting any substantive editorial/detector/reconstruction/experiment pass complete:

1. identify each actual new finding;
2. disposition it in `state/LESSON-LEDGER.json` via the current `pangram-lesson-closeout` command;
3. use `promoted`, `provisional`, `article-specific`, `superseded`, or `no-new-lesson` as appropriate;
4. for anything promoted, update `state/LESSON-INDEX.md` and a current `state/WORKING-LESSONS*.md` summary;
5. run the repository closeout check/audit and verify it passes;
6. only then claim completion.

Read `docs/LESSON-CLOSEOUT.md` for exact commands and cross-branch handling. Do not ask Joel to remember or periodically police this process. GitHub CI and the weekly audit are the backstop.

## Paid-call safety

Before any new Pangram submission:
- inspect exact-text cache and pending task state;
- reuse completed matching results;
- resume checkpointed task IDs instead of re-POSTing;
- preserve ambiguous POST failures without automatic repost;
- preserve wrong-version/terminal raw responses as evidence;
- keep GitHub durable before another paid call.

As of the v2.0.1 repair, the proven async path uses `x-api-key`, explicit `model: "pangram-4"`, expected terminal `version: "4.0"`, task-ID checkpoint before polling, content-addressed cache reuse, and fail-closed behavior after ambiguous submit. Read current code/README before assuming this has not changed.

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

- Human editorial quality, semantic sanity and fidelity outrank Pangram as editorial authorities; when Pangram success is an explicit delivery requirement, the detector pass is nevertheless a hard acceptance gate.
- Exact submitted boundary matters; short samples are less reliable.
- Preserve nulls and counterexamples.
- Test interactions; do not infer magic words from one case.
- Pangram green does not justify stopping if a real thought thread remains.
- Pangram red does not justify worse prose or altered meaning; keep searching for a faithful passing realization rather than silently accepting semantic loss.
- Stop once the local hypothesis is adequately discriminated; avoid token hunting.

## Promotion boundary

Raw/cached detector evidence and experiment histories stay here. Promote only durable editorial lessons into the current canonical lesson summary/index, with provenance, tested boundary, what was falsified, repeats/version, and whether the finding is local or cross-case replicated. If/when the separate canonical `u-dont-existDOTcom/joel-articles` repository is available, durable article-skill lessons should also be synchronized there according to its repository map.
