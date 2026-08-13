# Lesson Closeout Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce disposition of substantive humanization/detector findings before completion and detect orphaned research automatically.

**Architecture:** Add a SHA-256-bound JSON lesson ledger, a stdlib Python closeout CLI, exact-hash/range tests, and GitHub Actions for change gating plus weekly orphan reporting. Existing evidence before the activation timestamp is grandfathered.

**Tech Stack:** Python 3.10+ stdlib, pytest, git CLI, GitHub Actions, GitHub CLI in Actions.

## Global Constraints

- `state/LESSON-INDEX.md` is the mandatory current lesson entry point.
- Do not auto-promote detector findings.
- Do not require Joel to remember or manually police lesson closeout.
- Promoted findings require both index and summary updates.
- Non-promoted findings require an explicit reason.

---

### Task 1: Exact-hash ledger and audit CLI

**Files:**
- Create: `src/pangram_lab/lesson_closeout.py`
- Create: `state/LESSON-LEDGER.json`
- Create: `state/lesson-closeout-config.json`
- Test: `tests/test_lesson_closeout.py`

- [ ] Write failing tests for orphan detection, exact-hash invalidation, disposition validation, promotion targets, pre-gate grandfathering, changed-range enforcement, and cross-ref recording.
- [ ] Run the focused tests and confirm failure before implementation.
- [ ] Implement the minimum stdlib CLI and rerun focused tests until green.

### Task 2: Human/process documentation and package command

**Files:**
- Create: `docs/LESSON-CLOSEOUT.md`
- Modify: `pyproject.toml`
- Modify: `state/LESSON-INDEX.md`
- Modify: `docs/CHATGPT-OPERATING-GUIDE.md`

- [ ] Add `pangram-lesson-closeout` script entry.
- [ ] Make lesson index and ChatGPT guide state the completion gate and index-first retrieval rule.
- [ ] Document record/audit/check commands, dispositions, cross-ref closeout, and no-reminder rule.

### Task 3: GitHub enforcement and weekly backstop

**Files:**
- Create: `.github/workflows/lesson-integrity.yml`

- [ ] On PR/push, run changed-range closeout and full current-ref audit.
- [ ] Weekly, audit `main` and the configured automation branch.
- [ ] If weekly audit finds orphans, open/update one canonical issue; close it automatically after a clean weekly run.

### Task 4: Verification

- [ ] Run the complete pytest suite.
- [ ] Run Python compile checks.
- [ ] Run the audit against the current repository with the activation cutoff.
- [ ] Review the final diff for accidental lesson/source rewrites.
