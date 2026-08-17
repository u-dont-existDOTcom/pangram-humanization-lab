# Pangram GUI Browserbase Current State — 2026-08-17

## Goal

Replace Joel's repetitive manual Pangram GUI copy/paste/report-download loop with deterministic Browserbase + Playwright automation while retaining the GUI/PDF evidence that is useful for visual localization.

## Authority / baseline

- Development branch: `agent/pangram-browserbase-gui-automation-20260817`.
- Draft PR: #35, currently based on `agent/romance-concept-flow-improvement-20260817` for access to the exact current Romance split inputs during development.
- Current GUI source ref: `agent/romance-primal-crucible-gui-repair-20260817`, verified at `ea74343a8e8eb01af1cc029370d1d7b1ed081b9f`.
- Exact reader-visible SHA: `378d4afcf7e1dc7684d1b67eafd7b3ac5166a3fab8a59ddf0b3d88144e36453d` (18,702 words).
- Exact Part 1 SHA: `884eb308b7fd12398c6577cb8c93cd8fe3d14d28d0cc8c5b82abdcd64a27d070` (9,330 words); Part 2 SHA: `892904cd38e16893fd78fe6ed217357d192b7b6b4350e8cde1385251dbd7ddf9` (9,372 words).
- This subsystem is detector tooling only. It cannot modify article prose or article authority.
- Browserbase/Pangram credentials are never repository content.

## Completed

### Design and plan

- Specification: `docs/superpowers/specs/2026-08-17-pangram-browserbase-gui-automation.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-17-pangram-browserbase-gui-automation.md`.
- Operator runbook: `docs/PANGRAM-GUI-BROWSERBASE-RUNBOOK.md`.

### Pure evidence layer

`src/pangram_lab/gui_browserbase.py` now provides:

- exact UTF-8 SHA-256 identity;
- content-addressed result directories under `state/gui-runs/pangram-4/<sha>/`;
- completed-result duplicate defense keyed by SHA and runner version;
- stable artifact paths;
- Pangram GUI report parser for overall fractions and per-segment label / word count / confidence / text;
- null rather than invented values when the GUI does not expose a field;
- complete/failure receipt schemas with explicit PDF provenance.

### Browserbase lifecycle

- Browserbase Context creation via REST;
- persistent Context-bound session creation (`browserSettings.context.id`, `persist: true`);
- session timeout/keepAlive controls;
- fullscreen human-control Live View URL lookup, with bordered-debugger fallback;
- Playwright connection over the returned CDP `connectUrl`;
- reuse of Browserbase's default browser context;
- one-time `bootstrap_login` flow that opens Pangram login in a live Browserbase session, waits for manual login, prefers an authenticated `/dashboard` tab opened during login (with original-tab navigation as fallback), rejects login/signup/account-wall states, verifies the detector is visible, then closes the session so authentication changes persist.

### Pangram GUI runner

The live runner:

1. reads exact UTF-8 detector input and hashes it;
2. skips an already completed identical SHA by default and refuses an automatic repeat after an ambiguous post-submit failure;
3. opens Pangram's authenticated `/dashboard` using the persistent Browserbase Context;
4. fails closed before filling text if login/signup or an account wall is visible, or if a bounded detector input cannot be found;
5. fills exact text with Playwright;
6. clicks only a bounded detector-action button name (`Check for AI`, `Scan for AI`, `Detect`, `Analyze` variants);
7. waits for report markers;
8. writes raw visible report text and parses structured detector evidence;
9. prefers a clearly named native Pangram report/PDF download;
10. falls back to Chromium print-to-PDF only if no bounded native download succeeds, and marks the provenance as `playwright_print_fallback`;
11. writes complete result evidence including Browserbase session/debug/recording URLs;
12. writes `failure.json` plus best-effort screenshot and re-raises on failures, recording whether detector submission may already have occurred.

### CLI

`scripts/pangram_gui_browserbase.py`

- `bootstrap` — create/reuse persistent Context and perform the one-time manual Pangram login;
- `run` — measure repeated `--input` files;
- successful bootstrap saves the non-secret Context ID at `~/.config/pangram-gui/browserbase-context-id`, and future local commands reuse it automatically;
- no explicit inputs defaults to current Romance `pangram-part-1.txt` and `pangram-part-2.txt` on a branch where those files exist;
- `--force` is required to repeat a completed identical measurement or an ambiguous post-submit failure after evidence review.

### GitHub Actions

`.github/workflows/pangram-gui-browserbase.yml`

- manual `workflow_dispatch` only;
- repository secrets `BROWSERBASE_API_KEY` and `BROWSERBASE_CONTEXT_ID` required;
- accepts a safe `source_ref` containing the two Romance detector halves;
- extracts those exact files with `git show` instead of mutating them;
- runs Browserbase GUI measurement;
- commits only paths below `state/gui-runs/pangram-4/`;
- serialized through a concurrency group so two GUI detector jobs do not race against the same persistent Context;
- workflow-policy audit passes.

## Test evidence

TDD sequence was followed:

1. Initial parser/identity tests were added before the module existed and failed as expected.
2. Pure parser/identity implementation made the full repository tests pass.
3. Browserbase config/context tests were added before the runtime interfaces existed and failed as expected.
4. Browserbase lifecycle implementation restored the full test suite.
5. Measurement-orchestration receipt/duplicate-defense tests were added before those functions existed and failed as expected.
6. Measurement orchestration implementation restored the full test suite.

Latest known full-test evidence on the implementation path: the `Lesson integrity` PR change-gate reports `Run full test suite: success` after orchestration implementation. The overall lesson-integrity job remains red only because the branch is intentionally not closed out/promoted while live Browserbase/Pangram verification is still outstanding.

Repository workflow-policy audit for the new manual Browserbase workflow: success.

Fresh local verification after the Live View/local-Context durability changes:

- focused GUI suite: `17 passed`;
- full repository suite: `124 passed`;
- repository audit: `0 error(s)`, with five pre-existing/declared warnings.

## Current blocker / unresolved

### Live Browserbase + Pangram smoke test

Live evidence on 2026-08-17 established the following without exposing or storing the API key:

- the original `/tmp/pangram-browserbase-bootstrap.2702145.log` failed at `POST /v1/contexts` with Browserbase `HTTP 401 Unauthorized`;
- the documented API-key-only request contract (`X-BB-API-Key`, `POST /v1/contexts`, body `{}`) matches the implementation;
- a later current API key succeeded and created Context `c6b6b8ce-632f-45f1-be24-1c5fdd6e5981` without a Project ID;
- Browserbase session creation and Playwright CDP connection succeeded;
- the first session exposed a bordered `debuggerUrl`, but that page disconnected before Pangram login was verified;
- the runner now prefers Browserbase's `debuggerFullscreenUrl`, with regression coverage;
- the first session ended, and repeated later attempts to reuse the Context were rejected at session creation with `HTTP 401`; no second session or detector submission occurred.
- a later `bb_live_...` key authenticated independently against Browserbase's read-only Projects API, proving those `401` responses came from pairing the new key with the old Context rather than from the current key;
- the current key created fresh Context `64614e72-db2e-40b5-b6d9-c48833bf2025` and session `31c555ef-f2f3-4133-9abb-9866d3e4f6a6`;
- the old runner falsely accepted the public marketing-page detector input as authenticated login verification and saved that fresh Context;
- a second session, `f7a504fa-a868-4acf-86b8-d9b501cd8374`, filled the 121-word smoke input (SHA `00b54ca37127155ce7c146320b40ba19076ad901714f3b447f1250c764f6d835`) on the public page, clicked `Check for AI`, and timed out waiting for report markers;
- its screenshot proves Pangram redirected to `/signup` and displayed `Create your account to get started`; no report, parsed segment, or PDF was produced;
- because Pangram said the text was saved and would be checked after account creation, preserve this as an ambiguous post-submit attempt and do not automatically submit the same SHA again;
- regression coverage now requires `/dashboard`, rejects login/signup/account-wall states before filling text, and blocks normal reruns of ambiguous post-submit failures.
- corrected bootstrap session `408ca4c9-c40c-409a-b1fc-915d0b36eddc` then failed closed on an account wall after Joel reported completing login; the likely remaining bootstrap defect was verifying only the original login tab while an OAuth/login flow could open the authenticated dashboard in another tab;
- the next regression now prefers an already-open authenticated `/dashboard` tab and otherwise navigates the original page to `/dashboard`; focused GUI coverage passes with both paths.

The fresh Context exists, but authenticated Pangram state and cross-session persistence remain **unverified**. The following are still not live-certified:

- Pangram's current detector input selector;
- Pangram's current detector button accessible name;
- report-completion marker behavior under a real long submission;
- native Pangram PDF/download control detection;
- Browserbase persistent Pangram login surviving into a second unattended session.

Do not claim the GUI automation is production-verified until one real bootstrap + one real measurement succeeds.

### Final promotion branch

Development currently sits on a branch derived from the active Romance assembly so current split files were available while building. Detector tooling should ultimately be promoted cleanly into the lab's normal tooling authority (preferably `main`) without dragging private article-assembly changes into that PR. Do that after the live smoke test or by porting only the tooling/test/docs files to a clean branch from `main`.

## Required user setup

One-time:

1. Create/use a Browserbase account.
2. Obtain a current Browserbase API key.
3. Locally install `.[browser]`.
4. Set only `BROWSERBASE_API_KEY`.
5. Run `python scripts/pangram_gui_browserbase.py bootstrap`.
6. Open the printed fullscreen Live View URL and log into Pangram normally.
7. Press Enter in the terminal; the runner saves the Context ID locally.
8. Store `BROWSERBASE_API_KEY` and `BROWSERBASE_CONTEXT_ID` as GitHub repository secrets.

After that, normal detector runs can be unattended.

## Next safe action

Reuse fresh Context `64614e72-db2e-40b5-b6d9-c48833bf2025` with the current API key and tab-aware `/dashboard` authentication gate, complete Pangram login through fullscreen Live View, and close the session. Start a second session with the same Context and prove login persistence without filling or submitting text. Inspect Pangram history for the saved 121-word SHA before deciding whether any new smoke submission is necessary; do not repeat the ambiguous attempt automatically. Only after one real report is recovered or safely measured should PDF provenance and full-half credit cost be assessed.
