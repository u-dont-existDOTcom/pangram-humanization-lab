# Pangram local Playwright current state — 2026-08-19

## Goal

Use a dedicated headed persistent local Playwright profile on Joel's Zorin machine as the primary Pangram GUI transport while preserving exact-hash identity, ambiguity/duplicate protection, exact report evidence, paid-call accounting, recovery-before-repeat, bounded browser tabs, and GitHub durability.

## Authority / branch

- Repository: `u-dont-existDOTcom/pangram-humanization-lab`.
- Implementation branch: `agent/pangram-local-playwright-gpt-20260818` / draft PR #78.
- Romance source remains incubator branch `agent/romance-primal-crucible-gui-repair-20260817`; this tooling work does not establish article authority or edit prose.

## Exact current Romance boundary

- Reader-visible total: 20,496 words; SHA-256 `10359ab2119ffbe9a8a7a4a52cd0c3216bb1a6a2c0bffbd7e66fca01287f17ce`.
- Part 1: 10,236 words; SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`.
- Part 2: 10,260 words; SHA-256 `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`.
- Source commit last verified on owner machine: `8e0d70d0ea51fbcb12e307ed0629ed75ee35ce8c`.

## Live local transport already verified

- Brave `/opt/brave.com/brave/brave`, Playwright 1.62.0, Chromium sandbox enabled.
- Dedicated persistent profile `~/.config/pangram-local-browser/`; ordinary Brave profile is never used.
- Manual login completed and fresh-process authentication persistence verified.
- Exact source materialization/hash/word-count gates verified.
- Persistent tab accumulation repaired: normal runs are bounded to one working tab and leave an inert tab on shutdown.
- Exact report completion now scans all pages and accepts only a page bound to the exact input with a supported parsed layout and exact analyzed word count.
- Self-updating operator wrapper re-execs exactly once if `git pull` changes the wrapper itself.

## Paid-call state — blocking

Audit: `romance-current-20496-pangram-gui-20260818`.

### Part 1 — one paid call, ambiguous, DO NOT REPEAT

- section `romance-current-part-1`;
- paid calls: 1;
- estimated credits/cost: 11 / USD 0.55;
- exact SHA `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`.

The call reached Pangram. The original capture remained on the initiating dashboard and failed to parse a bound report. `failure.json` records `detector_submission_attempted: true`; the durable call reservation remains. No automatic Part-1 resubmission is permitted.

### Part 2 — never submitted

Part 2 remains uncached with no paid reservation. It must not run until Part 1 is recovered exactly.

## Recovery evidence already exhausted

1. Restored-tab recovery: only `/dashboard`, no report markers.
2. Older labelled History/scans/reports navigation: no exact report.
3. Dedicated-profile Chromium History SQLite: 0 `/history/<UUID>` candidates. This is not authoritative for SPA application history.
4. First authenticated dashboard DOM/JSON recovery: owner-machine suite **179/179 passed**; no Part-1 repeat and no Part-2 call; still no exact result located. Final page remained `/dashboard` with no report markers.

The exact latest live receipt is the 2026-08-19 `pangram-local-recover-resume.log` supplied by Joel.

## Current UI correction after the 179/179 run

Fresh official Pangram product material shows that stored detector records are currently surfaced under **All Checks**, with rows exposing **View Results**. The prior recovery code was biased toward older labels/routes containing `History`, scans, or reports.

The branch now includes a new read-only recovery patch that has **not yet been validated on Joel's machine**:

- recognizes `All Checks`, checks, records, and prior History/scans/reports vocabulary;
- selects past-record navigation using rendered control labels as well as routes, so the href need not literally contain `history`;
- follows explicit same-origin `View Results` links even if their current route differs from `/history/<UUID>`;
- accepts in-memory JSON result identity ancestry under check/document/submission/analysis as well as history/result/scan/detection/request;
- may inspect JSON responses from a backend host different from `pangram.com`, but retains only candidate identities and discards bodies;
- may open one explicitly-labelled menu/sidebar control before retrying All Checks/History controls;
- every candidate must still exact-bind to Part 1 and 10,236 analyzed words before ambiguity clears.

Project-specific checkpoint: `state/PANGRAM-LOCAL-ALL-CHECKS-RECOVERY-2026-08-19.md`.

## Privacy-bounded fallback diagnostic

If the current All Checks recovery still fails, it writes:

`~/Téléchargements/pangram-local-history-structure-diagnostic.json`

The file contains only structural information: redacted page metadata, visible interactive labels, candidate counts, response host/redacted path/status/content-type/method, and JSON key shapes. It excludes submitted text, response bodies, private result URLs, query strings, cookies, storage values, credential/header values, and secrets.

## Next safe action

Run:

`scripts/pangram_local_romance_recover_resume_safe.sh`

The wrapper must self-update/re-exec, run the complete local deterministic suite, then attempt exact no-repeat recovery through the current All Checks/View Results surface. If Part 1 is recovered, cache/persist it and only then allow uncached Part 2 to run. If recovery fails, stop with ambiguity intact and inspect the structural diagnostic; do not guess another selector and do not repeat Part 1.

## Stop conditions

Stop before resubmitting Part 1, bypassing its reservation/ambiguity block, submitting Part 2 before exact Part-1 recovery, using Joel's ordinary browser profile/history, committing browser/session/auth material, accepting a generic report marker, or rewriting Romance prose merely to simplify detector transport.
