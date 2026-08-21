# Interactive Supervisor Release Review — 2026-08-12

## Decision status

**Candidate; deterministic verification in progress; target-machine supervisor acceptance pending.** No deterministic fake, signal-unit test, or build-container SQLite test is treated as proof of real terminal signal behavior on Zorin.

## Provenance

- Imported baseline release commit recorded by the source package: `9683918db65c9907a081d177d22ccd6953f12415`.
- Imported baseline ZIP: `authorial-flow-graph-v1-9683918-pangram-async-auth-fix-release.zip`.
- Imported baseline ZIP SHA-256: `7bbdcefc354e1ff5ef45b57aa76b8cf55800a26b7796f3501e82452c0a84d140`.
- Preserved source-thread identifier: `f51ae3b6a22e44371ee58c4abbcf49a4e2302fe5cf1a3ec71365d77d3e0daac0`.
- Local import baseline: `ce10c3a`.
- Interactive-supervisor implementation through atomic/security hardening: `6006765`.
- Documentation/version commit: `9cc50c0665d47c7c701f049ae89a72949473bd42`.
- Final evidence commit: the commit containing this review record; its exact SHA is recorded by the final ZIP manifest and external handoff checksum to avoid a self-referential source-tree hash.

## Deterministic evidence recorded so far

All commands used blank live credentials so tests could not accidentally create external clients.

| Command | Result |
|---|---|
| `PANGRAM_API_KEY='' BRAVE_SEARCH_API_KEY='' .venv/bin/python -m pytest -q` after Task 7 | `301 passed in 9.34s` |
| `PANGRAM_API_KEY='' BRAVE_SEARCH_API_KEY='' .venv/bin/python -m pytest -q` after documentation/version commit | `302 passed in 10.54s` |
| `PANGRAM_API_KEY='' BRAVE_SEARCH_API_KEY='' .venv/bin/python -m pytest -q tests/integration/test_supervisor_pause_resume.py tests/integration/test_runtime_dependencies.py tests/integration/test_repair_resume.py tests/regression/test_supervisor_security.py` | `57 passed in 2.48s` |
| `PANGRAM_API_KEY='' BRAVE_SEARCH_API_KEY='' .venv/bin/python -m pytest -q tests/unit/test_pangram.py tests/integration/test_detector_downstream.py tests/repair tests/integration/test_repair_resume.py tests/integration/test_bootstrap_repair.py` | `54 passed in 1.92s` |
| `.venv/bin/python -m pytest -q tests/release/test_release_package.py` | `21 passed in 4.24s` |
| Credential-name and raw-operational-field `rg` scans | Intentional key handling, denylist/redaction code, prompt policy, and test fixtures only; no emitted raw prompt/stdout/stderr field |

The real LangGraph/SQLite test paths are installed and executed in this environment; there is no dependency-gated skip recorded in the results above.

## Release artifact

- Graph version: `1.1.0-dev1`.
- Python package version: `1.1.0.dev1`.
- Release archive root: `authorial-flow-graph-v1` (unchanged).
- Pre-evidence ZIP: `authorial-flow-graph-v1-9cc50c06-interactive-supervisor-release.zip`.
- Pre-evidence ZIP SHA-256: `ecec6b3b936d1e4c7022f6771f466560515931c34e906538faa786e36018ebec`.
- Pre-evidence build verification: `verification=PASS`; archive root `authorial-flow-graph-v1`; 203 members; clean-ZIP compile and independent clean-extraction compile passed.
- Final replacement ZIP filename/source commit/SHA-256: recorded in the external handoff and checksum sidecar after this evidence commit; the pre-evidence ZIP is not delivered.
- `PASTE_INTO_PROJECT_INSTRUCTIONS.txt` character count: `3175` according to the release verifier.

## Evidence boundary

Deterministic tests establish state-machine contracts, content-hash checks, redaction, event order, SQLite persistence, one-shot directives, per-move coverage, and fake Pangram/repair call counts. They do not establish:

- how Ctrl+C is delivered by Joel's target terminal and shell;
- live Claude or Codex CLI behavior under cancellation;
- live Pangram authentication, task submission, returned version, or Human/zero-AI result;
- owner judgment that a real bad-looking passage became better after a redirect.

## Target Zorin acceptance — all pending

| Check | Status |
|---|---|
| Exact extracted ZIP deterministic suite | PENDING |
| Live Claude smoke | PENDING |
| Live Codex smoke | PENDING |
| Pangram zero-task authentication probe | PENDING |
| First real Pangram task ID checkpoint and returned version | PENDING |
| Real bad-looking Thought-Flow run observed | PENDING |
| Ctrl+C opens supervisor in the same terminal | PENDING |
| One supervisor question leaves graph paused | PENDING |
| One confirmed bounded redirect | PENDING |
| Same-thread continuation or durable continued pause/reopen | PENDING |

Target approval must remain pending until these checks are performed against the exact final ZIP.
