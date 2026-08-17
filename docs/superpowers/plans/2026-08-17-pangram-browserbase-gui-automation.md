# Pangram Browserbase GUI Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic Browserbase + Playwright Pangram GUI runner with persistent login, SHA-bound duplicate defense, structured report extraction, PDF evidence capture, and a manual GitHub Actions dispatch path.

**Architecture:** Keep the evidence/identity/parser layer dependency-free in `src/pangram_lab/gui_browserbase.py`; load Playwright only inside the live-browser adapter so the normal repository test suite does not require browser packages. Use Browserbase's REST API through the Python standard library for Context/session/debug lifecycle. A thin CLI in `scripts/pangram_gui_browserbase.py` exposes `bootstrap` and `run`; GitHub Actions installs the optional browser extra only when GUI measurement is explicitly dispatched.

**Tech Stack:** Python 3.10+, standard-library HTTP/JSON/hashlib/pathlib, Playwright Python over CDP, Browserbase REST API, pytest, GitHub Actions.

## Global Constraints

- Never commit `BROWSERBASE_API_KEY`, Pangram credentials, cookies, or Browserbase user-data contents.
- `BROWSERBASE_CONTEXT_ID` comes from environment/secret configuration for unattended runs.
- Submitted detector text must be byte-equivalent as Unicode text to the selected input file; no labels or metadata may be prefixed/appended.
- Completed identical GUI measurements are reused unless `--force` is explicit.
- Article prose is read-only to this subsystem.
- Native Pangram PDF and browser-print fallback provenance must be distinguishable.
- UI selector fallbacks are bounded and must fail closed rather than click arbitrary controls.

---

### Task 1: Pure evidence identity and GUI report parser

**Files:**
- Create: `src/pangram_lab/gui_browserbase.py`
- Test: `tests/test_gui_browserbase.py`

**Interfaces:**
- Produces `sha256_text(text: str) -> str`.
- Produces `measurement_dir(root: Path, input_sha256: str) -> Path`.
- Produces `completed_result_exists(root: Path, input_sha256: str) -> bool`.
- Produces `parse_report_text(body: str) -> dict[str, object]`.
- Produces `build_session_payload(context_id: str, *, persist: bool, keep_alive: bool, timeout: int, user_metadata: dict[str, str]) -> dict[str, object]`.

- [ ] **Step 1: Write failing parser/identity/payload tests** using representative Pangram 4 GUI text matching the current PDFs: 94.4% Human Written, 5.6% AI Generated, `Fully AI Generated | 413 Words | High Confidence`, and neighboring Human segments.
- [ ] **Step 2: Run `python -m pytest tests/test_gui_browserbase.py -q`** and confirm failure because production module/functions do not exist.
- [ ] **Step 3: Implement minimal pure functions** with no Browserbase/Playwright imports.
- [ ] **Step 4: Re-run focused tests** and confirm green.
- [ ] **Step 5: Commit** pure evidence/parser layer.

### Task 2: Browserbase REST lifecycle and live Playwright adapter

**Files:**
- Modify: `src/pangram_lab/gui_browserbase.py`
- Test: `tests/test_gui_browserbase.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces `BrowserbaseRestClient` with `create_context`, `create_session`, and `debug_urls`.
- Produces `bootstrap_login(...) -> dict[str, object]`.
- Produces `run_inputs(...) -> list[dict[str, object]]`.
- Live Playwright import occurs only inside adapter functions.

- [ ] **Step 1: Add failing tests** for REST request construction and fail-closed environment validation.
- [ ] **Step 2: Run focused tests and verify RED** for missing lifecycle functions.
- [ ] **Step 3: Implement standard-library Browserbase REST client and bounded Playwright locator helpers.** Use Browserbase session `browserSettings.context.id/persist`, official CDP `connectUrl`, debugger endpoint, Pangram login URL, bounded detector input selectors, bounded detection button names, and report-completion markers.
- [ ] **Step 4: Add optional dependency** `browser = ["playwright>=1.50"]`; do not require browser packages for normal tests.
- [ ] **Step 5: Run focused tests and full `python -m pytest -q`**.
- [ ] **Step 6: Commit** live adapter.

### Task 3: CLI, artifact capture, and duplicate defense

**Files:**
- Create: `scripts/pangram_gui_browserbase.py`
- Modify: `src/pangram_lab/gui_browserbase.py`
- Test: `tests/test_gui_browserbase.py`

**Interfaces:**
- `bootstrap` creates/reuses a persistent Context, prints live debugger URL, waits for manual confirmation, and verifies detector availability before closing.
- `run` accepts repeated `--input`, `--force`, `--output-root`, and `--pangram-url`.

- [ ] **Step 1: Add failing tests** for completed-result skip behavior, exact result paths, and artifact provenance fields.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Implement CLI and run orchestration.** Save `result.json`, `report-body.txt`, native downloaded PDF when available, browser-print fallback otherwise, and failure evidence on exceptions. Save session recording/debug URL in every receipt.
- [ ] **Step 4: Verify focused and full tests GREEN**.
- [ ] **Step 5: Commit** CLI/orchestration.

### Task 4: Manual GitHub Actions dispatch

**Files:**
- Create: `.github/workflows/pangram-gui-browserbase.yml`
- Create: `docs/PANGRAM-GUI-BROWSERBASE-RUNBOOK.md`
- Test: repository full suite plus workflow/static audit.

**Interfaces:**
- Manual workflow consumes GitHub secrets `BROWSERBASE_API_KEY` and `BROWSERBASE_CONTEXT_ID`.
- Defaults to current Romance `pangram-part-1.txt` and `pangram-part-2.txt`.

- [ ] **Step 1: Write runbook first** with exact Browserbase bootstrap commands, one-time login flow, required secrets, manual dispatch behavior, duplicate defense, and troubleshooting/debug-session instructions.
- [ ] **Step 2: Add workflow** that installs `.[test,browser]`, invokes the runner, commits only `state/gui-runs/pangram-4/**`, and fails closed on expired auth/UI drift.
- [ ] **Step 3: Run full tests and repository audit**; check workflow YAML paths and least-privilege permissions.
- [ ] **Step 4: Commit** workflow/runbook.

### Task 5: Verification and durable handoff

**Files:**
- Create: `state/PANGRAM-GUI-BROWSERBASE-CURRENT-STATE-2026-08-17.md`

**Interfaces:**
- Records exact branch/head, test evidence, untested live assumptions, required user setup, and next safe action.

- [ ] **Step 1: Run `python -m pytest -q`.**
- [ ] **Step 2: Run `python scripts/audit_codex_github.py --root . --fail-on error`.**
- [ ] **Step 3: Verify no secrets or literal credentials are present in the diff.**
- [ ] **Step 4: Record limitations honestly:** live Pangram selectors cannot be certified until a Browserbase account/context is provided and the one-time login bootstrap is performed.
- [ ] **Step 5: Commit current state and open a PR** against the appropriate Pangram-lab base branch rather than merging detector tooling into article authority silently.
