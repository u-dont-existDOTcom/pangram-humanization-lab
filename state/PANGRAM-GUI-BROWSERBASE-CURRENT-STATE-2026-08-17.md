# Pangram GUI Browserbase Current State — 2026-08-17

## Goal

Replace Joel's repetitive manual Pangram GUI copy/paste/report-download loop with deterministic Browserbase + Playwright automation while retaining the GUI/PDF evidence that is useful for visual localization.

## Authority / baseline

- Development branch: `agent/pangram-browserbase-gui-automation-20260817`.
- Draft PR: #35, currently based on `agent/romance-concept-flow-improvement-20260817` for access to the exact current Romance split inputs during development.
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
- live debugger URL lookup;
- Playwright connection over the returned CDP `connectUrl`;
- reuse of Browserbase's default browser context;
- one-time `bootstrap_login` flow that opens Pangram login in a live Browserbase session, waits for manual login, verifies the Pangram detector is visible, then closes the session so authentication changes persist.

### Pangram GUI runner

The live runner:

1. reads exact UTF-8 detector input and hashes it;
2. skips an already completed identical SHA by default;
3. opens Pangram using the persistent Browserbase Context;
4. fails closed if login has expired or a bounded detector input cannot be found;
5. fills exact text with Playwright;
6. clicks only a bounded detector-action button name (`Check for AI`, `Scan for AI`, `Detect`, `Analyze` variants);
7. waits for report markers;
8. writes raw visible report text and parses structured detector evidence;
9. prefers a clearly named native Pangram report/PDF download;
10. falls back to Chromium print-to-PDF only if no bounded native download succeeds, and marks the provenance as `playwright_print_fallback`;
11. writes complete result evidence including Browserbase session/debug/recording URLs;
12. writes `failure.json` plus best-effort screenshot and re-raises on failures.

### CLI

`scripts/pangram_gui_browserbase.py`

- `bootstrap` — create/reuse persistent Context and perform the one-time manual Pangram login;
- `run` — measure repeated `--input` files;
- no explicit inputs defaults to current Romance `pangram-part-1.txt` and `pangram-part-2.txt` on a branch where those files exist;
- `--force` is required to repeat a completed identical measurement.

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

## Current blocker / unresolved

### Live Browserbase + Pangram smoke test

No Browserbase API key, Project ID, or persistent Context has been supplied to this work session. Therefore the following are **implemented but not yet live-certified**:

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
2. Obtain Browserbase API key and Project ID.
3. Locally install `.[browser]`.
4. Set `BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID`.
5. Run `python scripts/pangram_gui_browserbase.py bootstrap`.
6. Open the printed live debugger URL and log into Pangram normally.
7. Press Enter in the terminal; retain the returned Context ID.
8. Store `BROWSERBASE_API_KEY` and `BROWSERBASE_CONTEXT_ID` as GitHub repository secrets.

After that, normal detector runs can be unattended.

## Next safe action

Perform the one-time Browserbase/Pangram bootstrap and run a smoke measurement on a small known Pangram text first. Inspect the Browserbase recording and parsed JSON against the GUI. If that succeeds, run the two current Romance halves, confirm that native-PDF capture or explicitly marked fallback behaves correctly, then port the validated tooling to a clean `main`-based PR and close out the durable lesson/tooling state.
