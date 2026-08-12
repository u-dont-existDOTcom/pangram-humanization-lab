# Autonomous Self-Healing Runtime Design

**Status:** Approved design choice: full internal self-healing loop.

## Goal

When Authorial Flow encounters a genuinely machine-fixable failure (provider plumbing, deterministic runtime/checkpoint defects, regression harness defects, generation dead ends caused by runtime code, research-provider plumbing, fidelity/guard implementation defects, or Pangram plumbing), repair the runtime locally with Codex without making Joel collect logs, edit files, or manually restart the conceptual task. Resume the same article thread from the last valid LangGraph checkpoint after a verified repair.

## Non-goals and hard boundaries

- Never ask Codex to resolve missing authorial meaning, owner preference, claim authority, or research-adoption judgment.
- Never allow repair agents to mutate owner/project inputs, policy snapshots, gold/learning data, Pangram baselines, or `.state/learning/`.
- Never give repair Codex Pangram or Brave credentials.
- Never hardcode the current article/source wording into production code.
- Never promote an unverified patch or continue after exhausted bounded repair budgets.
- Never treat detector improvement as repair success.
- Do not add a second external supervisor when the in-runtime repair system already owns the relevant state.

## Existing substrate to preserve

The current implementation already provides:

- `FailureRecord` and failure classification;
- `RepairPlanner` using Codex;
- `RepairReviewer` using Claude with Codex fallback;
- disposable Git worktrees (`WorktreeManager`);
- protected-source snapshots and source-hardcoding guards;
- `RepairExecutor` using Codex in workspace-write sandbox;
- deterministic verification (`RepairVerifier`);
- a written but currently unused `verify_with_one_fix` bounded correction helper;
- fast-forward promotion to the main checkout;
- LangGraph/SQLite checkpoints;
- restart-required signaling after promoted Python repairs.

The self-healing feature extends these components rather than replacing them.

## Architecture

### 1. Evidence-complete failure bundle

Every `_guarded_node` failure must persist a dereferenceable repair bundle containing:

- failure class;
- originating node and phase;
- exception type and complete exception message;
- current program/git version;
- current thread ID/checkpoint identity when available;
- source hash, task mode, provenance, local gate state, repair attempt;
- provider/model/role/request identity for each model attempt when available;
- referenced provider stdout/stderr artifact IDs **and their bounded textual contents**;
- schema expected by the failed model call when available;
- relevant runtime environment/version facts that are safe to expose;
- most recent event/journal context needed to locate the failing component;
- suggested targeted test command derived from the failure location when deterministic.

The planner must receive this material, not merely the hash of the failure record. Evidence is stored in `.state/artifacts` and may be additionally materialized inside the disposable repair worktree under a repair-only evidence directory excluded from promotion.

### 2. Machine/owner gate before repair

`OWNER_JUDGMENT` remains an owner interrupt. All other currently repairable failure classes enter the bounded machine-repair pipeline. A planner requesting owner judgment is accepted only when the original failure record already establishes `authorial_information_missing=true`; a repair agent cannot manufacture an owner-question escape hatch.

### 3. Regression-first Codex repair in an isolated worktree

For each repair round:

1. Create a detached disposable Git worktree from the exact running commit.
2. Write the failure evidence bundle into a repair-only evidence directory.
3. Ask Codex for one causal repair plan constrained to the evidence and existing architecture.
4. Independently review the plan before edits.
5. Ask Codex to implement the approved repair **test-first**:
   - add the smallest regression reproducing the failure;
   - run it and preserve the RED evidence;
   - make the smallest production change;
   - rerun the targeted test and preserve GREEN evidence.
6. Prevent mutation of protected source/policy/learning paths and source-specific hardcoding.

The repair executor must return artifact references for its transcript/evidence and the candidate commit SHA.

### 4. Verification and one bounded correction

Production repair uses the existing verifier plus its currently unused one-fix path.

Verification order:

1. compile source/tests;
2. execute the plan-declared targeted regression(s) when safe and local;
3. unit + regression tests;
4. integration tests;
5. full repository pytest suite when not already equivalent;
6. protected-file/source-hardcoding diff guard;
7. independent diff review against the approved repair plan.

If verification fails, Codex gets exactly one bounded correction opportunity with:

- the approved plan;
- actual candidate diff;
- failing verification command;
- stdout/stderr from that command;
- previous repair transcript refs.

The correction occurs in the same disposable worktree, adds/adjusts tests only as needed to express the intended behavior, and is reverified from the beginning. A second failure ends that repair round without promotion.

### 5. Promotion and program-image restart

Only a fully verified candidate is fast-forward promoted. Promotion records:

- base commit;
- repair commit;
- failure bundle ref;
- plan ref;
- test/verification refs;
- independent review ref;
- repair round;
- parent thread ID.

A Python-code promotion still requires process restart; no hot reload is attempted.

### 6. Same-thread checkpoint continuation

The current restart behavior is changed. A promoted repair must **not** call `run <source>` and calculate a new program-version-derived thread ID. Instead:

- preserve `.state/current-thread.json` and its existing `thread_id`;
- record the new program version in repair lineage/state;
- restart the CLI with `resume`;
- reopen the same SQLite checkpoint thread under the newly promoted code;
- continue from the graph state immediately following the machine-failure/repair boundary.

The source/program lineage remains auditable, but program version no longer destroys conceptual continuity after a repair. New user-initiated runs may continue to use content/program-derived IDs as appropriate; autonomous repair restart is explicitly same-thread.

Legacy compatibility cannot assume that the terminal state contains `failure_origin_node`: releases affected by the returned-failure evidence defect may have finalized a valid `machine_failure` chain without that field. Recovery must inspect only the newest terminal lineage, stop before any older terminal checkpoint, find the newest `machine_failure`, and accept its allowlisted origin or phase as the replay node. It then selects the newest checkpoint whose `next` contains that node. If either inference is unavailable, recovery fails closed without replaying an older lineage or reseeding the article.

### 7. Repair-node continuation semantics

A promoted code repair returns a restart-required status that exits the old process only far enough for the CLI restart hook to `exec` the new program image. The checkpoint must retain the repair result and the pre-failure conceptual state. On `resume`, routing re-enters the repaired machine path rather than finalizing or reseeding.

Care is required to prevent the same `machine_failure` state from immediately re-entering repair forever. The resumed state must clear the resolved failure markers or route through the repaired originating stage/regression gate deterministically while retaining repair lineage.

### 8. Bounded budgets and escalation

- `repair_rounds`: retain the current bounded default (5) unless tests prove a smaller safe value.
- `implementation_fix_attempts`: exactly one correction within a repair round by default.
- Planner/reviewer/provider failures consume bounded machine attempts; they do not become owner debugging requests.
- If all bounded attempts fail, persist a complete evidence package and stop as `bounded_machine_stop`.
- Owner is interrupted only for genuine authorial information/judgment, not machine debugging.

### 9. Credential and source isolation

Repair Codex environment removes at minimum:

- `PANGRAM_API_KEY`;
- `BRAVE_SEARCH_API_KEY`.

Protected paths include all project owner inputs/gold files, policy bundles, `.state/learning/`, and any credential material. Repair evidence may include provider stderr/stdout but must redact environment secrets and must not copy arbitrary home-directory credentials into the worktree.

### 10. Observability

During self-repair the normal 10-second heartbeat remains visible and reports high-level states such as:

- `repair: diagnose`;
- `repair: plan-review`;
- `repair: codex-red`;
- `repair: patch`;
- `repair: verify-targeted`;
- `repair: verify-full`;
- `repair: correction-1`;
- `repair: promote`;
- `repair: restart-same-thread`.

The user should not need to inspect these logs unless the bounded repair system itself exhausts.

## Test design

The implementation must add regression coverage for at least these cases:

1. A provider schema/plumbing failure bundle passed to the planner contains dereferenced stderr/stdout and expected schema, not just artifact hashes.
2. Repair Codex cannot see Pangram/Brave credentials or modify protected owner/policy/learning files.
3. Repair execution demonstrates RED-before-GREEN evidence for a machine repair.
4. A broken first candidate enters exactly one bounded correction and promotes only after all verification passes.
5. A second failed correction does not promote.
6. A promoted repair restarts with `resume`, not `run`, and preserves the exact parent `thread_id`.
7. SQLite reopen after a promoted repair continues the same conceptual checkpoint without reseeding `accepted_moves` or source representation.
8. The repaired originating path is retried under the new code rather than finalizing at `repair_promoted_restart_required`.
9. Owner-judgment failures still interrupt rather than invoking Codex repair.
10. Dirty main worktree, protected-source mutation, source hardcoding, unrelated broad refactor, failed full suite, or rejected independent review blocks promotion.
11. Exhausted machine repair produces a bounded failure/evidence package without asking Joel to relay logs.
12. Existing 175-test target-machine behavior remains green.

## Likely file changes

- `src/authorial_flow/failures.py` — richer safe failure/repair evidence schema.
- `src/authorial_flow/runtime.py` — build/dereference failure bundles; orchestrate evidence-rich planning, correction, verification, promotion, and post-repair state clearing.
- `src/authorial_flow/repair/planner.py` — consume structured evidence bundle.
- `src/authorial_flow/repair/executor.py` — enforce regression-first repair contract and retain repair transcript refs.
- `src/authorial_flow/repair/verify.py` — production use of targeted/full verification and one bounded correction.
- `src/authorial_flow/repair/schemas.py` — evidence/test/correction metadata needed for durable audit.
- `src/authorial_flow/repair/protection.py` — expand protected path/prefix enforcement if required.
- `src/authorial_flow/cli.py` — restart promoted repairs with same-thread `resume`.
- `src/authorial_flow/routing.py` and/or `src/authorial_flow/nodes/repair.py` — deterministic post-repair continuation semantics.
- `src/authorial_flow/state.py` — durable repair lineage/evidence fields as needed.
- `tests/repair/*`, `tests/integration/test_repair_resume.py`, `tests/integration/test_runtime_dependencies.py`, and CLI/graph tests — regression-first coverage.
- `README.md`, `docs/core-runtime-verification.md`, `docs/acceptance-matrix.md`, `docs/release-checklist.md` — document automatic repair acceptance criteria and validation planes.

## Acceptance criteria

A release is acceptable only when:

- all deterministic tests pass;
- the real LangGraph/SQLite integration test passes where dependencies are installed;
- release-package verification and clean-extraction compilation pass;
- project instruction text remains under 8,000 characters;
- a synthetic machine failure can self-repair in an isolated worktree and continue the same checkpoint thread without user log relay;
- no protected owner/policy/learning input changes;
- no repair credentials leak to Codex;
- exhausted repair stops safely with evidence rather than looping or silently finalizing;
- live provider smoke and the real article run remain separate validation planes and are reported honestly.
