# Pangram local Playwright current state — 2026-08-18

## Goal

Replace Browserbase as the primary Pangram GUI transport with a dedicated, headed, persistent local Playwright profile on Joel's Zorin machine while preserving the existing exact-hash cache, no-duplicate guard, parser, PDF/screenshot evidence, no-submit History recovery, and GitHub durability.

## Authority and branch

- Repository: `u-dont-existDOTcom/pangram-humanization-lab`.
- Implementation branch: `agent/pangram-local-playwright-gpt-20260818`.
- Stack base: Browserbase tooling PR #35 head `f29c02152e45aa723ccfcefd2e0a1f952e6fffe3`.
- Romance source remains the incubator branch `agent/romance-primal-crucible-gui-repair-20260817`; this work does not establish article authority or edit prose.
- Browserbase remains an optional fallback rather than being deleted.

## Exact current Romance boundary

- Reader-visible total: 20,496 words.
- Reader-visible SHA-256: `10359ab2119ffbe9a8a7a4a52cd0c3216bb1a6a2c0bffbd7e66fca01287f17ce`.
- Part 1: 10,236 words; SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`.
- Part 2: 10,260 words; SHA-256 `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`.
- No current-half Pangram submission is recorded. The Browserbase 402 occurred before text fill or detector activation.

## Implemented

### Shared-core local transport

`src/pangram_lab/gui_local.py` imports and reuses the Browserbase module's transport-independent identity, cache, ambiguity, auth, selector, parser, report, PDF, and History-binding logic. It adds only the local browser/session layer and local provenance.

Implemented behavior:

- dedicated default profile `~/.config/pangram-local-browser/`;
- refusal of normal browser profiles without explicit override;
- refusal of persistent profiles inside real Git worktrees without explicit override, while an inert home-level `.git` marker does not create a false positive;
- headed browser by default;
- Chromium sandboxing explicitly enabled for authenticated local persistent sessions;
- system Brave/Chromium-family discovery, with explicit executable support;
- persistent-context lifecycle with closure in success and failure paths;
- one-time manual login bootstrap;
- fresh read-only authentication verification;
- local browser launch smoke;
- exact-SHA and word-count gates before browser launch;
- cache and ambiguous-submission behavior shared across Browserbase and local receipts;
- exact report word-count verification;
- raw report, PDF, and screenshot evidence;
- native download / Playwright print / local CDP print provenance;
- no-submit History recovery;
- source commit/path/manifest provenance for exact current Romance inputs.

### Deterministic CLI

`pangram-local` / `scripts/pangram_local.py` provides:

- `bootstrap`
- `verify`
- `status`
- `run`
- `recover`

Default `status`/`run` fetch the live Romance source branch, read the current manifest and halves with `git show`, materialize them into a private cache outside Git, and verify exact blob hashes and word counts. Branch movement is accepted only while the exact authorized detector boundary remains unchanged; receipts record the actual source commit.

### Git durability

`GitSync` now supports path-scoped evidence commits and explicit named-branch pushes:

- only the result/failure directory is committed;
- unrelated staged work remains staged;
- paths outside the repository and the repository root are rejected;
- detached HEAD is rejected;
- a complete result or ambiguous failure is pushed before another input proceeds;
- local cache/failure state remains blocking when the push itself fails;
- the next invocation syncs existing evidence before new browser work.

### Tests and documentation

Added focused tests for profile safety, headed launch, Chromium sandboxing, inert-home-`.git` handling, close-on-success/failure, read-only verification, cache compatibility, exact-SHA preflight, post-click ambiguity, recovery, exact source materialization, and path-scoped Git commits.

Operator documentation: `docs/PANGRAM-GUI-LOCAL-PLAYWRIGHT-RUNBOOK.md`.

## Current verification status

Repository-side exact-head gates are green on the current local-Playwright branch: the complete deterministic test suite, lesson-integrity audit, and repository workflow-policy check passed after the sandbox/profile hardening.

Owner-machine live verification now confirms:

- visible headed Brave launch on Zorin using `/opt/brave.com/brave/brave`;
- Playwright 1.62.0 in the repository virtual environment;
- dedicated persistent profile `~/.config/pangram-local-browser/`;
- clean context close;
- corrected launch without the prior `--no-sandbox` warning;
- one-time manual Pangram login completed in the dedicated profile.

The following remain unverified and must not be inferred from the successful login bootstrap:

- authentication persistence across a fresh local process;
- read-only detector dashboard verification after relaunch;
- exact current Romance cache/ambiguity status after fresh source materialization;
- current long-document Pangram report/PDF behavior;
- paid submission of the two current exact halves.

No paid Pangram call was performed by smoke, bootstrap, or repository implementation work.

## Next safe action

1. Run `pangram-local verify` in a fresh local process; it must verify the authenticated detector without filling or submitting text.
2. Run read-only `pangram-local status` and inspect the exact current Romance source commit, hashes, cache state, and ambiguity flags.
3. If both exact halves remain uncached and unambiguous and authentication persists, run `pangram-local run` once, without `--force`.
4. If the first paid half fails after detector activation may have occurred, stop the batch and use History/recovery before any repeat or Part 2.

## Stop conditions

Stop before:

- using Joel's ordinary browser profile;
- bypassing an ambiguity block;
- repeating a paid exact SHA instead of checking History/recovery;
- committing profile/cookie/auth material;
- claiming fresh-process authentication persistence without its receipt;
- rewriting Romance prose solely to facilitate transport or detector behavior.
