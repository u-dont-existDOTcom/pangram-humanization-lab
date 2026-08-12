# Autonomous Self-Healing Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make machine-fixable Authorial Flow failures repair themselves with evidence-rich, test-first Codex patches in isolated worktrees, promote only verified repairs, and resume the exact same LangGraph/SQLite conceptual thread automatically.

**Architecture:** Extend the existing `FailureRecord`/repair planner/executor/verifier/worktree pipeline rather than add a second supervisor. Persist a dereferenceable `RepairEvidenceBundle`, materialize it only inside disposable repair worktrees, enforce RED-before-GREEN repair evidence and credential/protected-path isolation, use the existing one-fix verifier in production, record promotion lineage, then restart the CLI with `resume` against the unchanged `current-thread.json` thread ID. A resolved repair clears failure markers and deterministically re-enters the failed graph stage under the new program image.

**Tech Stack:** Python 3.12+, Pydantic, LangGraph + SQLite checkpointer, pytest, Git worktrees, Claude CLI, Codex CLI.

## Global Constraints

- Preserve owner/project inputs, policy snapshots, gold/learning data, Pangram baselines, `.state/learning/`, and credential material.
- Repair Codex never receives `PANGRAM_API_KEY` or `BRAVE_SEARCH_API_KEY`.
- Owner judgment remains an interrupt; machine repair cannot invent an owner-question escape hatch.
- Repairs are isolated, regression-first, bounded, independently reviewed, and fast-forward promoted only after all gates pass.
- Exactly one implementation correction is allowed per repair round by default.
- A promoted Python repair restarts with `resume` on the exact existing thread ID; it must never call `run <source>` or reseed conceptual state.
- Exhausted repair produces an evidence package and `bounded_machine_stop`, never a request that Joel relay logs.
- The known Claude structured-output failure is a required regression case and must be fixed without weakening schema validation.
- Project instructions must remain under 8,000 characters and the release build must pass its clean-package verifier.

---

### Task 1: Repair Claude Structured-Output Contract

**Files:**
- Modify: `src/authorial_flow/models/claude_cli.py`
- Test: `tests/unit/test_model_adapters.py`

**Interfaces:**
- Consumes: `ModelCall(prompt, schema, role)`.
- Produces: Claude CLI stdin that includes the requested JSON schema when `schema` is present, while preserving the existing fail-closed local schema validation.

- [ ] **Step 1: Write a failing adapter regression** proving a schema-constrained Claude call serializes the expected schema into the instruction sent to Claude and does not leak controller credentials.
- [ ] **Step 2: Run only that test and verify RED** because the current adapter sends only `call.prompt`.
- [ ] **Step 3: Implement the minimal schema instruction** by appending a canonical JSON representation of `call.schema` plus an explicit “return one JSON object matching this schema” requirement to the Claude stdin payload. Do not change `--output-format json` parsing or local validation.
- [ ] **Step 4: Run adapter unit tests and verify GREEN.**
- [ ] **Step 5: Commit** `fix: constrain Claude structured runtime roles`.

### Task 2: Evidence-Complete Failure Bundles

**Files:**
- Create: `src/authorial_flow/repair/evidence.py`
- Modify: `src/authorial_flow/failures.py`
- Modify: `src/authorial_flow/runtime.py` (`_guarded_node`)
- Test: `tests/unit/test_failure_routing.py`
- Test: `tests/repair/test_repair_pipeline.py`

**Interfaces:**
- Produces: `RepairEvidenceBundle` with failure record, thread/checkpoint/program/source/task state, provider attempt metadata, bounded dereferenced stdout/stderr, expected schema when available, and safe runtime context.
- Produces: `build_failure_evidence(...) -> RepairEvidenceBundle` and `materialize_evidence_bundle(...)` in a repair-only directory.

- [ ] **Step 1: Write failing tests** for provider failure evidence containing provider/model/role/request identity, dereferenced stdout/stderr text, expected schema, thread ID, and no secret values.
- [ ] **Step 2: Run the focused tests and verify RED.**
- [ ] **Step 3: Add the immutable evidence models/helper.** Bound individual provider text fields to a deterministic maximum and redact known secret values/keys.
- [ ] **Step 4: Extend `_guarded_node`** to capture provider metadata/schema from exceptions when available and persist a repair-evidence artifact alongside the compatibility `FailureRecord`; graph state points `failure_record_ref`/`last_error_ref` to the evidence bundle used by repair.
- [ ] **Step 5: Re-run focused tests and verify GREEN.**
- [ ] **Step 6: Commit** `feat: persist dereferenceable repair evidence`.

### Task 3: Evidence-Aware Planner and Test-First Repair Executor

**Files:**
- Modify: `src/authorial_flow/repair/planner.py`
- Modify: `src/authorial_flow/repair/executor.py`
- Modify: `src/authorial_flow/repair/schemas.py`
- Modify: `src/authorial_flow/repair/protection.py`
- Test: `tests/repair/test_repair_pipeline.py`
- Test: `tests/repair/test_worktree_protection.py`

**Interfaces:**
- `RepairPlanner.plan(failure_context: str)` continues to consume text, but production supplies full evidence JSON rather than refs-only metadata.
- `RepairExecutor.apply(..., evidence_bundle_text: str = "") -> ImplementationResult` materializes evidence and requires test-first repair behavior.
- `ImplementationResult` adds repair transcript/RED/GREEN evidence refs while preserving existing fields.

- [ ] **Step 1: Write failing tests** showing planner prompt receives dereferenced evidence; executor strips Pangram/Brave credentials; repair-only evidence is materialized under an excluded directory; protected paths include owner/policy/learning inputs; and successful implementation must report RED-before-GREEN evidence.
- [ ] **Step 2: Run focused repair tests and verify RED.**
- [ ] **Step 3: Extend executor prompt/contract** to require the smallest regression, targeted RED run, minimal patch, targeted GREEN run, and explicit markers/command output in the Codex transcript. Persist the transcript and parse/store RED/GREEN evidence refs; fail closed when a successful Codex exit lacks test-first evidence.
- [ ] **Step 4: Expand protection coverage** to policy and `.state/learning/` prefixes plus all project owner/gold inputs. Keep `supervisor-evidence/` excluded from source-hardcoding promotion and ensure it never becomes part of the candidate commit.
- [ ] **Step 5: Re-run focused tests and verify GREEN.**
- [ ] **Step 6: Commit** `feat: require test-first isolated Codex repairs`.

### Task 4: Production One-Fix Verification and Promotion Gates

**Files:**
- Modify: `src/authorial_flow/repair/verify.py`
- Modify: `src/authorial_flow/repair/executor.py`
- Modify: `src/authorial_flow/runtime.py` (`_production_repair_cycle`)
- Test: `tests/integration/test_repair_resume.py`
- Test: `tests/repair/test_repair_pipeline.py`

**Interfaces:**
- `RepairVerifier` runs compile, plan-declared safe targeted tests, unit/regression, integration, and full-suite gates before protection + independent diff review.
- `RepairExecutor.correct(...)` performs the single bounded correction using actual diff and failed verification evidence.
- Production invokes `verify_with_one_fix` exactly once per repair round.

- [ ] **Step 1: Write failing integration tests** for: first candidate fails then exactly one correction passes/promotes; correction fails again and does not promote; full-suite failure/rejected independent review/protected mutation blocks promotion.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Add safe plan-test command normalization** and full-suite verification while preventing arbitrary/network commands.
- [ ] **Step 4: Add the executor correction method** that receives approved plan, candidate diff, failed command/stdout/stderr and prior transcript refs, edits the same worktree, commits one correction, and returns evidence.
- [ ] **Step 5: Wire `verify_with_one_fix` into production** with `config.implementation_fix_attempts == 1`; persist verification artifacts and promotion metadata.
- [ ] **Step 6: Verify focused integration tests GREEN.**
- [ ] **Step 7: Commit** `feat: verify and correct repairs before promotion`.

### Task 5: Same-Thread Repair Restart and Retry Semantics

**Files:**
- Modify: `src/authorial_flow/cli.py`
- Modify: `src/authorial_flow/nodes/repair.py`
- Modify: `src/authorial_flow/routing.py`
- Modify: `src/authorial_flow/state.py`
- Modify: `src/authorial_flow/runtime.py`
- Test: `tests/integration/test_repair_resume.py`
- Test: `tests/integration/test_cli.py`
- Test: `tests/integration/test_graph_resume.py`

**Interfaces:**
- `restart_argv(config) -> [..., "resume"]` for autonomous promoted repairs.
- Repair state records lineage and `repair_resume_node` / resolved-failure metadata without changing `thread_id`.
- `route_after_repair` re-enters the repaired originating stage after restart rather than finalizing/reseeding.

- [ ] **Step 1: Write failing tests** proving restart argv uses `resume`; parent `thread_id` remains byte-for-byte identical; `current-thread.json` is unchanged; accepted moves/source representation survive SQLite reopen; repaired origin is retried; resolved markers do not immediately re-trigger repair.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Change CLI repair restart** to append lineage then `exec ... resume`, never `_resolve_thread`/`run`.
- [ ] **Step 4: Persist repair continuation state** (`repair_resume_node`, resolved failure ref/class, repair commit/program version) and clear active failure markers only after promotion is checkpointed.
- [ ] **Step 5: Route post-repair continuation** to the original machine stage (`regressions`, `representation`, `generation`, `cold_audit`, `freeze`, `detector`, or `owner_learning`) under the new program image; reject unsafe/unknown origins to regressions rather than finalize.
- [ ] **Step 6: Run CLI/repair/real-LangGraph tests and verify GREEN where dependencies are available.**
- [ ] **Step 7: Commit** `feat: resume repaired code on the same graph thread`.

### Task 6: Bounded Exhaustion Evidence and Repair Observability

**Files:**
- Modify: `src/authorial_flow/nodes/repair.py`
- Modify: `src/authorial_flow/runtime.py`
- Modify: `src/authorial_flow/events.py`
- Modify: `src/authorial_flow/cli.py` if heartbeat labels require it
- Test: `tests/integration/test_repair_resume.py`
- Test: `tests/unit/test_process_runner.py`

**Interfaces:**
- Repair stages journal high-level `repair:*` phases.
- Exhaustion returns `bounded_machine_stop` plus a dereferenceable evidence package ref and no owner-debug interrupt.

- [ ] **Step 1: Write failing tests** for repair phase events and exhausted-machine evidence without owner courier/debug instructions.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Add high-level repair journal/heartbeat events** for diagnose, plan-review, codex-red/patch, verify-targeted/full, correction-1, promote, restart-same-thread.
- [ ] **Step 4: Persist exhausted repair evidence package ref** and keep `authorial_information_missing=false` machine failures out of owner interrupts.
- [ ] **Step 5: Verify focused tests GREEN.**
- [ ] **Step 6: Commit** `feat: expose bounded autonomous repair progress`.

### Task 7: Acceptance, Release, and Exact-Package Verification

**Files:**
- Modify: `src/authorial_flow/acceptance.py`
- Modify: `README.md`
- Modify: `PASTE_INTO_PROJECT_INSTRUCTIONS.txt` only if needed and still < 8,000 chars
- Modify: release manifest through `scripts/build_release.py`
- Test: all repository tests
- Test: release verifier/tests

**Interfaces:**
- Acceptance matrix distinguishes deterministic self-heal verification from live Claude/Codex/Pangram/target-machine validation.
- Release ZIP is built from the exact verified commit and declares its source commit.

- [ ] **Step 1: Update acceptance/docs** to state autonomous Codex repair behavior, same-thread restart semantics, bounded stop behavior, and live-validation boundaries.
- [ ] **Step 2: Run `python -m compileall -q src tests`.**
- [ ] **Step 3: Run targeted repair/model/CLI suites.**
- [ ] **Step 4: Run `python -m pytest -q` and require zero failures.**
- [ ] **Step 5: Verify project-instruction character count < 8,000.**
- [ ] **Step 6: Commit** `docs: document autonomous repair acceptance`.
- [ ] **Step 7: Run a cold diff/security review** against the approved design: no protected mutations, no secret exposure, no source hardcoding, no detector-authority weakening, no unrelated refactor.
- [ ] **Step 8: Build the release ZIP with `scripts/build_release.py`, then verify clean extraction/compile/release metadata/checksums.**
- [ ] **Step 9: Record remaining live validation planes**: actual target-machine Claude/Codex repair, SQLite reopen after promoted live repair, Pangram, and owner interrupt continuation.

### Task 8: Bootstrap Self-Healing for Installer/Test Failures

**Files:**
- Create: `src/authorial_flow/bootstrap_repair.py`
- Modify: `INSTALL-AND-RUN.sh`
- Modify: `tests/integration/test_graph_resume.py`
- Modify: `tests/release/test_release_package.py`
- Create: `tests/integration/test_bootstrap_repair.py`

**Interfaces:**
- `run_preflight(command, config, services=None, repair_cycle_factory=None) -> int` runs the exact installer preflight, persists bounded failure evidence, invokes the existing isolated repair cycle on failure, reruns the exact command after verified promotion, and returns nonzero only after bounded repair exhausts.
- `python -m authorial_flow.bootstrap_repair --root . -- <command...>` is the installer-facing entry point.
- The installer reconciles the release Git baseline before invoking repairable pytest preflight so worktree promotion has a clean authoritative base.

- [ ] **Step 1: Correct the live SQLite regression assertion** to treat optional `AuthorialState` keys as optional after replay; the successful replay must preserve conceptual state and clear/omit stale failure metadata.
- [ ] **Step 2: Write failing bootstrap tests** proving a failed preflight creates evidence, invokes one isolated repair cycle, reruns after promotion, succeeds without user log relay, and packages evidence on bounded exhaustion.
- [ ] **Step 3: Write failing release-contract tests** proving `reconcile_release_baseline.py` runs before repairable pytest and the installer invokes `authorial_flow.bootstrap_repair` rather than raw pytest.
- [ ] **Step 4: Implement `bootstrap_repair.py`** by reusing `RuntimeServices`, the production repair cycle, artifact store, bounded repair rounds, and evidence-package builder. Preserve command/stdout/stderr/program/source context and strip credentials through the existing repair executor.
- [ ] **Step 5: Update `INSTALL-AND-RUN.sh`** so release baseline reconciliation precedes the repairable preflight and the bootstrap controller owns the pytest command.
- [ ] **Step 6: Run focused tests, then the full suite, release verifier, and clean-extraction build.**
- [ ] **Step 7: Build a new exact-commit release.**
