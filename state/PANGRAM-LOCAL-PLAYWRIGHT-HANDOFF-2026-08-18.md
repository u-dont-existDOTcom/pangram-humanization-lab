# Fresh-conversation handoff — Pangram local Playwright migration — 2026-08-18

## Goal

Replace Browserbase as the **primary** Pangram GUI transport with a local persistent Playwright browser on Joel's Zorin machine, while preserving the existing exact-hash cache, no-duplicate safeguards, report parsing, PDF/screenshot evidence, recovery, and GitHub durability. Browserbase may remain as an optional fallback.

The immediate operational goal is to submit the current Romance article halves to Pangram 4.0 without paying Browserbase for browser minutes or requiring Joel to manually copy/paste every detector run.

## Recover current authority first

This is Joel-byline detector/tooling work. Fresh-read before changing anything:

1. `u-dont-existDOTcom/joel-articles/SKILL.md`
2. `u-dont-existDOTcom/joel-articles/CANONICAL-REPO-MAP.md`
3. the rest of the current substantial-work read order named there
4. `u-dont-existDOTcom/pangram-humanization-lab/README.md`
5. `state/WORKING-LESSONS.md`
6. this handoff
7. `docs/PANGRAM-GUI-BROWSERBASE-RUNBOOK.md`
8. `state/PANGRAM-GUI-BROWSERBASE-CURRENT-STATE-2026-08-17.md`
9. `state/PANGRAM-GUI-BROWSERBASE-FREE-MINUTES-BLOCKER-2026-08-18.md`
10. live PR heads for Romance PR #36 and Browserbase tooling PR #35

Do not infer article authority from this handoff. `joel-articles/articles/INDEX.json` is currently empty; Romance remains an incubator in `pangram-humanization-lab`.

## Current Romance detector boundary

Romance branch:

`agent/romance-primal-crucible-gui-repair-20260817`

Current exact reader-visible detector boundary:

- total words: **20,496**
- reader-visible SHA-256: `10359ab2119ffbe9a8a7a4a52cd0c3216bb1a6a2c0bffbd7e66fca01287f17ce`
- Part 1: **10,236 words**; SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`
- Part 2: **10,260 words**; SHA-256 `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`

The article's two card-game references now link to:

`https://innerself.love/blog/romance-card-game/`

Those were link-only Markdown edits around existing visible words, so the reader-visible text and Pangram hashes did **not** change.

## Latest Pangram evidence

The previous exact **20,612-word** boundary was manually tested in Pangram 4.0:

- Part 1: **92.1% Human / 7.9% AI**
- Part 2: **90.2% Human / 9.8% AI**

A safe detector-informed editorial pass then changed only new integration prose where the red detector window corresponded to an independent coherence/overcompletion problem. Owner-controlled historical red spans were not rewritten merely for detector compliance. Two cold audits were completed. The resulting **20,496-word** boundary above is currently **untested**.

Do not transfer the 20,612 scores to the current boundary.

## Browserbase status and why we are moving away from it

Browserbase automation is implemented on:

`agent/pangram-browserbase-gui-automation-20260817` / PR #35.

It already provides useful transport-independent logic:

- exact UTF-8 SHA-256 identity;
- content-addressed evidence under `state/gui-runs/pangram-4/<sha>/`;
- completed-result cache;
- ambiguous-post-submit duplicate defense;
- persistent authenticated Pangram state;
- bounded detector selectors;
- report completion detection;
- long/short report parsing framework;
- raw report-body capture;
- native-PDF preference with Playwright PDF fallback;
- no-submit History recovery;
- failure receipts/screenshots;
- Browserbase session/debug provenance.

Do **not** throw this away. Reuse the pure Pangram/evidence logic and replace only the browser/session backend where possible.

### Live Browserbase outcome

The repository Actions secrets were successfully configured and the exact current Romance hashes verified. The runner then failed on its read-only Browserbase session creation with:

`HTTP 402 Payment Required: Free plan browser minutes limit reached.`

No Pangram text was filled, no detector button was clicked, no Pangram credit was spent, and no ambiguous submission exists for either current half.

Joel reports Browserbase showed roughly two hours consumed even though he remembers only around 15 calls of a few seconds each. Earlier live debugging did expose at least one real lifecycle defect where bootstrap used `keepAlive: true` and a Browserbase session remained `RUNNING` after Playwright disconnected. That bug was fixed. Treat the historical usage discrepancy as plausibly including session-lifecycle/minimum-billing effects, but do not claim an exact accounting without Browserbase billing/session evidence.

For now Joel considers Browserbase too expensive for routine Pangram work.

## Desired replacement architecture

Primary path:

`Codex CLI -> local Pangram runner -> local headed Chromium/Brave via Playwright -> pangram.com`

Browserbase becomes optional fallback only.

### Browser profile rule

Use a **dedicated persistent automation profile**, not Joel's normal everyday browser profile.

Suggested user-data directory:

`~/.config/pangram-local-browser/`

Joel should log into Pangram manually once in that dedicated headed browser. Thereafter the local runner should reuse cookies/storage from that profile.

Do not store Pangram credentials in Git or source files. Do not automate password entry unless Joel explicitly asks for a secure credential path.

### Headed by default

Default local Pangram automation should be visibly headed so Joel can see what the browser is doing and intervene if Pangram changes its UI. A future headless mode can be added only after the headed path is proven reliable.

### Reuse versus rewrite

Prefer extracting a browser-transport abstraction from the existing Browserbase runner instead of forking the whole detector stack.

Keep shared logic for:

- exact input preparation;
- SHA/word identity;
- cache and ambiguous-submission blocking;
- authenticated-dashboard validation;
- detector field/action selectors;
- report wait/parse logic;
- report-to-exact-input binding;
- result/failure schemas;
- PDF/report capture where applicable;
- History recovery.

Add a local transport implementation that owns:

- launching/attaching to local Chromium-family browser;
- persistent `user_data_dir` lifecycle;
- headed window behavior;
- clean browser close;
- local profile health/auth verification;
- local evidence provenance rather than Browserbase session URLs.

## Suggested CLI contract

Do not make Codex improvise browser behavior. Give it deterministic commands.

Desired user-facing surface, naming may be adjusted to fit current CLI architecture:

```text
pangram-local bootstrap
pangram-local verify
pangram-local run --input <file> [--input <file> ...]
pangram-local recover --input <file>
pangram-local status
```

Functional meanings:

- `bootstrap`: launch dedicated headed persistent profile at Pangram login/dashboard; allow Joel to complete login manually; verify dashboard; close cleanly.
- `verify`: launch fresh local browser instance using saved profile; confirm authenticated detector input; **never submit**.
- `run`: exact SHA-bound submission with cache and ambiguous-post-submit protection.
- `recover`: capture a matching existing Pangram History result without a new detector submission.
- `status`: report profile path, auth state if cheaply/read-only verifiable, current exact Romance hashes, cached result/failure status, and whether any ambiguous submission blocks a run.

Codex's role should be supervisor/recovery logic around these deterministic commands, not free-form clicking whenever possible.

## Required implementation sequence

### 1. Fresh smoke-test the local environment

On Joel's Zorin machine, determine:

- current repo path;
- Python/venv state;
- current Playwright package availability;
- available browser executable(s): Brave, Chromium, Chrome, etc.;
- whether Playwright can launch a **headed** persistent context using a dedicated non-default profile;
- whether the visible browser window appears normally in Joel's desktop session.

Do not install a second giant browser stack unless necessary. Prefer an already-installed Chromium-family executable if Playwright can drive it safely; otherwise install only the minimal justified Playwright browser/runtime.

### 2. Add local transport with TDD

Tests first for at least:

- dedicated profile path selection;
- refusal to use an ordinary/default browser profile unless explicitly overridden;
- headed default;
- local session close in success/failure paths;
- provenance schema distinguishes `local_playwright` from Browserbase;
- cache and ambiguous-submission behavior remains identical across transports;
- `verify` cannot submit;
- `recover` cannot submit;
- exact current Romance SHA checks can be enforced before paid calls.

### 3. One-time Pangram login bootstrap

Launch the dedicated local profile visibly. Joel logs in manually. Verify the authenticated `/dashboard` detector is visible. Close and relaunch with `verify` to prove persistence before any paid Pangram call.

### 4. Run a no-cost/read-only verification cycle

Prove repeated local browser start -> authenticated dashboard -> close does not lose the profile and does not submit detector text.

### 5. Live Pangram smoke test

Before spending a long-document call, use a short fixture only if a genuinely new paid smoke is necessary. First inspect existing Pangram History/cache and reuse the already completed 121-word Browserbase smoke result where it is sufficient to validate parser behavior. Do **not** repeat that exact smoke merely because transport changed unless the test specifically needs a local-browser submission and Joel authorizes it.

The local-browser integration can often be validated up through login, fillability, bounded button discovery, and History recovery without buying another detector call.

### 6. Submit current Romance halves

Once local auth persistence and long-document interaction are acceptable, submit the exact current halves:

Part 1 SHA:
`ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`

Part 2 SHA:
`2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`

Do not use `--force`. There is no prior Pangram submission for these SHAs.

If the first half fails **after** the detector action may have been clicked, stop. Save evidence and check Pangram History/recovery before any retry. Do not automatically continue to Part 2 if the first failure suggests UI drift or an account/credit problem.

### 7. Persist evidence

Commit/push:

- exact result JSON;
- raw report text;
- PDF or labeled browser-print fallback;
- screenshots/failure receipt where relevant;
- local transport provenance;
- exact input SHA/word counts;
- Pangram model/version/date;
- parser/report-layout notes;
- no-repeat state.

Do not commit cookies, browser profiles, API keys, passwords, session tokens, or private auth state.

### 8. Compare with manual 20,612 evidence

Once the 20,496 results exist, use them only as detector localization evidence. Check whether safe repairs improved the previously new red regions. If remaining red is primarily in owner-controlled historical spans, stop for an owner/editorial decision before rewriting them merely for detector compliance.

## Browserbase cleanup / fallback posture

Do not delete PR #35 immediately. It contains useful transport/evidence work and a proven Browserbase fallback path.

After local transport works:

- refactor shared Pangram GUI logic so Browserbase and local Playwright call the same core where practical;
- document Browserbase as optional remote fallback;
- keep `keepAlive: false` for normal short-lived Browserbase verification/run sessions unless a specifically justified long-lived session is required;
- ensure every Browserbase session closes in `finally` paths;
- consider adding Browserbase session-duration diagnostics so future billed-time anomalies can be audited from recorded session start/end/status rather than guessed.

## Current article-side constraint

Do not make further Romance prose changes merely to facilitate local-browser work. The current reader-visible detector boundary is intentionally hash-stable. The card-game link change already points readers directly to Joel's game without altering detector-visible text.

If article prose changes for another reason before Pangram submission, regenerate the reader-visible boundary and halves and treat all hashes in this handoff as historical.

## Stop conditions

Stop and ask Joel before:

- spending a new Pangram call only for transport debugging when read-only verification could suffice;
- using Joel's ordinary browser profile instead of a dedicated automation profile;
- bypassing an ambiguous-post-submit block with `--force`;
- rewriting owner-controlled article prose solely to improve Pangram;
- committing any browser/auth secret material;
- discarding Browserbase tooling rather than refactoring/reusing its core without first checking whether a clean shared-core extraction is feasible.

## Success condition

The migration is complete when Joel can run one local command (or ask Codex to run it) that:

1. recovers the current exact Romance halves;
2. verifies their SHA-256 identities;
3. opens a dedicated authenticated local Pangram browser profile;
4. reuses cache/History where possible;
5. submits only uncached exact text;
6. captures structured Pangram evidence and PDF/screenshots;
7. closes the browser cleanly;
8. commits/pushes durable evidence;
9. refuses duplicate or ambiguous repeat submissions automatically.
