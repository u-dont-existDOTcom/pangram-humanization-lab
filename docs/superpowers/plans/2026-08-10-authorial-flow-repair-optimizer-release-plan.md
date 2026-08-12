# Authorial Flow Graph v1 — Repair, Optimizer, and Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make machine failures self-repairing, add bounded evaluator/program optimization without contaminating owner labels, and prove a clean one-command release/cutover on the target Zorin environment.

**Architecture:** Keep executable repair outside article-generation logic but inside the same LangGraph runtime. Repairs happen only in disposable git worktrees, with protected-file hashes, source-hardcoding checks, tests, and independent plan/diff review before promotion. The optimizer changes evaluator/program instructions only and must pass development/validation/locked gates. Release verification runs from a clean ZIP and distinguishes mocked, live-provider, detector, and owner-interrupt evidence.

**Tech Stack:** Core runtime stack, git worktrees, pytest, optional DSPy/GEPA extra. No required OpenHands dependency.

## Global Constraints

- Machine/runtime/provider/regression failures are machine work; only genuinely authorial decisions interrupt the user.
- Repair agents cannot modify protected source, policy authority, owner labels, learning records, or Pangram baselines.
- Repair agents never receive Pangram credentials.
- A repair must be small, causal, general, tested, reviewed, and non-source-specific.
- Model-provider failure during repair invokes bounded provider fallback/retry, not user log collection.
- Optimizer may modify evaluator/program instructions but not article prose or owner ground truth.
- Development cases may guide optimization; locked-test cases may not be visible during proposal generation.
- Detector-only improvement is a failed optimization if fidelity/coherence/editorial quality regresses.
- Release acceptance requires exact clean-ZIP installation and resume behavior under `~/Téléchargements`.
- A release reports exactly which validation planes are mocked, live, detector-confirmed, and owner-confirmed.

---

## File Map

- `src/authorial_flow/failures.py` — failure taxonomy and machine-vs-owner classification.
- `src/authorial_flow/repair/worktree.py` — isolated branch/worktree lifecycle.
- `src/authorial_flow/repair/protection.py` — protected hashes/source-hardcoding/diff scope gates.
- `src/authorial_flow/repair/planner.py` — Codex repair-plan call and schema.
- `src/authorial_flow/repair/reviewer.py` — Claude review + Codex fallback.
- `src/authorial_flow/repair/executor.py` — Codex workspace-write implementation.
- `src/authorial_flow/repair/verify.py` — compile/tests/diff review/promotion.
- `src/authorial_flow/nodes/repair.py` — graph repair subgraph entry/rejoin.
- `src/authorial_flow/optimizer/program.py` — versioned prompt/program bundle.
- `src/authorial_flow/optimizer/evaluate.py` — partition-safe evaluation.
- `src/authorial_flow/optimizer/search.py` — bounded proposal/selection loop.
- `src/authorial_flow/optimizer/dspy_adapter.py` — optional extra adapter only.
- `src/authorial_flow/release.py` — deterministic release ZIP/manifest/checksums.
- `scripts/live_smoke.py` — explicit live-provider smoke suite.
- `tests/repair/`, `tests/optimizer/`, `tests/release/` — regression and release evidence.

---

### Task 1: Failure Taxonomy and Machine-vs-Owner Routing

**Files:**
- Create: `src/authorial_flow/failures.py`
- Modify: `src/authorial_flow/routing.py`
- Modify: `src/authorial_flow/state.py`
- Test: `tests/unit/test_failure_routing.py`

**Interfaces:**
- Produces: `FailureClass` = DETERMINISTIC_RUNTIME, PROVIDER_PLUMBING, REGRESSION_ARCHITECTURE, GENERATION_DEAD_END, SEMANTIC_DEVELOPMENTAL, RESEARCH_PROVIDER, FIDELITY, PANGRAM_ONLY, OWNER_JUDGMENT.
- Produces: `classify_failure(FailureRecord) -> FailureClass`
- Produces: `route_failure(FailureClass) -> "repair" | "owner_interrupt" | "bounded_stop"`.

- [ ] **Step 1: Write routing tests**

```python
# tests/unit/test_failure_routing.py
from authorial_flow.failures import FailureClass
from authorial_flow.routing import route_failure


def test_provider_failure_is_machine_repair():
    assert route_failure(FailureClass.PROVIDER_PLUMBING) == "repair"


def test_missing_authorial_meaning_is_owner_interrupt():
    assert route_failure(FailureClass.OWNER_JUDGMENT) == "owner_interrupt"


def test_pangram_only_failure_is_not_owner_question():
    assert route_failure(FailureClass.PANGRAM_ONLY) == "repair"
```

- [ ] **Step 2: Implement typed failure record**

Include originating node, exception/failure code, provider attempt refs, state checkpoint ID, source/program hashes, local gate state, and `authorial_information_missing: bool`.

- [ ] **Step 3: Implement deterministic first-pass classifier**

Do not ask an LLM to decide obvious categories such as child exit error, missing schema, timeout, failed regression, or Pangram non-Human. Use model classification only for ambiguous machine diagnostic boundaries; model cannot promote a machine failure to OWNER_JUDGMENT without `authorial_information_missing=True` from semantic-sanity/owner-question logic.

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_failure_routing.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/authorial_flow/{failures.py,routing.py,state.py} tests/unit/test_failure_routing.py
git commit -m "feat: classify machine and owner failures explicitly"
```

---

### Task 2: Disposable Git Worktree and Protected-File Gates

**Files:**
- Create: `src/authorial_flow/repair/__init__.py`
- Create: `src/authorial_flow/repair/worktree.py`
- Create: `src/authorial_flow/repair/protection.py`
- Test: `tests/repair/test_worktree_protection.py`

**Interfaces:**
- `WorktreeManager.create(repair_id) -> WorktreeRef`
- `WorktreeManager.discard(ref)`
- `WorktreeManager.promote(ref, commit_sha)`
- `ProtectedSnapshot.capture(root, protected_paths) -> ProtectedSnapshot`
- `validate_candidate_diff(base, candidate, source_texts) -> ProtectionReport`.

- [ ] **Step 1: Write worktree lifecycle test in temporary git repository**

```python
# tests/repair/test_worktree_protection.py
from pathlib import Path
from authorial_flow.repair.worktree import WorktreeManager


def test_repair_uses_separate_worktree(tmp_git_repo: Path):
    mgr = WorktreeManager(tmp_git_repo, tmp_git_repo / ".state" / "worktrees")
    ref = mgr.create("r001")
    assert ref.path != tmp_git_repo
    assert (ref.path / ".git").exists()
    mgr.discard(ref)
    assert not ref.path.exists()
```

- [ ] **Step 2: Write protected mutation/source-hardcoding tests**

Test mutation of `project/INPUT.md` or `project/HUMAN-FLOW-GOLD.json` returns hard failure. Add 70-character current-source span to production prompt and assert source-hardcoding detector rejects it. Allow generic code changes containing common function words.

- [ ] **Step 3: Implement worktree lifecycle using `git worktree add --detach`**

Create under `.state/worktrees/<repair_id>`. Record base commit SHA. Discard runs `git worktree remove --force` then `git worktree prune`. Promotion requires candidate commit SHA and fast-forward/cherry-pick policy defined by current branch state; refuse dirty main worktree.

- [ ] **Step 4: Implement protected snapshot and diff scanner**

Protected set includes policy snapshot, project source/requirements/context, owner/semantic gold, learning store, source baseline, and current accepted candidate artifacts. Compare exact hashes before/after. Source-hardcoding scan checks only added lines in production code/prompts, excluding test fixtures/evidence directories.

- [ ] **Step 5: Run tests**

Run: `pytest tests/repair/test_worktree_protection.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/authorial_flow/repair tests/repair/test_worktree_protection.py
git commit -m "feat: isolate repairs in protected git worktrees"
```

---

### Task 3: Repair Plan, Independent Review, Implementation, and Diff Review

**Files:**
- Create: `src/authorial_flow/repair/schemas.py`
- Create: `src/authorial_flow/repair/planner.py`
- Create: `src/authorial_flow/repair/reviewer.py`
- Create: `src/authorial_flow/repair/executor.py`
- Create: `src/authorial_flow/prompts/repair_plan.md`
- Create: `src/authorial_flow/prompts/repair_review.md`
- Create: `src/authorial_flow/prompts/diff_review.md`
- Test: `tests/repair/test_repair_pipeline.py`

**Interfaces:**
- `RepairPlan(repairable, diagnosis, patch_summary, target_files, rationale, tests, needs_owner_judgment, owner_question)`
- `ReviewDecision(verdict, reason, required_changes)`
- `RepairPlanner.plan(failure_context) -> RepairPlan`
- `RepairReviewer.review_plan(...)`, `review_diff(...)`
- `RepairExecutor.apply(worktree, plan) -> ImplementationResult`.

- [ ] **Step 1: Write plan/reviewer fallback tests**

Use fake Claude failure + fake Codex review success; assert provider recorded as `codex-fallback` and pipeline continues. Both providers fail → machine failure record, never owner interrupt.

- [ ] **Step 2: Implement schema-constrained Codex planning**

Use Core `CodexCLI` read-only call with repair context containing relevant code/evidence refs, not Pangram key or owner exemplar text. Plan may set `needs_owner_judgment=True`; reviewer must independently agree that missing information is authorial before routing owner-side.

- [ ] **Step 3: Implement Claude review using Core structured adapter**

Use same known-good stdin task topology and resolved model cache. On Claude provider failure, use schema-constrained read-only Codex reviewer and record fallback.

- [ ] **Step 4: Implement workspace-write Codex executor**

A separate controlled adapter permits `--sandbox workspace-write` only with cwd = disposable worktree. Prompt enumerates protected paths and tells Codex to run local nonnetwork tests but not Pangram.

- [ ] **Step 5: Implement actual diff review**

Generate `git diff --binary <base>...<candidate>` text artifact, run protection scan first, then independent reviewer. Reviewer checks plan adherence, unrelated refactor, authority weakening, checkpoint/credential regression, and detector-only degradation.

- [ ] **Step 6: Run tests**

Run: `pytest tests/repair/test_repair_pipeline.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/authorial_flow/repair src/authorial_flow/prompts/{repair_plan.md,repair_review.md,diff_review.md} tests/repair/test_repair_pipeline.py
git commit -m "feat: add reviewed autonomous repair pipeline"
```

---

### Task 4: Repair Verification, Promotion, and Graph Resume

**Files:**
- Create: `src/authorial_flow/repair/verify.py`
- Create: `src/authorial_flow/nodes/repair.py`
- Modify: `src/authorial_flow/graph.py`
- Modify: `src/authorial_flow/config.py`
- Test: `tests/integration/test_repair_resume.py`

**Interfaces:**
- `RepairVerifier.verify(worktree, plan) -> VerificationResult`
- Verification invokes compile, targeted tests, full hard regressions, integration subset, protected hashes, source-hardcoding scan, and diff review.
- Graph repair node returns new program version and resumes failed logical node from a new thread lineage/checkpoint compatible with unchanged protected project state.

- [ ] **Step 1: Write broken-patch repair test**

Fake first implementation introduces syntax error. Verifier fails compile; one bounded implementation-repair attempt fixes it; full verification passes; promotion occurs once.

- [ ] **Step 2: Implement deterministic verification commands**

Run in worktree:

```bash
python -m compileall -q src tests
pytest tests/unit tests/regression -q
pytest tests/integration -q
```

Then run protected/source-hardcoding gates and independent diff review. Capture each command as an artifact with exit code/stdout/stderr.

- [ ] **Step 3: Implement bounded repair budgets**

Config defaults: executable repair rounds 5; plan revisions 2; one implementation fix per candidate patch. Exhaustion creates bounded machine stop package, not owner question.

- [ ] **Step 4: Implement promotion transaction**

Before promotion assert main worktree clean and base commit unchanged. Promote reviewed candidate commit, increment graph program version, keep old checkpoint/evidence immutable, and start a new compatible thread lineage referencing the prior failure checkpoint as ancestry.

- [ ] **Step 5: Write resume integration test**

Start graph with deterministic regression bug, route to repair fake pipeline, promote fix, rerun hard regression, continue to next graph node automatically. Assert user-interrupt count remains zero.

- [ ] **Step 6: Run tests**

Run: `pytest tests/integration/test_repair_resume.py tests/repair -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/authorial_flow/{config.py,graph.py,nodes/repair.py,repair/verify.py} tests/integration/test_repair_resume.py
git commit -m "feat: verify promote and resume machine repairs"
```

---

### Task 5: Versioned Program Bundle and Partition-Safe Built-In Optimizer

**Files:**
- Create: `src/authorial_flow/optimizer/__init__.py`
- Create: `src/authorial_flow/optimizer/program.py`
- Create: `src/authorial_flow/optimizer/evaluate.py`
- Create: `src/authorial_flow/optimizer/search.py`
- Test: `tests/optimizer/test_optimizer_partitions.py`
- Test: `tests/optimizer/test_optimizer_quality_gate.py`

**Interfaces:**
- `ProgramBundle(id, prompt_hashes, evaluator_config, parent_id)`
- `EvaluationScore(hard_pass, target_metrics, fidelity_regressions, owner_regressions)`
- `OptimizerSearch.run(base_program, learning_store, rounds) -> ProgramCandidate | None`.

- [ ] **Step 1: Write locked-test isolation test**

```python
# tests/optimizer/test_optimizer_partitions.py

def test_proposal_builder_never_receives_locked_test_bodies(optimizer_fixture):
    proposal_input = optimizer_fixture.build_proposal_input()
    assert "LOCKED_SECRET_CASE_TEXT" not in proposal_input
    assert "locked-test" in optimizer_fixture.partition_manifest()
```

- [ ] **Step 2: Implement program bundle hashing**

Bundle includes exact prompt file hashes + evaluator aggregation config + graph compatibility version. Never modify prompts in place during search; each candidate is a content-addressed bundle under `.state/artifacts/`.

- [ ] **Step 3: Implement evaluation harness**

Evaluate development cases for search signal; validation after candidate proposal; locked-test only for final promotion. Owner-hard/fidelity failures force `hard_pass=False` regardless detector/aggregate metric.

- [ ] **Step 4: Write detector-only regression test**

Candidate program makes Pangram metric better but flips an owner LOCAL_EDGE case or fidelity case. Assert optimizer rejects promotion.

- [ ] **Step 5: Implement bounded search loop**

Codex/Claude may propose prompt/program deltas using only development summaries/cases. Max configured rounds 6. Each proposal gets provenance, diff, evaluation, and rationale. No automatic optimizer run in normal article path; invoke only from explicit optimizer command or machine repair when failure class says evaluator architecture and repair policy chooses optimizer.

- [ ] **Step 6: Run tests**

Run: `pytest tests/optimizer -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/authorial_flow/optimizer tests/optimizer
git commit -m "feat: add partition-safe evaluator optimizer"
```

---

### Task 6: Optional DSPy/GEPA Adapter Without Hot-Path Dependency

**Files:**
- Modify: `pyproject.toml`
- Create: `src/authorial_flow/optimizer/dspy_adapter.py`
- Test: `tests/optimizer/test_dspy_optional.py`

**Interfaces:**
- Extra: `[project.optional-dependencies].optimizer = ["dspy==3.2.1"]` based on the current stable PyPI release checked 2026-08-10; implementation rechecks primary docs before locking if the build date changes.
- `ClaudeCodexLM` adapter maps DSPy request to Core CLI adapters; never embeds API keys.

- [ ] **Step 1: Write optional-import test**

Without optimizer extra installed, importing normal `authorial_flow`/running CLI must succeed. Calling `load_dspy_optimizer()` raises a targeted message with install command rather than import failure at package import time.

- [ ] **Step 2: Re-verify the DSPy/GEPA API against primary docs before coding the adapter**

The planning baseline is stable `dspy==3.2.1` (checked on PyPI 2026-08-10). Record the exact build-time check in `docs/dependency-verification.md`; if the stable version changed, update the pin and lock file in the same commit rather than coding against remembered signatures.

- [ ] **Step 3: Implement lazy adapter**

DSPy import occurs inside factory function. LM calls delegate to Claude/Codex CLI wrappers so existing process observability/secret isolation applies.

- [ ] **Step 4: Test normal hot path without extra**

Run: `python -c 'import authorial_flow'` and full normal test suite in base env.

- [ ] **Step 5: Test optional extra in disposable venv**

Install `.[optimizer,test]`, run `tests/optimizer/test_dspy_optional.py`; no live optimizer call required.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/authorial_flow/optimizer/dspy_adapter.py tests/optimizer/test_dspy_optional.py docs/dependency-verification.md
git commit -m "feat: add optional DSPy optimizer adapter"
```

---

### Task 7: Deterministic Release Builder and Clean-ZIP Verification

**Files:**
- Create: `src/authorial_flow/release.py`
- Create: `scripts/build_release.py`
- Create: `tests/release/test_release_package.py`
- Create: `docs/release-checklist.md`

**Interfaces:**
- `build_release(repo_root, out_zip) -> ReleaseManifest`
- Release includes code, policy snapshot, project migration fixtures, lock file, launchers, README, project-instructions file, manifests/checksums; excludes `.state`, `.venv`, secrets, git internals, previous result ZIPs.

- [ ] **Step 1: Write release-member/executable tests**

```python
# tests/release/test_release_package.py
import zipfile


def test_release_contains_required_assets(release_zip):
    with zipfile.ZipFile(release_zip) as z:
        names = set(z.namelist())
        assert any(n.endswith("/INSTALL-AND-RUN.sh") for n in names)
        assert any(n.endswith("/requirements.lock") for n in names)
        assert any(n.endswith("/PASTE_INTO_PROJECT_INSTRUCTIONS.txt") for n in names)
        assert not any("/.state/" in n or "/.venv/" in n for n in names)
```

Also inspect `external_attr` executable bits for both shell launchers.

- [ ] **Step 2: Implement manifest/checksum builder**

Generate `MANIFEST.json` with path, size, SHA-256, executable flag, source commit SHA, graph/policy version. Generate `SHA256SUMS.txt`; build deterministic ZIP ordering and fixed timestamp where practical.

- [ ] **Step 3: Implement release verify command**

Unzip to fresh temp dir, verify checksums/member uniqueness/path traversal/executable bits/project-instruction char count, parse JSON policy/project manifests, then create disposable venv and run offline unit/regression tests using the lock if wheel/network setup is available in CI environment.

- [ ] **Step 4: Run release tests**

Run: `pytest tests/release/test_release_package.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/authorial_flow/release.py scripts/build_release.py tests/release/test_release_package.py docs/release-checklist.md
git commit -m "feat: build reproducible self-contained releases"
```

---

### Task 8: Live Smoke Harness and Provider/Detector Verification

**Files:**
- Create: `scripts/live_smoke.py`
- Create: `tests/live/README.md`
- Create: `docs/live-smoke-report-template.md`

**Interfaces:**
- `python scripts/live_smoke.py --claude --codex --pangram --research`
- Live tests are opt-in; ordinary `pytest` never spends model/detector/search quota.

- [ ] **Step 1: Implement Claude/Codex capability smoke calls**

Minimal prompts request fixed tiny JSON. Report CLI version, resolved model, duration, return code, artifact hashes. Do not print raw credentials.

- [ ] **Step 2: Implement Pangram `/models` + tiny candidate smoke**

Only submit candidate when `--pangram-submit` explicitly present; otherwise check `/models`. If submitting, verify task checkpoint/poll code on a harmless generated sentence and archive result.

- [ ] **Step 3: Implement research provider smoke**

Use harmless public query and/or direct URL fetch. Report provider, canonical URL, access level, status. This proves plumbing only, not research quality.

- [ ] **Step 4: Implement heartbeat visibility check**

Run a controlled silent local child for >10 seconds through `ProcessRunner`; assert terminal/event journal emitted heartbeat at <=10-second intervals.

- [ ] **Step 5: Commit**

```bash
git add scripts/live_smoke.py tests/live/README.md docs/live-smoke-report-template.md
git commit -m "test: add opt-in live provider smoke harness"
```

---

### Task 9: Full v1 Acceptance Matrix, Legacy Cutover, and Final Release

**Files:**
- Create: `tests/integration/test_acceptance_matrix.py`
- Create: `docs/acceptance-matrix.md`
- Create: `docs/migration-cutover.md`
- Modify: `README.md`

**Interfaces:**
- Maps every approved spec acceptance criterion to test ID/evidence artifact.
- Produces final `authorial-flow-graph-v1.zip` only after exact release verification.

- [ ] **Step 1: Create acceptance-matrix test cases**

Each spec criterion 1–28 gets a stable ID `AC-01`… and either deterministic test function or explicit live/owner evidence requirement. The test fails if any criterion lacks a mapping.

- [ ] **Step 2: Run complete mocked suite**

Run:

```bash
export LANGGRAPH_STRICT_MSGPACK=true
pytest tests/unit tests/regression tests/integration tests/repair tests/optimizer tests/release -q
```

Expected: PASS.

- [ ] **Step 3: Run clean-ZIP install test in a fresh directory**

Build release, copy ZIP into a new temp `Téléchargements`-named path, unzip, execute `INSTALL-AND-RUN.sh` with fake provider mode so no credentials are required. Kill during a checkpointed mock model call, rerun same command, verify exact thread resumes.

- [ ] **Step 4: Run live provider smoke checks on target machine**

Require only irreducible credential/login actions. Capture exact output/evidence automatically. Do not ask user to collect logs.

- [ ] **Step 5: Run first live free-will development thread**

Use legacy free-will passage as development material, not semantic authority. Confirm: provenance classification; hard owner/semantic regressions; AI-provisional units not mandatory; source-order positives diagnostic; Thought-Flow reaches either machine-valid candidate or narrow genuine owner interrupt; silent calls heartbeat; Pangram only after local gates.

- [ ] **Step 6: Demonstrate owner interrupt/resume**

When a genuine review/authorial question appears, owner gives only the judgment. System records it, resumes without script/version transfer, and if a new regression fails, machine repair handles it locally.

- [ ] **Step 7: Freeze legacy supervisor**

`docs/migration-cutover.md` records legacy supervisor as read-only evidence and explicitly states no legacy harness/autopilot/supervisor process is in production path.

- [ ] **Step 8: Build and verify final release**

```bash
python scripts/build_release.py --out ~/Téléchargements/authorial-flow-graph-v1.zip
python -m authorial_flow.release verify ~/Téléchargements/authorial-flow-graph-v1.zip
```

Expected: PASS; exact project-instructions character count reported <8000; executable bits preserved.

- [ ] **Step 9: Update README with one-command workflow and validation status**

Distinguish deterministic test coverage, live provider plumbing, Pangram test status, research plumbing, and owner-review evidence. Do not claim generalization beyond data.

- [ ] **Step 10: Commit release candidate**

```bash
git add tests/integration/test_acceptance_matrix.py docs/acceptance-matrix.md docs/migration-cutover.md README.md
git commit -m "release: verify authorial flow graph v1 candidate"
```

---

## Repair/Optimizer/Release Verification Gate

Before release:

```bash
export LANGGRAPH_STRICT_MSGPACK=true
pytest tests/unit tests/regression tests/integration tests/repair tests/optimizer tests/release -q
python scripts/build_release.py --out /tmp/authorial-flow-graph-v1.zip
python -m authorial_flow.release verify /tmp/authorial-flow-graph-v1.zip
```

Then, on the target Zorin machine, run opt-in live smoke and the first development thread. No release claim may substitute local deterministic success for live provider/destination evidence.

## Plan Self-Review

- Spec coverage: failure classification, autonomous worktree repair, provider-review fallback, protected/hash/source-hardcoding gates, partition-safe optimizer, optional DSPy, deterministic release, live smoke, acceptance matrix, migration/cutover.
- Repair can never mutate owner/source/policy/learning authority.
- Provider failures remain machine work.
- Optimizer never uses locked-test bodies to invent candidates and never promotes detector-only regressions.
- Release packaging tests executable bits, schemas/assets, instruction character limit, checksums, and clean install/resume.
- No required OpenHands dependency was introduced.
- Placeholder scan: no unresolved implementation placeholders remain.
