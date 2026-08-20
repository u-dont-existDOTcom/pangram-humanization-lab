# ChatGPT Operating Guide — Pangram Humanization Lab

This **public** repository is the canonical detector-research store for Joel Rosenblum article humanization work. Fresh chats should inspect GitHub directly rather than asking Joel to paste logs/results already committed here.

## Start here

1. **Read `state/CURRENT-STATE.md` first** for the current repository checkpoint and detector-transport routing.
2. Read `state/LESSON-INDEX.md` for current lesson authority, evidence-branch routing, and closeout requirements.
3. Open the relevant case study, incident note, cache/result, and case history only as needed for the exact task.
4. For detector disputes or newer incidents, follow the branch/evidence instructions in current state and the lesson index rather than assuming `main` contains every raw experiment.

Current owner instructions and exact repository evidence outrank stale summaries, old branch handoffs, and historical transport runbooks.

## Current detector transports

As of 2026-08-20:

- the owner's **self-hosted Pangram API** is the normal programmatic detector route;
- `pangram-local` is the supported headed Brave/Chromium + Playwright fallback for authenticated History recovery, visual evidence, and resilience;
- GitHub-hosted Actions is a **legacy/optional** transport, not a required access fallback. A 2026-08-19 hosted-runner test produced an origin-specific HTTP 401 at the Pangram async external endpoint despite the same key working locally; see issue #95 and `docs/PANGRAM-ACTIONS-RUNBOOK.md`;
- the old remote Browserbase proposal is compatibility/history, not the primary GUI route.

Do not spend detector credits merely to re-prove infrastructure. New paid calls require an actual detector task.

## Division of labor

Joel/model does the human editorial work. The lab does repetitive detector science and evidence handling: controlled probe design, blind semantic/editorial review, Pangram submit/cache/recovery, exact repeats, interaction analysis, falsification, stopping rules, and durable GitHub evidence.

Do not send Joel through manual chains of one-off detector variants when the lab can safely automate them.

## Humanization execution and completion gate

Whenever Joel asks to humanize text, make it pass Pangram, or otherwise makes Pangram success a delivery requirement, this gate applies. Detector validation is part of the task definition rather than an optional postscript.

Before rewriting, identify protected rhetorical functions in the source: reader agency and permission, trauma-informed invitation, non-coercive choice, pacing around sensitive material, exact claim/certainty, severe-claim agency, lived memories, humor/idiolect, links/media, chronology, causality, and other owner-intended functions. Do not classify a function as expendable merely because its current wording resembles a known AI pattern.

For trauma-informed or other sensitive writing:

- do not assume invitational language is detector-hostile; test it;
- distinguish functional permission/choice language from empty performed coziness or generic therapeutic scaffolding;
- if exact wording is detector-red, preserve the function and test a minimal alternative realization before deleting it;
- never use Pangram as permission to soften or remove Joel's intended argument.

Joel's standing acceptance target for a requested Pangram pass is 100% Human on the exact intended delivery boundary unless he explicitly sets another target for the task.

A requested humanization pass is not complete until:

1. semantic sanity, coherence, fidelity, and protected-function audits pass;
2. the exact intended delivery boundary has an actual Pangram result from the required detector/version;
3. when the standing 100% gate applies, the result has `stage == STAGE_SUCCESS`, Pangram 4.0, Human fraction `1.0`, AI fraction `0.0`, and AI-assisted fraction `0.0`;
4. every detector-driven change has been re-audited for semantic/rhetorical loss;
5. user-facing detector claims come from measured results rather than prediction or intuition.

Section/window measurements are diagnostic unless that unit is the complete requested deliverable. Section results do not aggregate automatically into a whole-article pass.

### Reader-visible representation gate

Certification must use the reader-visible text surface Pangram will actually evaluate. For Markdown article work, **raw Markdown is diagnostic only** when the reader sees a different surface: strip source-only Markdown syntax and link destinations as appropriate and certify the resulting **visible plaintext**. Preserve the source representation separately, but hash and certify the exact visible boundary actually being measured.

A Human headline or partial score such as 93% or 99% Human is progress only when the task requires 100%; it is not a passing result under that gate.

A 100% Human result with semantic, rhetorical, editorial, fidelity, provenance, or article-function loss also fails.

## Detector access-resolution gate

Do not infer that Pangram is unavailable merely because a local environment variable is absent, an ordinary browser is signed out, or GitHub-hosted Actions fails.

Before labeling a candidate unmeasured or pre-Pangram:

1. freeze the exact reader-visible boundary and record its UTF-8 SHA-256;
2. inspect exact cache/result state, pending API checkpoints, local-GUI submission reservations, authenticated History recovery state, and call accounting;
3. use the self-hosted API when a programmatic result is sufficient;
4. use `pangram-local` when GUI/History recovery or visual evidence is useful;
5. consider GitHub-hosted Actions only if the task specifically needs it and its current origin/API compatibility has been verified;
6. if supported routes are genuinely unusable, record the exact blocker rather than saying only “Pangram unavailable.”

Never retrieve, print, commit, or ask Joel to paste detector secrets.

## Learning closeout is a completion gate

Before reporting any substantive editorial/detector/reconstruction/experiment pass complete:

1. identify each actual new finding;
2. ensure each new detector result is durably registered for semantic lesson review on its evidence ref;
3. disposition the finding in the canonical lesson ledger directly or through the metadata-only request path;
4. use `promoted`, `provisional`, `article-specific`, `superseded`, or `no-new-lesson` as appropriate;
5. for promoted findings, update `state/LESSON-INDEX.md` and an appropriate current `state/WORKING-LESSONS*.md` summary;
6. run the repository closeout check/audit and verify it passes;
7. only then claim completion.

The review queue stores source identity and detector triage metadata, not tested article prose. Read `docs/LESSON-CLOSEOUT.md` for exact commands and cross-branch handling. Do not ask Joel to remember or police this process manually.

## Paid-call safety and accounting

For every new humanization audit that may make paid Pangram calls, assign stable audit/boundary identities before the first submission. The historical fixed-batch budget key is `audit_id + section_id + detector model + expected version`; other transports must preserve the same principle of stable identity and durable accounting.

**Standing hard limit: at most 6 new paid Pangram submissions per section per audit** unless Joel explicitly changes that limit. A whole-article acceptance boundary counts as its own section. Splitting the same section across new batches, transports, branches, workflows, chats, or retries does not reset its budget.

Before any new paid submission:

- inspect exact-text cache and completed results;
- resume checkpointed API tasks instead of re-POSTing;
- inspect local-GUI reservations and recover from Pangram History instead of re-clicking;
- preserve ambiguous failures as potentially paid;
- preserve wrong-version/terminal raw responses as evidence;
- make the reservation/checkpoint durable before another paid action whenever the transport supports it;
- persist the completed exact result before proceeding to another input.

Count toward the paid cap every new detector submission and every ambiguous action that may have reached Pangram. Do not count exact cache hits, non-billable verification, polling, or read-only recovery of already-paid work.

Before a seventh paid submission under the standing cap, stop and request narrow help from Joel. Do not silently reset the audit identity or raise the cap.

Record per measured boundary:

- exact paid submissions;
- cache hits and pending/reservation recoveries;
- exact submitted word count and SHA-256;
- detector model/version and structured result fractions;
- result path/commit and transport provenance;
- estimated credit/cost fields only when explicitly labeled as estimates.

Code-only CI must not spend Pangram.

## Transport-specific paid-work invariants

### Self-hosted/API path

Use explicit Pangram-4 model/version gates, content-addressed caching, durable task/checkpoint identity, and fail-closed behavior after ambiguous submit. If an explicit Pangram-4 request returns another terminal detector version, archive the evidence and do not automatically buy another call.

### Local Playwright GUI

The supported GUI transport writes and persists a submission reservation before the detector click, attaches authenticated History observation before the click, exact-binds completion to the stored Pangram record, reads structured Pangram-4 `response.overall`, and blocks automatic repeat when a reservation exists without a complete result. See `docs/PANGRAM-LOCAL-PLAYWRIGHT.md`.

### GitHub-hosted Actions

Treat as optional/legacy. Read `docs/PANGRAM-ACTIONS-RUNBOOK.md` and issue #95 before intentionally selecting it. The historical fixed-batch accounting design remains useful, but the existence of a repository secret or green code-only workflow does not prove the current Pangram async endpoint accepts GitHub-hosted runner traffic.

## Choice diffs and unresolved handoff

Default to the single best passing faithful version. Show multiple measured choices only when alternatives preserve meaning but differ in owner-valued function, tone, or tradeoff.

If work reaches an operational cap or the model genuinely knows no further faithful repair, record an unresolved handoff with the exact failing boundary/hash, measured detector result, attempts, preserved claims/functions, paid-call state, and the narrow authorial input needed. Do not call that state complete or passing.

## Local runtime

For ordinary current GUI work use the repository's `pangram-local` CLI and `docs/PANGRAM-LOCAL-PLAYWRIGHT.md`.

The older adaptive harness may still live on Joel's Zorin machine under a `pangram-humanization-lab-v2` working directory and can use `./INSTALL-AND-RUN.sh` for its historical experiment workflow. Do not assume that old local path or installer determines current transport authority; read current GitHub state and CLI help first.

## Interpretation

- Human editorial quality, semantic sanity, fidelity, and article function outrank Pangram as editorial authorities; when Joel explicitly requires a detector pass, the measured gate remains a delivery constraint.
- Exact submitted boundary matters; short samples are less reliable.
- Preserve nulls and counterexamples.
- Test interactions; do not infer magic words from one case.
- Pangram green does not justify stopping if a real thought thread remains.
- Pangram red does not justify worse prose or altered meaning.
- For controlled research probes, stop once the local hypothesis is adequately discriminated; avoid token hunting. This research stopping rule never overrides paid-call safety.

## Promotion boundary

Raw/cached detector evidence and experiment histories stay here. Promote only durable editorial lessons into the current canonical lesson summary/index, with provenance, tested boundary, falsified alternatives, repeats/version, and whether the finding is local or cross-case replicated.

Article-authority and article-skill state belong in `u-dont-existDOTcom/joel-articles` according to that repository's current map. Detector harnesses, raw/cached evidence, and detector-research history remain here.
