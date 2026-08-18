# Pangram local Playwright current state — 2026-08-18

## Goal

Use a dedicated, headed, persistent local Playwright profile on Joel's Zorin machine as the primary Pangram GUI transport while preserving exact-hash identity, no-duplicate/ambiguity guards, report evidence, History recovery, paid-call accounting, and GitHub durability. Browserbase remains fallback.

## Authority and branch

- Repository: `u-dont-existDOTcom/pangram-humanization-lab`.
- Implementation branch: `agent/pangram-local-playwright-gpt-20260818`.
- Stack base: Browserbase tooling PR #35 head `f29c02152e45aa723ccfcefd2e0a1f952e6fffe3`.
- Romance source remains incubator branch `agent/romance-primal-crucible-gui-repair-20260817`; this work does not establish article authority or edit prose.

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
- Chromium sandboxing enabled (the prior `--no-sandbox` warning removed);
- dedicated persistent profile `~/.config/pangram-local-browser/`;
- one-time manual Pangram login;
- fresh-process authentication persistence;
- authenticated detector input editable without filling/submitting;
- exact current Romance source materialization and SHA/word-count checks;
- before the paid run, both exact halves were uncached and unambiguous;
- owner-machine deterministic suite passed 167/167 immediately before the first paid attempt.

## Paid-call state

Audit: `romance-current-20496-pangram-gui-20260818`.

### Part 1

One paid Part 1 detector action was reserved durably and submitted:

- section: `romance-current-part-1`;
- paid calls: 1;
- estimated credits: 11;
- estimated cost: USD 0.55;
- exact SHA: `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`.

The call reached Pangram. Evidence then failed at report capture because the original runner accepted a generic report-ready marker on the wrong page/surface and found no parseable analyzed segments. The saved dashboard body contains the submitted text but no parseable report segments.

`failure.json` correctly records `detector_submission_attempted: true`. Therefore Part 1 is **ambiguous and blocked from automatic repeat**. Its durable call reservation remains in `state/pangram-call-ledgers/romance-current-20496-pangram-gui-20260818.json`.

### Part 2

Part 2 was not submitted. It remains uncached and has no paid reservation, but it must not be run until Part 1 is recovered successfully.

## Owner correction: browser tab accumulation

Joel reported that the automation was opening too many tabs and not closing them. This was confirmed as a persistent-profile lifecycle defect: Chromium could restore tabs that were open at shutdown, while the initial runner closed the context without explicitly normalizing the tab set.

The durable incident and repair are recorded in:

`state/PANGRAM-LOCAL-TAB-REPORT-INCIDENT-2026-08-18.md`

## Current repairs

### Tab/session hygiene

The local transport now:

- normally starts with one working tab and explicitly closes restored extras;
- keeps one tab between multi-part operations;
- before persistent-context shutdown, closes extras and leaves the surviving tab at `about:blank`;
- preserves authentication in the profile without preserving an ever-growing tab session.

An ambiguous-result recovery launch may intentionally retain restored tabs long enough to search them for an already-paid result, then performs the same cleanup before closing.

### Exact multi-tab report binding

The paid runner no longer treats `wait_for_report` generic UI text as completion. It scans every open page/tab and accepts a result only when:

1. stable report anchors bind it to the exact submitted text;
2. the report parser yields supported analyzed segments/layout;
3. parsed analyzed word count equals the exact submitted boundary.

The exact matching page is then used for body and PDF evidence. This covers same-tab and new-tab result behavior.

### Paid-call accounting

The local paid runner reuses the canonical `PangramCallLedger` and six-call section cap. Each paid call reservation is committed/pushed before detector activation. A reserved but incomplete call is never silently repeated.

## Next safe action

Use:

`scripts/pangram_local_romance_recover_resume_safe.sh`

It must:

1. update the branch and run the complete local deterministic suite;
2. recover the already-paid Part 1 result from restored tabs or bounded History navigation **without submitting Part 1 again**;
3. exact-bind and cache the recovered Part 1 report;
4. normalize/close extra tabs;
5. only after successful recovery, resume the paid runner, where Part 1 is a cache hit and only uncached/unambiguous Part 2 may be submitted;
6. use exact multi-tab report binding for Part 2 and preserve evidence/call accounting before completion.

If Part 1 cannot be recovered automatically, stop. Do not repeat it. If Part 2 becomes ambiguous after detector activation, stop and recover it before any repeat.

## Hosted CI / cost boundary

Private-repository hosted Actions are currently being conserved. The current tooling repair commits use `[skip ci]`; use the owner-machine local deterministic suite for this recovery lane rather than spending more hosted Actions minutes solely for code validation.

## Stop conditions

Stop before:

- resubmitting Part 1;
- bypassing any ambiguity block or paid-call reservation;
- submitting Part 2 before Part 1 recovery succeeds;
- using Joel's ordinary browser profile;
- committing profile/cookie/auth material;
- accepting a generic report marker without exact text + word-count binding;
- leaving persistent browser tab clutter as normal automation state;
- rewriting Romance prose solely to facilitate transport/detector behavior.
