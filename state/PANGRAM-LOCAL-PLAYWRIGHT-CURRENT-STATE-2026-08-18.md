# Pangram local Playwright current state — 2026-08-20

## Status

**LIVE VALIDATION COMPLETE for the current Romance two-half boundary.**

The dedicated headed local Playwright transport on Joel's Zorin machine has now completed the full long-document workflow end to end with exact stored-history binding, duplicate-call protection, paid-call accounting, durable Git evidence, bounded tabs, and PDF capture.

The Pangram API is independently available through Joel's private self-hosted executor. Keep API and GUI as separate supported transports; GUI remains useful for visual/report inspection, authenticated-history recovery, evidence capture, and resilience.

## Authority / branch

- Repository: `u-dont-existDOTcom/pangram-humanization-lab`.
- Implementation branch: `agent/pangram-local-playwright-gpt-20260818` / draft PR #78.
- PR #78 remains stacked on the Browserbase GUI branch / PR #35. Do not retarget or merge that stack by inference.
- Romance material remains incubator material in this repository; this tooling state does not establish article authority.
- Repository visibility is public; normal code-only CI may be used. Detector execution remains intentional and separately gated.

## Independent API transport

Pangram API execution is also available through Joel's self-hosted execution path. `u-dont-existDOTcom/pangram-private-executor` is the trusted private envelope around the self-hosted runner and reuses the lab's cache, pending-task checkpointing, ambiguity guard, call ledger, section cap, result schema, and Git synchronization.

A private-executor smoke has already produced a durable Pangram 4.0 `STAGE_SUCCESS`. This is a separate transport and does not replace the GUI evidence below.

## Exact validated Romance boundary

- Reader-visible total: **20,496 words**; SHA-256 `10359ab2119ffbe9a8a7a4a52cd0c3216bb1a6a2c0bffbd7e66fca01287f17ce`.
- Part 1: **10,236 words**; SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`.
- Part 2: **10,260 words**; SHA-256 `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`.
- Source commit bound by the run: `8e0d70d0ea51fbcb12e307ed0629ed75ee35ce8c`.
- Manifest SHA-256: `21808bf6f02355f63093cfe2ebdd79936de360522942c19b51afccc828f021b2`.

## Final GUI detector results

### Part 1 — recovered exactly, no repeat submission

- Original paid reservation: `2026-08-18T17:43:00.595741+00:00`.
- Timestamp-bound history record created **12.974 seconds** later.
- Stored `prompt` exact-matched the authorized Part-1 UTF-8 bytes and 10,236-word boundary.
- Transport match mode: `exact_utf8`.
- Detector: Pangram 4.0 / `STAGE_SUCCESS`.
- Headline: `Mostly Human Written`.
- Prediction short: `Human`.
- AI fraction: **0.0794752836**.
- AI-assisted fraction: **0.0**.
- Human fraction: **0.9205247164**.
- Recovery itself made **no detector submission**.
- Evidence source: `recovered_existing_report`.
- Durable receipt: `state/gui-runs/pangram-4/ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8/result.json`.

The original ambiguity is therefore resolved. Do not resubmit Part 1 merely because its first live capture failed.

### Part 2 — one new GUI submission, exact completion

- Paid reservation: `2026-08-20T16:27:40.570062+00:00`.
- One GUI submission was made after the reservation was durably pushed.
- Stored `prompt` exact-matched the authorized Part-2 UTF-8 bytes and 10,260-word boundary.
- Transport match mode: `exact_utf8`.
- Detector: Pangram 4.0 / `STAGE_SUCCESS`.
- Headline: `AI Detected`.
- Prediction short: `Mixed`.
- AI fraction: **0.1016966403**.
- AI-assisted fraction: **0.0**.
- Human fraction: **0.8983033895**.
- PDF provenance: `playwright_print_fallback`.
- Durable receipt: `state/gui-runs/pangram-4/2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0/result.json`.

## Paid-call accounting

Audit: `romance-current-20496-pangram-gui-20260818`.

- Part 1: **1 paid GUI call** total; estimated 11 credits / USD 0.55.
- Part 2: **1 paid GUI call** total; estimated 11 credits / USD 0.55.
- Total GUI paid calls for these two exact halves: **2**.
- No duplicate Part-1 submission occurred during any recovery attempt.
- Durable ledger: `state/pangram-call-ledgers/romance-current-20496-pangram-gui-20260818.json`.

## Local transport validation

Verified on the owner machine:

- Zorin / Linux with Brave `/opt/brave.com/brave/brave`;
- Playwright 1.62.0;
- dedicated persistent profile `~/.config/pangram-local-browser/`;
- headed launch with Chromium sandbox enabled;
- manual login + fresh-process auth persistence;
- source materialization/hash/word-count gates;
- one-working-tab normalization and explicit cleanup of extras;
- self-updating wrapper re-exec when `git pull` changes the running launcher;
- recovery-before-repeat for ambiguous paid work;
- authenticated `history-list` + exact `/api/history/<uuid>/` binding;
- current long-document structured result extraction from `response.overall`;
- local deterministic suite on the final owner run: **200/200 passed**;
- final wrapper result: `RECOVER_RESUME_RESULT=complete`.

Public code-only CI for the structured-result repair also passed its full test suite, lesson closeout, repository audit, and workflow-policy gate before the final owner run.

## Current long-document contract

Observed Pangram web-app surfaces:

- report page: `https://www.pangram.com/history/<uuid>`;
- report data: `https://web.pangram.com/api/history/<uuid>/`;
- list data: `https://web.pangram.com/api/history-list/`;
- submitted document identity is available in the stored record `prompt`;
- document-level structured detector output is available under `response.overall` for these validated runs;
- current long-document reports need not expose the older per-segment word-count layout;
- `prediction_prob` is retained as raw provenance only and is **not** interpreted as the AI fraction.

Accepted stored-text identity modes remain bounded to exact UTF-8, line-ending normalization, terminal-newline normalization, or outer-whitespace normalization with identical word count. Fuzzy similarity and collapsed interior whitespace remain invalid identity proofs.

## Known evidence quirks / non-blockers

- The inherited generic `runner_version` field still reads `pangram-gui-browserbase-v1`; the receipt separately records `transport: local_playwright` and `transport_runner_version: pangram-gui-local-playwright-v1`. Do not misclassify the transport from the inherited compatibility field alone.
- Recovered Part 1 has an empty visible report-body artifact and therefore a null top-level detector-version field, while its exact stored structured result records Pangram 4.0 / `STAGE_SUCCESS`. The structured stored result is the score authority for this recovery.
- Both current long-document PDFs use the Playwright print fallback rather than a Pangram-native download. This is explicitly recorded provenance, not native-PDF equivalence.
- Part 2's Pangram headline is `AI Detected` even though its structured fractions are ~10.17% AI / ~89.83% Human; preserve both fields rather than normalizing the headline by intuition.

## Operational rule going forward

For a new exact document boundary:

1. check the content-addressed result cache and ambiguity ledger first;
2. if an ambiguous paid call exists, recover from authenticated stored history before any repeat;
3. reserve/push paid-call accounting before a new detector click;
4. attach stored-history capture before submission;
5. accept completion only after exact/bounded document identity and explicit structured detector result are both bound;
6. persist the receipt/PDF/Git evidence before another paid input;
7. keep the persistent browser session bounded to one working tab.

The self-hosted API should normally be preferred when visual GUI evidence is unnecessary, but the GUI path is now independently live-certified.

## Next repository action

- Update PR #78's description to reflect completed live validation.
- Keep the PR stack intact pending an explicit promotion/merge decision for PR #35 and PR #78.
- Do not spend another Pangram call merely to prove the same two exact halves again.
