# Pangram GUI Browserbase project-ID correction — 2026-08-17

## Authority / trigger

Joel supplied current Browserbase onboarding material on 2026-08-17 stating that `BROWSERBASE_API_KEY` alone identifies the project and workers must not ask for or set `BROWSERBASE_PROJECT_ID`.

The supplied API key is a secret and is **not** copied into this repository or this state file.

## Verification

Current Browserbase documentation is internally uneven: the standalone older `Create a Context` API-reference page still shows `projectId`, while the current Contexts guide shows context creation with the SDK using only the API key and cURL `POST /v1/contexts` with `{}`. Current session creation likewise documents project inference from the API key when no project ID is supplied.

For this tooling, follow the current Contexts/session guidance and Joel's onboarding material: API-key-only project resolution.

## Required code correction

The current development implementation is stale in these places and must be changed before live bootstrap:

- remove `project_id` from `BrowserbaseConfig`;
- stop reading `BROWSERBASE_PROJECT_ID`;
- remove `require_project_if_context_missing`;
- replace `build_context_payload(project_id)` with an empty context-create payload `{}`;
- change `BrowserbaseRestClient.create_context(project_id)` to `create_context()`;
- change `bootstrap_login()` so a missing context creates one using only the API key;
- remove all CLI/runbook/workflow language that asks for or requires a Project ID;
- update tests first so the stale project-ID requirement fails before implementation is changed.

## Context requirement that remains

`BROWSERBASE_CONTEXT_ID` is still needed for **unattended Pangram runs after bootstrap**, because the whole point is to reuse the authenticated Pangram browser state. Bootstrap may create the Context automatically from the API key and return its ID.

## Live setup

The one-time live sequence becomes:

1. API key only.
2. Create/reuse a Browserbase Context.
3. Open a persistent session and Pangram login page.
4. Joel completes Pangram login in Live View once.
5. Close the session with persistence enabled.
6. Reuse the returned Context ID for unattended Pangram runs.

No repository secret or environment placeholder named `BROWSERBASE_PROJECT_ID` should exist.

## Next safe action

Apply the correction test-first on `agent/pangram-browserbase-gui-automation-20260817`, run the complete test suite and workflow-policy audit, then perform the first live bootstrap using the API key without ever committing or printing the key.