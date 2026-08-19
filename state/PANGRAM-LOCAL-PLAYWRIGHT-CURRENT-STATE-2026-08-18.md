# Pangram local Playwright current state — 2026-08-19

## Goal

Use a dedicated, headed, persistent local Playwright profile on Joel's Zorin machine as the primary Pangram GUI transport while preserving exact-hash identity, no-duplicate/ambiguity guards, report evidence, History recovery, paid-call accounting, and GitHub durability. Browserbase remains fallback.

## Authority and branch

- Repository: `u-dont-existDOTcom/pangram-humanization-lab`.
- Implementation branch: `agent/pangram-local-playwright-gpt-20260818`.
- Romance source remains incubator branch `agent/romance-primal-crucible-gui-repair-20260817`; this tooling work does not establish article authority or edit prose.
- PR: #78, still draft/open.

## Exact current Romance boundary

- Reader-visible total: 20,496 words.
- Reader-visible SHA-256: `10359ab2119ffbe9a8a7a4a52cd0c3216bb1a6a2c0bffbd7e66fca01287f17ce`.
- Part 1: 10,236 words; SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`.
- Part 2: 10,260 words; SHA-256 `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`.
- Source commit last verified on owner machine: `8e0d70d0ea51fbcb12e307ed0629ed75ee35ce8c`.

## Verified owner-machine gates

The local Zorin path has verified:

- headed Brave launch using `/opt/brave.com/brave/brave`;
- Playwright 1.62.0 inside the repository virtual environment;
- Chromium sandboxing enabled;
- dedicated persistent profile `~/.config/pangram-local-browser/`;
- one-time manual Pangram login and fresh-process authentication persistence;
- authenticated detector input editable without filling/submitting;
- exact current Romance source materialization and SHA/word-count checks;
- persistent-tab cleanup after owner-reported tab accumulation;
- owner-machine deterministic suite progression: 167/167, then 171/171, then 175/175, and most recently **176/176 passed** on 2026-08-19 before the latest dashboard-History recovery patch.

## Paid-call state

Audit: `romance-current-20496-pangram-gui-20260818`.

### Part 1 — ambiguous, do not repeat

One paid Part 1 detector action was durably reserved and submitted:

- section: `romance-current-part-1`;
- paid calls: 1;
- estimated credits: 11;
- estimated cost: USD 0.55;
- exact SHA: `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`.

The call reached Pangram. The original runner then captured the initiating dashboard rather than a bound result page and failed because no analyzed segments could be parsed. `failure.json` records `detector_submission_attempted: true`; the paid-call ledger remains durable. Part 1 is therefore **ambiguous and blocked from automatic repeat**.

### Part 2 — not submitted

Part 2 remains uncached and has no paid reservation. It must not be submitted until Part 1 is recovered successfully.

## Owner correction: browser tab accumulation

Joel reported that the automation was opening too many tabs and not closing them. This was a real persistent-profile lifecycle defect. The transport now normally starts/ends with one bounded working tab, closes extras explicitly, and leaves an inert `about:blank` tab on shutdown. The incident is preserved in `state/PANGRAM-LOCAL-TAB-REPORT-INCIDENT-2026-08-18.md`.

## Exact report binding repair

Paid-result completion no longer accepts a generic UI marker on the initiating page. It scans all current pages/tabs and accepts a report only when:

1. stable anchors bind it to the exact submitted text;
2. the parser yields a supported analyzed layout;
3. parsed analyzed word count equals the exact submitted boundary.

The matching page becomes the body/PDF evidence page.

## Recovery evidence so far

### Restored-tab / bounded UI route

The first no-repeat recovery found only one restored page, `https://www.pangram.com/dashboard`, with no report markers. Bounded History-control navigation did not recover the exact report. No Part 1 repeat and no Part 2 call occurred.

### Self-updating wrapper incident

A later run fetched new recovery code while an older wrapper process was already running. The process continued its old in-memory control flow. The wrapper now detects when `git pull` changes itself and `exec`s the fetched version exactly once before consequential work; the transferable lesson was promoted to `u-dont-existDOTcom/universal-dev-architecture`.

### Dedicated Chromium History route — live falsification

On the latest owner-machine run:

- deterministic suite: **176/176 passed**;
- Part 1 was not submitted again;
- Part 2 was not submitted;
- the dedicated profile's Chromium `History` SQLite databases yielded **0** Pangram `/history/<UUID>` result URLs;
- the only final page was the authenticated dashboard with no report markers.

This falsifies the assumption that a dashboard SPA result must appear in Chromium's global browsing-history database. It does **not** establish that Pangram lost the result. Pangram's current public data-privacy documentation states that dashboard submissions remain available in account History while the account is active, and documented dashboard-result links use `/history/<UUID>`.

## New recovery route — hydrated authenticated dashboard History

After the 176/176 live run, the branch added a stricter read-only recovery layer. This code has not yet been validated on Joel's machine.

`src/pangram_lab/browser_history_recovery.py` now supports three in-memory result-identity sources:

1. existing dedicated-profile Chromium history (still tried first, but no longer assumed authoritative);
2. `/history/<UUID>` links already rendered in authenticated Pangram DOM;
3. Pangram result UUIDs/links contained in authenticated Pangram JSON responses while navigating the dashboard History surface.

Privacy/safety boundaries:

- only the dedicated automation profile is used;
- ordinary Brave history is never inspected;
- only Pangram same-origin/same-domain result identities survive filtering;
- JSON bodies are inspected only in memory and discarded; submitted text, cookies, storage, headers, and private URLs are not printed or committed;
- bare UUIDs are accepted only when their JSON key ancestry places them under history/result/scan/detection/request context;
- every candidate is read-only and must exact-bind to Part 1 plus the 10,236-word count before it can clear ambiguity;
- the recovery script contains no Part 1 detector-action path.

`scripts/pangram_local_romance_recover_part1_history.py` now:

- discovers result links already rendered on the dashboard;
- follows current dashboard-rendered History navigation URLs rather than assuming a remembered route;
- may click only visible interactive controls explicitly labeled History / past scans / recent scans / my scans / reports;
- listens to authenticated Pangram JSON responses during that navigation and extracts only result identities;
- tries all bounded candidate result URLs in one working tab;
- falls back to the older bounded recovery route only after those sources fail.

Deterministic tests were added/expanded for DOM result-link filtering, History-navigation filtering, payload UUID ancestry, unrelated-account UUID rejection, URL canonicalization, and existing SQLite behavior. The complete owner-machine suite must run before this new path is trusted.

## Next safe action

Run the same terminal-safe entry point:

`scripts/pangram_local_romance_recover_resume_safe.sh`

It must:

1. self-update/re-exec safely if its wrapper changes;
2. run the complete local deterministic suite including the new dashboard-History tests;
3. recover the already-paid Part 1 result through the authenticated Pangram History surface **without submitting Part 1 again**;
4. exact-bind and cache Part 1 if found;
5. normalize/close extra tabs;
6. only after successful Part 1 recovery, resume the paid runner where Part 1 is a cache hit and only Part 2 may be submitted;
7. if Part 2 becomes ambiguous, stop and recover it before any repeat.

If Part 1 still cannot be recovered, stop with the paid ambiguity intact. Do not repeat it.

## Hosted CI / cost boundary

Private-repository hosted Actions are being conserved. Recovery/tooling commits use `[skip ci]`; validation for this lane is the owner-machine deterministic suite plus the exact live recovery gate.

## Stop conditions

Stop before:

- resubmitting Part 1;
- bypassing any ambiguity block or paid-call reservation;
- submitting Part 2 before Part 1 recovery succeeds;
- using Joel's ordinary browser profile/history;
- committing profile/cookie/auth/session material;
- accepting a generic report marker without exact text + word-count binding;
- leaving persistent browser tab clutter as normal automation state;
- treating Chromium global history as authoritative for SPA application history;
- rewriting Romance prose solely to facilitate transport/detector behavior.
