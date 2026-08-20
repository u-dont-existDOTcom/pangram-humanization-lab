# Pangram Humanization Lab current state

Updated: 2026-08-20

## Goal

Preserve exact Pangram detector evidence, editorial authority, lesson closeout, and paid-call safety while supporting two independent detector transports:

1. the owner's self-hosted Pangram API path for normal programmatic detector work;
2. a local headed Brave/Chromium + Playwright GUI fallback for visual evidence, authenticated History recovery, and resilience.

Current owner instructions, exact repository evidence, tests, and current `main` outrank historical chat or old task branches.

## Authority and recovery

- Canonical repository branch: `main`.
- Long-lived fixed-batch/evidence branch: `automation/pangram-fixed-batch`.
- Start lesson recovery at `state/LESSON-INDEX.md`.
- Start repository documentation at `docs/INDEX.md`.
- This file is the single canonical repository recovery checkpoint.
- The local GUI transport is documented at `docs/PANGRAM-LOCAL-PLAYWRIGHT.md`.
- Historical Romance GUI/evidence branches remain provenance only and do not establish article authority.

## Current transport architecture

### Self-hosted Pangram API — normal programmatic route

The owner reports that Pangram API execution is now available through his own server/self-hosted execution path. Use the repository's existing content-addressed cache, task checkpoint/resume, exact model/version gates, ambiguity protection, call budget, and durable Git evidence rules around that transport. Never expose or commit API credentials.

The API is the normal choice when a programmatic detector result is all that is required.

### Local Playwright GUI — supported fallback

The reusable local authenticated-browser transport is now on `main`.

It uses:

- a dedicated persistent automation profile, not the owner's ordinary browser profile;
- headed Brave/Chromium through Playwright;
- exact input SHA-256 and optional pre-authorized hash gates;
- a durable `submission-reservation.json` persisted before the detector click;
- an authenticated History-record listener attached before the paid click;
- exact/bounded `/api/history/<uuid>/` stored-text binding;
- explicit Pangram 4 `response.overall` structured fractions rather than guessed `prediction_prob` semantics;
- recovery-before-repeat after an ambiguous action;
- bounded tab cleanup and privacy-limited diagnostics;
- labeled Playwright/CDP PDF fallback evidence when Pangram does not expose a native download.

The generic command is `pangram-local`; it accepts explicit input files and no longer embeds a Romance article default.

The older remote Browserbase implementation remains only as shared compatibility/evidence code plus an optional remote adapter. The Browserbase service is not required for normal local GUI execution.

## Live local-GUI certification — 2026-08-20

The historical local-GUI evidence branch completed the exact 20,496-word Romance two-half workflow end to end.

### Part 1

- exact SHA-256: `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`
- words: 10,236
- Pangram: 4.0 / `STAGE_SUCCESS`
- Human fraction: `0.9205247164`
- AI fraction: `0.0794752836`
- AI-assisted fraction: `0.0`
- stored-text binding: `exact_utf8`
- paid GUI calls total: exactly 1
- the original paid call had become capture-ambiguous; final recovery identified its exact stored record and did **not** submit Part 1 again.

### Part 2

- exact SHA-256: `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`
- words: 10,260
- Pangram: 4.0 / `STAGE_SUCCESS`
- Human fraction: `0.8983033895`
- AI fraction: `0.1016966403`
- AI-assisted fraction: `0.0`
- stored-text binding: `exact_utf8`
- paid GUI calls total: exactly 1
- Part 2 was submitted once only after Part 1 had become an exact recovered cache hit.

Total paid GUI calls for that audit: exactly 2, one per half. No duplicate Part-1 submission occurred.

These are two half-document measurements, not a measured whole-article score and not article authority.

## Mainline GUI promotion

The clean current-main local-GUI promotion was built directly from the then-current `main` rather than merging the old Romance/GUI branch stack.

Promotion result:

- reusable local browser/auth/profile/history/result modules moved onto current `main`;
- a generic structured-History completion layer and `pangram-local` CLI were added;
- old article-specific Browserbase workflow/script topology was intentionally not promoted;
- clean-main validation passed **226 tests with 5 intentional skips**;
- changed-file lesson closeout passed;
- repository audit passed;
- repository workflow policy passed;
- no Pangram detector submission occurred in CI.

The clean promotion merged to `main` as `57db50384933be52bd91f6a078b924bebcd0f7f8`.

The older **remote Browserbase Pangram GUI automation proposal** and the older **stacked local Brave/Playwright GUI development/evidence proposal** are closed as superseded. Their branches/history are preserved as provenance; do not delete them merely because the reusable transport was promoted.

## Lesson-closeout cleanup

During clean-main integration, the repository audit exposed five pre-existing Romance state artifacts on `main` whose current hashes had no lesson dispositions. They were not caused by the GUI promotion.

All five were explicitly dispositioned through the trusted closeout processor:

- two historical assistant integration/restoration records: `superseded`;
- three exact owner-final/detector evidence records: `article-specific`.

No duplicate universal humanization rule was created. Existing promoted lessons already cover recovery-before-repeat, exact artifact binding, contextual detector windows, realization-first repair, persistent-browser hygiene, and fail-closed paid work.

## Older governance state

The older fail-closed paid-dispatch registration and evidence-branch workflow hardening are already merged. Do not resume their old “merge next” instructions from stale checkpoints.

The separate hosted-controls hardening audit remains open and is not a GUI-transport blocker. It owns verification of repository-hosted settings that cannot be inferred from repository files alone.

## Current blockers / unresolved

There is no known local-GUI transport blocker.

Remaining unrelated repository governance work is tracked separately, especially hosted-control verification. Do not treat that as a reason to disable the now-supported API or local GUI transports.

Browserbase-native execution has not been re-promoted as a primary route; treat it as optional compatibility/fallback code unless a future task specifically needs remote browser execution.

## Next safe action

For ordinary Pangram work:

1. use the self-hosted API when a programmatic result is sufficient;
2. use `pangram-local` when authenticated GUI/history recovery or visual evidence is useful;
3. before any paid action, check exact cache/result/reservation/history state;
4. if an action may already have happened, recover first and do not repeat automatically;
5. persist exact hashes, model/version, result fractions, and evidence before another paid input.

No further GUI validation call is required merely to prove the transport. New paid GUI calls should be justified by an actual detector task, not by infrastructure testing.

## Recovery rule

After interruption or a fresh chat, inspect current `main`, this checkpoint, `state/LESSON-INDEX.md`, `docs/PANGRAM-LOCAL-PLAYWRIGHT.md`, the relevant evidence branch/cache/ledger, and any active task-specific branch before acting.

Never infer paid-call state from chat. Never repeat an ambiguous or already-paid detector action before exact stored state has been recovered or deliberately resolved.
