# Pangram GUI Browserbase project-ID correction — 2026-08-17

## Authority / trigger

Joel supplied current Browserbase onboarding material on 2026-08-17 stating that `BROWSERBASE_API_KEY` alone identifies the project and workers must not ask for or set `BROWSERBASE_PROJECT_ID`.

The supplied API key is a secret and is **not** copied into this repository or this state file.

## Verification

Current Browserbase documentation is internally uneven: the standalone older `Create a Context` API-reference page still shows `projectId`, while the current Contexts guide shows context creation with the SDK using only the API key and cURL `POST /v1/contexts` with `{}`. Current session creation likewise documents project inference from the API key when no project ID is supplied.

For this tooling, follow the current Contexts/session guidance and Joel's onboarding material: API-key-only project resolution.

## Implemented correction

The stale project-ID requirement has been removed from the development runner:

- `BrowserbaseConfig` no longer has `project_id`;
- `BROWSERBASE_PROJECT_ID` is no longer read or validated;
- the old project-if-context-missing gate is gone;
- `build_context_payload()` returns `{}`;
- `BrowserbaseRestClient.create_context()` takes no project argument;
- `bootstrap_login()` creates a Context using only the API key when no Context ID is supplied;
- the CLI, runbook, and implementation specification no longer ask for or require a Project ID;
- the GitHub workflow continues to require only `BROWSERBASE_API_KEY` and the persistent `BROWSERBASE_CONTEXT_ID` for unattended runs.

## TDD evidence

The correction was made test-first.

1. `tests/test_gui_browserbase.py` was changed to require API-key-only Context creation and to reject any surviving `project_id` field.
2. The full repository test suite then failed at the new Browserbase tests, establishing the RED gate.
3. The config/REST/bootstrap implementation was corrected without changing Pangram interaction selectors or detector logic.
4. The CLI and documentation were aligned with the corrected contract.
5. At current branch head `5b0fcece499901cf0527d7b6c26351cff5028f13`, the `Lesson integrity` workflow reports the full test suite as successful. The workflow's overall red status is the existing research-closeout gate for an intentionally open branch, not a test failure. Repository workflow policy is successful.

## Context requirement that remains

`BROWSERBASE_CONTEXT_ID` is still needed for **unattended Pangram runs after bootstrap**, because the whole point is to reuse the authenticated Pangram browser state. Bootstrap may create the Context automatically from the API key and return its ID.

## Live setup

The one-time live sequence is now:

1. API key only.
2. Create/reuse a Browserbase Context.
3. Open a persistent session and Pangram login page.
4. Joel completes Pangram login in Live View once.
5. Close the session with persistence enabled.
6. Reuse the returned Context ID for unattended Pangram runs.

No repository secret or environment placeholder named `BROWSERBASE_PROJECT_ID` should exist.

## Current status / next safe action

**Implementation/test status: complete. Live certification: pending.**

The remaining task is one real Browserbase bootstrap plus Pangram login, followed by a small smoke measurement. Until that succeeds, do not claim the current Pangram selectors, persistence across a second session, or native-PDF capture are production-verified.

The API key must remain outside GitHub content and logs.