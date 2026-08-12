> **Historical review:** This records the pre-self-healing implementation review. Current release status is in `docs/2026-08-11-autonomous-self-healing-review.md`.

# Authorial Flow Graph v1 — completion code/spec review (2026-08-11)

## Scope

Cold review of the implementation handoff at `a727b77c657c132ea6b644eefbc320283e472768` against the v1 design and implementation plans, followed by regression-first repairs in `feature/implementation`.

## Defects found and repaired

1. **Authorial-ambiguity resume context was lost.** `ANSWER` responses were revalidated as `FINAL_REVIEW`, so a real ambiguity resume failed before learning. Interrupt kind is now persisted through the interrupt node and consumed by owner learning.
2. **Owner answers were logged but not deterministically installed into the resumed conceptual substrate.** The resolved answer now becomes an `OWNER_GROUNDED` semantic unit and Thought-Flow restarts from it.
3. **`RESEARCH_ADOPTION` existed only as a payload/validator, not as a graph interrupt.** A dedicated durable graph node and route now handle `ADOPT_ALTERNATIVE`, `KEEP_POSITION`, and `DEFER`.
4. **Research decisions were logged but not applied on resume.** Adopted alternatives and retained faithful positions now resume directly from the selected units without repeating research.
5. **Non-divergent research repair was discarded.** Research-informed units now return to active Thought-Flow when they do not change the owner's position.
6. **A model-declared divergent developmental position could become active byline prose.** Divergent alternatives now remain separate and require owner judgment before adoption.
7. **Owner-final/P2S text could be escalated into P3/P4 by a model recommendation without substantive permission.** The runtime now interrupts for owner authority instead of silently escalating.
8. **Owner locks could be removed by `bank`, and `owner_position_changed=True` could suppress exact-lock validation.** `bank` now counts as removal for preservation validation, and exact owner locks remain fatal even for candidate-only alternatives.
9. **Writer-attempt budget was configured but unenforced; accepted-move budget was hard-coded.** Both are now enforced from `RuntimeConfig` and produce durable bounded-stop machine states.
10. **Pangram async task IDs were not checkpointed before polling.** Production async clients now submit in one graph step, checkpoint task identity, poll only on subsequent detector steps, reuse the same task on resume, reject candidate/task identity mismatches, enforce the polling deadline, and verify terminal version `4.0`.
11. **The one-command installer always seeded `run` again.** It now delegates to a state-aware wrapper: first invocation starts a thread; later no-argument invocations resume the recorded thread.

## Verification added

Regression tests now cover the repaired owner-authority, research adoption, research return-to-flow, writer-budget, async Pangram checkpoint/resume, and installer-resume paths. Each production repair was preceded by a failing regression test.

## Still requires target-machine evidence

- Real LangGraph + SQLite checkpointer reopen/resume test (dependency intentionally absent in the review container).
- Exact Zorin `~/Téléchargements` install path and one-command first-run/resume behavior.
- Live Claude Opus 5 / Codex model resolution, structured calls, heartbeat, and Ctrl+C child-process behavior.
- Live Pangram `pangram-4` `/models`, submit, checkpoint, poll, terminal version, and no-duplicate resume behavior.
- Live bounded research discovery/fetch path when triggered.
- First real free-will Thought-Flow, owner ambiguity/research-adoption interrupt where applicable, final review, owner response, persisted learning, and same-thread continuation.

These target-machine items remain separate from deterministic repository verification; they are not claimed complete here.

## Target-machine follow-up — SQLite resume test harness correction

The first Zorin dependency-complete run exposed a defect in the previously skipped real-LangGraph integration test itself. `test_owner_interrupt_resumes_same_thread_after_sqlite_reopen` used a detector stub that returned only `final_local_gates.hard_pass=True`. The production detector reaches final owner review only after Pangram returns Human, at which point it explicitly returns `status="owner_review_ready"` and `pangram_human=True`. The graph therefore correctly finalized the malformed test state instead of interrupting.

The integration stub now models the production post-Pangram contract explicitly. Production routing was deliberately left unchanged: inferring owner-review readiness from local `hard_pass` would violate the design by allowing owner review without a Pangram-Human result. The corrected test still exercises the intended live boundary: interrupt persistence in SQLite, process/checkpointer reopen, same `thread_id`, `Command(resume=...)`, and continuation to owner acceptance.
