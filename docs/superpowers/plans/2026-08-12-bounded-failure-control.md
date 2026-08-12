# Bounded Failure Control Implementation Plan

> **Execution:** Use `superpowers:executing-plans`; implement every task test-first in this checkout. Do not delegate article or policy decisions. Check off tasks only after the listed verification succeeds.

**Goal:** Make the reproduced semantic-gate, generation-boundary, repair-loop, and provider-failover failure impossible while preserving the user's existing `.state` and P0 content.

**Architecture:** Add deterministic normalization at each external-model boundary, bind generation decisions to a canonical accepted boundary, normalize every machine failure into safe evidence, and make repair/provider retries idempotent by durable signatures and typed outcomes.

**Baseline:** remote commit `042b425cd5d2c2fadf4dbce84dc21650e0c89f0b`; local reconstructed baseline commit `5b37644bfbdebd4a12f1a6ea6c284f3ec425148c` with identical tree `01c0822d4e42092f402c7976ba58f7f821516fd7`.

## Global constraints

- Article, owner-gold, semantic-gold, policy, project inputs, and promoted learning remain untouched.
- State additions are optional and default-safe for the existing SQLite checkpoint.
- Do not weaken fidelity, cold-audit, regression, repair-review, or Pangram v4 Human/zero-AI gates.
- Use content-addressed references and allowlisted fields; never persist raw decision prose in traces.
- Each production change follows a focused RED test, minimal GREEN implementation, relevant regression slice, and commit.
- Run tests with service keys blank unless the test explicitly supplies a fake provider.

## Task 1: Fail-closed semantic escalation

**Files:** `src/authorial_flow/runtime.py`, `src/authorial_flow/state.py`, `tests/integration/test_runtime_dependencies.py`, `tests/unit/test_model_adapters.py`.

- [ ] Add RED tests proving an unknown natural-language escalation and `FAIL+BASIC` return an owner diagnostic interrupt, never `represented`.
- [ ] Add a RED test for `owner_question + research_trigger`: owner resolution must not erase pending research.
- [ ] Constrain the representation schema enum and implement independent runtime normalization/required-action routing.
- [ ] Replace the owner-answer forced PASS with explicit resolution of only the owner requirement.
- [ ] Run `python -m pytest -q tests/integration/test_runtime_dependencies.py tests/unit/test_model_adapters.py`.
- [ ] Commit `fix: fail closed on semantic escalation`.

## Task 2: Boundary-scoped generation and feasible stopping

**Files:** create `src/authorial_flow/nodes/boundary.py`; modify `src/authorial_flow/runtime.py`, `src/authorial_flow/state.py`, `src/authorial_flow/nodes/flow.py`; add `tests/unit/test_generation_boundary.py`; modify `tests/integration/test_runtime_dependencies.py`.

- [ ] Add RED unit tests for stable boundary identity and identity changes on move, coverage, graph version, or program version.
- [ ] Add RED integration tests for stale prior pressure not governing a new boundary; retry persisting current pressure/boundary; `STOP_BEFORE_CANDIDATE` stopping when coverage is complete; rollback when required units remain; fail-closed `POLICY_CONTRADICTION` when rollback is unsafe; and pre-accept rejection of a premature arrival.
- [ ] Implement the canonical boundary helper and add optional boundary/decision fields to state.
- [ ] Tag pressure and edge results; persist current pressure on every retry.
- [ ] Route current-boundary `STOP_BEFORE_CANDIDATE` through stop/rollback/fail-closed control, not writer retry.
- [ ] Reject an arrival candidate whose post-candidate coverage leaves mandatory units unresolved.
- [ ] Run `python -m pytest -q tests/unit/test_generation_boundary.py tests/unit/test_flow_edges.py tests/integration/test_runtime_dependencies.py`.
- [ ] Commit `fix: bind generation decisions to accepted boundaries`.

## Task 3: Normalize returned failures and safe decision traces

**Files:** `src/authorial_flow/runtime.py`, `src/authorial_flow/repair/evidence.py`, `src/authorial_flow/work_feed.py`, `src/authorial_flow/supervisor.py`, `src/authorial_flow/state.py`, `tests/repair/test_failure_evidence.py`, `tests/unit/test_work_feed.py`, `tests/unit/test_supervisor.py`, `tests/integration/test_runtime_dependencies.py`.

- [ ] Add RED tests that a node-returned `machine_failure` receives origin and dereferenceable evidence while preserving its declared class.
- [ ] Add RED tests for a decision trace containing hashes/counts/enums/confidences and excluding raw source, candidate, prompts, and supplied secret values.
- [ ] Factor exception/returned-failure evidence creation through one normalizer and avoid duplicate evidence.
- [ ] Add `decision.trace` allowlist/rendering and snapshot/evidence fields.
- [ ] Run `python -m pytest -q tests/repair/test_failure_evidence.py tests/unit/test_work_feed.py tests/unit/test_supervisor.py tests/integration/test_runtime_dependencies.py`.
- [ ] Commit `fix: preserve safe evidence for all machine failures`.

## Task 4: Capability-aware provider failover and lazy services

**Files:** `src/authorial_flow/models/common.py`, `src/authorial_flow/models/claude_cli.py`, `src/authorial_flow/models/codex_cli.py`, `src/authorial_flow/runtime.py`, `scripts/live_smoke.py`, `tests/unit/test_model_adapters.py`, `tests/integration/test_runtime_dependencies.py`, `tests/integration/test_live_smoke.py`.

- [ ] Add RED adapter tests for typed auth, unsupported-model, invalid-schema, contract, transient, and unknown classifications; deterministic equivalent attempts stop while a materially different/transient fallback remains possible.
- [ ] Extend `ModelAttempt` compatibly with `failure_kind` and `capability_signature`; classify bounded stdout/stderr/error text locally.
- [ ] Deduplicate configured equivalent profiles and stop deterministic retries according to policy.
- [ ] Validate runtime schemas before spawn and add schema-inventory plus one structured probe per configured profile to live smoke.
- [ ] Make research and Pangram provider construction lazy even when ambient keys exist.
- [ ] Run `python -m pytest -q tests/unit/test_model_adapters.py tests/integration/test_runtime_dependencies.py tests/integration/test_live_smoke.py`.
- [ ] Commit `fix: make provider failover capability aware`.

## Task 5: Idempotent repair outcomes

**Files:** `src/authorial_flow/repair/schemas.py`, `src/authorial_flow/repair/planner.py`, `src/authorial_flow/repair/verify.py`, `src/authorial_flow/runtime.py`, `src/authorial_flow/state.py`, `src/authorial_flow/work_feed.py`, `tests/repair/test_repair_pipeline.py`, `tests/integration/test_repair_resume.py`.

- [ ] Add RED tests that repairable plans require at least one exact safe pytest command and prose descriptions stop before review/executor.
- [ ] Add RED tests for canonical signatures, duplicate suppression on unchanged evidence/program, history in the next planner context, and explicit `APPLIED_VERIFIED`, `STAGED_FOR_OWNER`, `REJECTED_WITH_REASON`, `NON_APPLICABLE_STOP` events/state.
- [ ] Implement local plan validation before review, canonical signature/history, bounded feedback, and typed outcomes.
- [ ] Ensure a duplicate signature returns non-applicable without creating a worktree or invoking a reviewer/executor.
- [ ] Run `python -m pytest -q tests/repair tests/integration/test_repair_resume.py`.
- [ ] Commit `fix: make autonomous repair idempotent`.

## Task 6: Release, migration, and exact verification

**Files:** `src/authorial_flow/version.py`, `pyproject.toml`, `README.md`, `docs/migration-cutover.md`, `docs/release-checklist.md`, release manifest/checksum files and tests as required.

- [ ] Bump to `1.2.0-dev1` and document the state-preserving upgrade and new fail-closed statuses.
- [ ] Run focused slices from Tasks 1–5, then `env -u PANGRAM_API_KEY -u BRAVE_SEARCH_API_KEY -u OPENAI_API_KEY -u ANTHROPIC_API_KEY .venv/bin/python -m pytest -q`.
- [ ] Run compile/build/install checks and the repository's release-package regression.
- [ ] Copy the incident SQLite/artifacts to a temporary state root and verify it opens without migration or destructive rewrite.
- [ ] Review `git diff --check`, protected-path diff, secrets scan, and all test output.
- [ ] Commit `release: authorial flow graph 1.2.0-dev1`.
- [ ] Publish a versioned Git install branch and draft PR, verify the remote tree equals the local Git tree, and provide one idempotent install/upgrade command that backs up the old branch and preserves `.state`.

