# Pangram Section Budget + Usage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enforce a persistent six-paid-submission cap per audit section and record detector-use efficiency.

**Architecture:** Add a focused usage ledger. PangramClient reserves a paid submission immediately before each POST and reports cache/resume events. Fixed-batch supplies audit/section identity and emits usage summaries. State persists across separate batches in the same audit.

**Tech Stack:** Python 3.11, pytest, existing cache and GitSync.

## Global constraints

- Maximum paid submissions: 6 per audit + section + model/version.
- Ambiguous POST attempts count.
- Cache hits, auth probes, polling and pending-task resumes do not count.
- Persist and sync the reservation before POST.
- Word-count-derived credit values are estimates.
- Legacy fixed-batch specs remain compatible.

### Task 1: Persistent usage state

Create `src/pangram_lab/usage.py` and `tests/test_usage.py`.

- [ ] Write tests first: six reservations succeed; the seventh is blocked; sections are independent; state reload preserves counts; estimated credits use ceiling(words/1000), minimum one per paid submission.
- [ ] Run `pytest -q tests/test_usage.py` and verify the missing feature fails.
- [ ] Implement minimal atomic JSON ledger under `state/usage/pangram/<audit_id>.json`.
- [ ] Re-run and verify green.

### Task 2: Instrument PangramClient

Modify `src/pangram_lab/pangram4.py` and `tests/test_pangram.py`.

- [ ] Write failing tests: cache hit costs zero; pending resume costs zero; a new POST costs one; ambiguous POST still costs one; a seventh POST is blocked before transport sees it.
- [ ] Verify red.
- [ ] Extend `detect_cached(..., usage=None, section_id=None)` without changing result type. Reserve immediately before every actual POST and sync reservation before POST.
- [ ] Verify green.

### Task 3: Fixed-batch schema and reporting

Modify `src/pangram_lab/fixed_batch.py`, `scripts/run_fixed_batch.py`, and `tests/test_fixed_batch.py`.

- [ ] Write failing tests for top-level `audit_id`, per-variant `section_id`, cumulative same-section budget, independent section budgets, usage summary output, and legacy v1 compatibility.
- [ ] Verify red.
- [ ] Implement minimal plumbing and result fields.
- [ ] Verify green.

### Task 4: Exhaustion handoff

Modify `src/pangram_lab/usage.py`, `src/pangram_lab/fixed_batch.py`, and `tests/test_fixed_batch.py`.

- [ ] Write a failing test that preloads six reservations, blocks the next paid submission, and writes `state/handoffs/pangram/<audit_id>-<section_id>.json` with reason `paid_section_budget_exhausted` and completed results.
- [ ] Verify red, implement, then verify green.

### Task 5: Docs and verification

Modify `docs/PANGRAM-ACTIONS-RUNBOOK.md`, `docs/CHATGPT-OPERATING-GUIDE.md`, and `README.md`.

- [ ] Require audit/section identity for new humanization work; document six-call hard cap and handoff behavior.
- [ ] Require reporting paid submissions, cache hits, estimated credits, and calls-to-Human.
- [ ] Run focused tests, then `pytest -q` full suite.
- [ ] Verify no credentials or historical evidence are rewritten.