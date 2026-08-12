# Authorial Flow Graph v1 — Implementation Plan Index

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement these plans in order. Steps use checkbox syntax for tracking.

**Goal:** Implement the owner-approved Authorial Flow Graph v1 design as three independently testable increments without reintroducing nested homemade supervisors.

**Architecture:** Plan 1 establishes the sole LangGraph runtime and a complete Basic Thought-Flow path. Plan 2 adds provenance-aware mode selection, P3/P4/research escalation, candidate-role separation, scoped owner learning, and narrow human interrupts. Plan 3 adds autonomous executable repair, safe optimizer support, exact release verification, and live cutover.

**Tech Stack:** Python, LangGraph + SQLite checkpointer, Claude/Codex local CLIs, Pangram async REST, provider-neutral research, git worktrees, pytest; optional DSPy/GEPA.

## Global Constraints

- The controlling design is `docs/superpowers/specs/2026-08-10-authorial-flow-graph-design.md` at owner-approved status.
- The current Joel Articles policy snapshot controls authority and humanization behavior; owner corrections outrank model/detector conclusions.
- Do not start Plan 2 until Plan 1 verification gate passes and is committed.
- Do not start Plan 3 until Plan 2 verification gate passes and is committed.
- Each task follows TDD: failing test → observed failure → minimal implementation → passing test → commit.
- Before claiming any plan complete, run its full verification gate and the superpowers verification-before-completion skill.

---

## Plan 1 — Core Runtime

File: `docs/superpowers/plans/2026-08-10-authorial-flow-core-runtime-plan.md`

Delivers a working Basic Thought-Flow LangGraph with:

- content-addressed artifacts and append-only events;
- SQLite checkpoints and durable `thread_id` resume;
- nonblocking heartbeat process runner;
- Claude/Codex structured adapters;
- Pangram task checkpointing;
- hard owner/semantic regressions and diagnostic positives;
- authority-aware Basic representation;
- candidate-blind pressure, local/global flow, fidelity, stop/rollback;
- cold audits and editorial freeze before detector;
- durable owner interrupt;
- one-command local CLI and deterministic evidence package.

**Exit condition:** complete mocked end-to-end run pauses/resumes across a fresh Python process and reaches owner ACCEPT without legacy supervisor processes.

---

## Plan 2 — Development, Research, and Learning

File: `docs/superpowers/plans/2026-08-10-authorial-flow-development-research-learning-plan.md`

Adds:

- P0/P1/P2/P2S/P3/P4 mode authority;
- provenance classifier and default `humanize` inference;
- semantic-sanity escalation and return to Basic Thought-Flow;
- P3/P4 developmental reconstruction;
- bounded provenance-aware research;
- conservative/developmental/research-informed/better-reasoned candidate roles;
- detector-blind editorial ranking and minimal presentation;
- append-only owner learning with scope ladder/partitions;
- separate local edge/stop and global precomputed-shape labels;
- narrow authorial/research-adoption interrupts.

**Exit condition:** mocked default `humanize` can repair an AI-generated thought, perform bounded research when material, return to Thought-Flow, and learn from one owner judgment without restart or global overgeneralization.

---

## Plan 3 — Repair, Optimizer, and Release

File: `docs/superpowers/plans/2026-08-10-authorial-flow-repair-optimizer-release-plan.md`

Adds:

- explicit machine-vs-owner failure classification;
- isolated git-worktree code repair;
- Codex plan/implementation + Claude review/Codex fallback;
- protected-file/source-hardcoding gates;
- tested/reviewed promotion + automatic resume;
- partition-safe built-in evaluator/program optimizer;
- optional DSPy/GEPA adapter;
- deterministic release ZIP and clean-install verification;
- opt-in live Claude/Codex/Pangram/research smoke tests;
- full acceptance matrix and legacy cutover.

**Exit condition:** exact clean release ZIP installs/runs/resumes on the target Zorin path, machine failures repair locally, and only a genuine authorial judgment requires human input.

---

## Overall Definition of Done

All owner-approved acceptance criteria in the design spec have a passing deterministic test or explicitly named live/owner evidence artifact. The final runtime asks the owner for judgments, not courier/debug labor, and the legacy harness/autopilot/supervisor stack is retired from the live path.

## Spec Coverage Matrix

| Approved design section | Implemented by |
|---|---|
| 1–2 purpose/non-goals | All plans; enforced by acceptance matrix in Plan 3 Task 9 |
| 3 policy/operation levels | Plan 2 Tasks 1–3 |
| 4 semantic authority model | Plan 1 Task 7; Plan 2 Tasks 3–4 |
| 5 sole LangGraph architecture | Plan 1 Tasks 2, 10–12 |
| 6 repository layout | Plan 1 Tasks 1–12; Plans 2–3 add declared modules |
| 7 typed graph state | Plan 1 Task 2; extended in Plan 2 Task 2 and Plan 3 Task 1 |
| 8 main graph | Plan 1 Task 10; escalation edges Plan 2 Tasks 2–9; repair edge Plan 3 Task 4 |
| 9 semantic sanity/escalation | Plan 2 Tasks 2, 4, 9 |
| 10 bounded research | Plan 2 Task 5 |
| 11 regressions | Plan 1 Tasks 6, 8, 12; Plan 2 learning regressions |
| 12 Thought-Flow generation | Plan 1 Tasks 7–9 |
| 13 cold audits | Plan 1 Task 9 |
| 14 candidate pool/presentation | Plan 2 Task 6 |
| 15 detector conflict policy | Plan 1 Task 9; Plan 2 Task 6 |
| 16 Pangram | Plan 1 Tasks 5, 9 |
| 17 human interruption | Plan 1 Task 10; Plan 2 Task 8 |
| 18 learning model | Plan 2 Tasks 7–8 |
| 19 failure/repair | Plan 3 Tasks 1–4 |
| 20 observability | Plan 1 Tasks 3, 11; Plan 3 Task 8 |
| 21 artifacts/research storage | Plan 1 Task 2; Plan 2 Task 5 |
| 22 optimizer | Plan 3 Tasks 5–6 |
| 23 one-command workflow | Plan 1 Task 11; exact release Plan 3 Tasks 7–9 |
| 24 secret/authority isolation | Plan 1 Tasks 3–6; Plan 3 Task 2 |
| 25 testing strategy | All plans; final matrix Plan 3 Task 9 |
| 26 acceptance criteria | Plan 3 Task 9 maps every criterion to evidence |
| 27 migration/cutover | Plan 1 Task 12; Plan 3 Task 9 |
| 28 deferred items | Preserved as explicit non-goals; no task adds browser/OpenHands/multi-user/cloud DB |
| 29 approved owner decisions | Plan 2 Tasks 1–9 + Plan 1 detector policy |
| 30 reference basis | Dependency/API verification in Plan 1/3 and release documentation |
