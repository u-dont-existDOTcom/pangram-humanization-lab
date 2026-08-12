# Pangram Async API Authentication/Transport Review — 2026-08-11

## Trigger

On the target Zorin machine, installer live smoke reached Pangram and received HTTP 401 with both the pre-existing key and a freshly entered replacement key. The replacement key was correctly exported into the retry process; repeated 401 therefore required inspection of the HTTP contract rather than another credential prompt.

## Root cause

The runtime's async Pangram client still used an older/incorrect transport contract:

- `Authorization: Bearer <key>`;
- `GET /models`;
- `POST /task` with a `model` field.

Current Pangram async API documentation for `text.external-api.pangram.com` specifies:

- `x-api-key: <key>`;
- `POST /task` with `text` and `public_dashboard_link`;
- `GET /task/{task_id}` for polling;
- 401 = missing/invalid key, 402 = insufficient credits, 403 = authenticated key does not own the task, 404 = task absent.

The docs do not expose a `/models` endpoint or a request-time model selector.

## Repair

- `PangramClient` now authenticates with `x-api-key`.
- Submission no longer sends the undocumented `model` field.
- Live smoke no longer calls `/models`. It probes `GET /task/00000000-0000-0000-0000-000000000000`; 200/403/404 establish that authentication reached the task API without creating a billable task.
- 401 invalid-key handling remains secret-safe. A 403 while polling a checkpointed task is treated as task ownership (for example after credential refresh): the stale task is cleared and the same candidate is resubmitted under the still-valid key. 402 is surfaced separately as `PANGRAM_CREDITS` and is never sent to Codex repair.
- The existing Pangram-4 semantic gate remains unchanged: a real candidate counts as detector-passing only when the terminal result reports version `4.0`, `prediction_short=Human`, zero AI fraction, zero AI-assisted fraction, and no AI/assisted windows.
- If the server authenticates but returns another version such as `3.3`, execution stops with `bounded_detector_contract_stop`, recording required version `4.0` and the returned version. It does not silently substitute the detector and does not ask Codex to alter the policy.

## Validation planes

- Deterministic transport/header/payload tests: passed.
- Zero-task auth-probe behavior: passed.
- 401 credential and 402 account-action classification: passed.
- Async task checkpoint/resume behavior: regression-covered.
- Non-v4 fail-closed behavior: passed.
- Full build-container suite before freeze: **235 passed, 1 dependency-gated LangGraph module skip**.
- Target-machine Pangram authentication/version result: pending the corrected release; no live Pangram-4 success is claimed yet.
