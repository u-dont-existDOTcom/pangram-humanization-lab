# Authorial Flow Graph — Autonomous Self-Healing Completion Review

**Date:** 2026-08-11  
**Feature branch:** `feature/autonomous-self-healing`  
**Implementation baseline:** `9afbcd1`  
**Reviewed implementation commit:** `e1a270a95637b9291e4c03b59c25fc14706ca64a`

## Scope

Cold code/spec review of the approved autonomous self-healing design: machine-failure evidence capture, isolated Codex repair, regression-first proof, controller verification, one bounded correction, verified fast-forward promotion, process-image restart, and continuation of the same LangGraph/SQLite thread.

## Implemented behavior

1. Claude structured runtime roles receive the exact JSON Schema that local validation later enforces. This closes the provider-plumbing failure exposed by the first real Thought-Flow run.
2. `_guarded_node` failures persist a secret-redacted, dereferenceable evidence bundle with provider/model/role/request identity, expected schema, bounded stdout/stderr contents, runtime/thread/source state, and safe event context.
3. Repair Codex runs only in a disposable worktree. `project/`, `policy/`, and `.state/learning/` are protected; Pangram and Brave credentials are removed from the repair process.
4. Initial repair requires real RED-before-GREEN proof for one safe local pytest command. Repair-only evidence is removed before the candidate commit.
5. The controller independently reruns compile, safe plan-declared targeted tests, unit/regression, integration, the full suite, source/protection guards, and independent diff review.
6. A failed controller verification permits exactly one Codex correction in the same repair worktree. The corrected commit must pass the complete verification sequence; a second failure is not promoted.
7. Only the final verified commit is fast-forward promoted.
8. Promotion checkpoints a machine-only `MACHINE_RESTART` interrupt. The stale Python process `exec`s the CLI with `resume`; the new program image resumes the exact existing thread/checkpoint and routes to the original failed machine stage. `current-thread.json` is not reseeded.
9. High-level `repair:*` progress phases are journaled/printed. Exhausted machine repair produces `bounded_machine_stop` plus a secret-free evidence ZIP instead of asking the owner to collect logs.
10. Unsafe or testless model-authored repair plans are rejected before write-capable Codex runs.
11. In-place release upgrades reconcile the local Git repair baseline only after the new release manifest and checksums prove the overlaid files. `.state` is preserved; unrelated dirty files fail closed; a clean existing head (including a previously promoted self-repair) is never reset to a stale release manifest.
12. An older thread that is already terminal at `bounded_machine_stop` is recovered without reseeding: the new runtime replays the newest same-thread checkpoint immediately before the recorded failed machine node. Recovery is permitted once per thread/program-version pair; a bounded stop created by the current program version stamps itself exhausted to prevent repeated provider loops.

## Cold-review defects found and repaired before release

- **Source-hardcoding guard omitted tests.** A repair could have embedded the current article into a new regression test even though production hardcoding was blocked. The guard now scans repair tests as well as production files for long source-specific spans.
- **Unsafe model-declared tests reached the write-capable executor.** The verifier ignored unsafe commands, but the raw plan still reached Codex. Repair execution and correction now fail closed before Codex when tests are absent or are not direct local pytest commands.
- Added explicit coverage that a dirty main worktree blocks promotion and a rejected independent diff review blocks verification.
- The real LangGraph promoted-repair regression now also asserts preservation of both accepted moves and semantic representation across SQLite reopen.
- **In-place release overlays left Git on the old baseline.** Preserving `.state` while unzipping a new release over the existing folder made the working tree dirty, which would cause later autonomous promotion to refuse itself. The installer now reconciles only manifest-owned release changes into a new local baseline, removes obsolete prior-release members safely, preserves `.state`, leaves clean self-repaired heads untouched, and rejects unrelated local changes.
- **An upgraded runtime could preserve the old terminal checkpoint too faithfully.** The real failed thread from the previous release had already reached `END` as `bounded_machine_stop`; ordinary `resume` can therefore return the terminal state without executing the repaired generation node. The CLI now uses LangGraph checkpoint replay to re-execute the recorded failed node from its newest pre-failure checkpoint on the same thread, with a per-program replay marker and current-version exhaustion marker to prevent loops.

## Verification on the reviewed commit

Fresh build-container verification after all code/security fixes:

- `python -m compileall -q src tests scripts` — PASS
- focused repair/model/CLI/failure/heartbeat suite — **71 passed**
- release package/baseline suite — **17 passed**
- full repository suite — **203 passed, 1 skipped**
- skipped test: `tests/integration/test_graph_resume.py` because this build container cannot install the pinned LangGraph/SQLite dependencies
- `git diff --check` — PASS
- protected project/policy paths changed by this feature — **none**
- exact current article sentence hardcoded in `src/` — **none found**
- `PASTE_INTO_PROJECT_INSTRUCTIONS.txt` — **3,175 characters / 8,000 limit**

The prior candidate already passed **175/175** tests on Joel's Zorin machine after LangGraph installation, establishing the baseline SQLite reopen path. The self-healing commit now carries three real-LangGraph/SQLite tests in the dependency-gated module: owner interrupt reopen, promoted-repair restart on the same thread, and replay of an older terminal machine stop from the pre-failure checkpoint. Those exact tests remain target-machine pending until the new ZIP is installed there.

## Independent-review limitation

No Codex CLI/subagent is installed in this build container, so an external-model code-review pass could not be executed here. The cold review above was performed directly against the approved design and complete Git diff; this is lower independence than the normal repair pipeline's Claude/Codex diff review. The target runtime itself still requires independent model review before any autonomous repair promotion.

## Remaining live validation planes

- Install the exact new ZIP on the target Zorin machine and run the full suite, including the new real LangGraph same-thread repair-restart test.
- Trigger one genuine machine-repairable failure and observe evidence capture → Codex RED/GREEN repair → controller verification → promotion → same-thread `resume` end to end.
- Live Pangram submit/checkpoint/poll/no-duplicate-resume behavior.
- First complete owner interrupt/response/learning continuation on the repaired runtime.

These are deliberately not inferred from deterministic tests or prior candidate runs.


## Target-machine follow-up: installer preflight repair boundary

The `20be761` release ran on Joel's Zorin machine with **205 passing tests and one failing real-LangGraph integration assertion**. The terminal replay had already succeeded: it returned `status=done` while preserving the accepted move and section representation. The harness then raised `KeyError` only because it indexed optional `failure_origin_node`; `AuthorialState` is `TypedDict(total=False)` and the replay checkpoint precedes creation of that failure key. The corrected regression therefore uses `.get(..., "")` and does not require stale failure metadata to survive a successful replay.

That target run also exposed an architectural gap: raw installer pytest ran before the LangGraph repair node existed. The candidate now routes installer pytest through `authorial_flow.bootstrap_repair`, after release-baseline reconciliation, reusing the same evidence-rich isolated Codex repair/verification/promotion pipeline. Repair Codex also receives the installed project venv first on `PATH`, while Pangram/Brave credentials remain stripped. In the build container the resulting suite is 208 passed with one dependency-gated LangGraph module skip; Zorin should execute the three tests in that module, for 211 total.

## Target-machine follow-up: live-smoke handoff boundary

The bootstrap-self-healing release completed **211/211** tests on Joel's Zorin machine, including all three real LangGraph/SQLite integration cases. Installation then launched live child processes and printed provider heartbeats, but returned to the shell immediately after `live_smoke_report=.state/live-smoke/install-report.json`. Root-cause tracing showed that `scripts/live_smoke.py` always prints that report path but returns exit status 2 when any requested smoke subcheck is not `pass`; because `INSTALL-AND-RUN.sh` uses `set -e`, the shell exited before `exec ./RUN.sh` and did not surface which subcheck failed.

The current candidate closes that pre-runtime gap. Live smoke now runs through `authorial_flow.bootstrap_repair` with `PROVIDER_PLUMBING` metadata and the full redacted smoke report attached as evidence. A failed smoke prints the failing subcheck(s). Machine-fixable smoke failures enter the same isolated Codex RED/GREEN repair path used elsewhere; the original live-smoke command is also injected as a controller-owned verification command in the disposable worktree, so a patch cannot be promoted merely because pytest passes while the provider failure remains. If the repair controller itself is unavailable (for example Codex is the failed provider), the installer catches that failure and produces the bounded evidence package instead of crashing or requiring manual log relay.

Build-container verification after this repair is **215 passed / 1 dependency-gated LangGraph module skip**; the skipped module contains the same three SQLite tests that passed on Zorin, so the corresponding target-machine suite is expected to contain 218 passing tests before live smoke begins. Exact target results remain pending until this candidate is installed.
