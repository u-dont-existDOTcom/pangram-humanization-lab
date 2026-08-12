# Authorial Flow Graph v1 — Acceptance Matrix

This matrix maps the owner-approved v1 acceptance criteria to deterministic tests, live-provider checks, and owner-confirmed evidence. A deterministic pass does not imply that a live or owner plane has been demonstrated.

| ID | Criterion | Plane | Current evidence | Release status |
|---|---|---|---|---|
| AC-01 | One command installs or updates the environment and resumes the correct thread. | Live | `INSTALL-AND-RUN.sh`; Zorin target preflight 211/211; live-smoke handoff failure diagnosed | Handoff retest pending |
| AC-02 | Ctrl+C and process death resume from the last successful checkpoint. | Live | `tests/integration/test_graph_resume.py`; target-machine interruption smoke | LangGraph/live pending in build container |
| AC-03 | A silent child call produces a heartbeat at least every 10 seconds. | Deterministic | `tests/unit/test_process_runner.py`; `tests/live/test_live_smoke_unit.py` | Covered |
| AC-04 | No stale regression evidence can cross-contaminate suites. | Deterministic | `tests/regression/test_regression_provenance.py` | Covered |
| AC-05 | Repair agents cannot mutate protected source/owner files. | Deterministic | `tests/repair/test_worktree_protection.py`; `tests/integration/test_repair_resume.py` | Covered |
| AC-06 | Owner regression examples are never visible to the writer. | Deterministic | `tests/regression/test_learning_isolation.py`; runtime-dependency tests | Covered |
| AC-07 | Source-order positive probes are diagnostic only. | Deterministic | regression provenance + runtime-dependency tests | Covered |
| AC-08 | Pangram is skipped when hard local gates fail. | Deterministic | `tests/integration/test_detector_downstream.py` | Covered |
| AC-09 | Pangram uses the documented async `x-api-key` transport, verifies authentication without creating a task, checkpoints real task IDs before polling, and does not duplicate submissions on resume. Returned detector version must be exactly `4.0` before Pangram-Human can satisfy the gate. | Live | `tests/unit/test_pangram.py`; `tests/integration/test_live_smoke.py`; runtime detector tests; target-machine Pangram run | Transport deterministic; live version-4 result pending |
| AC-10 | The first Pangram-Human candidate is frozen. | Deterministic | downstream detector/candidate-freeze tests | Covered |
| AC-11 | Machine failures capture dereferenceable evidence, use isolated regression-first Codex repair, controller verification with at most one correction, verified promotion, and same-thread restart rather than user log collection. | Deterministic/live | repair pipeline/protection + repair-resume + CLI + bootstrap/live-smoke repair tests | Runtime repair live pending; installer repair covered |
| AC-12 | The only routine human interrupt is an authorial decision or credential action. | Owner/live | failure taxonomy tests; first target-machine owner interrupt | Owner/live pending |
| AC-13 | A bad-edge owner label is persisted and execution resumes automatically. | Owner/live | `tests/integration/test_owner_learning_resume.py`; first live owner interrupt/resume | Owner/live pending |
| AC-14 | Internal artifacts are archived rather than printed as nonexistent upload paths. | Deterministic | evidence packaging and runtime-output tests | Covered |
| AC-15 | Final completion produces accepted text plus one reproducible evidence package. | Owner/live | evidence/release tests; first owner-accepted live thread | Owner/live pending |
| AC-16 | All migrated known failure cases have explicit passing regression coverage, including Claude structured-role schema plumbing and autonomous repair restart semantics. | Deterministic | model-adapter + owner-flow + relation + provenance + fallback + atomicity + repair + packaging suites | Covered |

## Bounded-failure control criteria (1.2)

| ID | Criterion | Plane | Deterministic evidence | Status |
|---|---|---|---|---|
| BF-01 | Invalid or actionless semantic FAIL output cannot reach generation; owner and research requirements remain sequential. | Deterministic | semantic-escalation runtime dependency regressions | Covered |
| BF-02 | Pressure and edge results control only their exact accepted boundary; stale 1.1 values are ignored. | Deterministic | generation-boundary unit and runtime regressions | Covered |
| BF-03 | `STOP_BEFORE_CANDIDATE` stops, performs one validated arrival rollback, or fails as `POLICY_CONTRADICTION` without generic writer retry. | Deterministic | bounded stopping/rollback runtime regressions | Covered |
| BF-04 | A premature arrival cannot strand protected authority units in accepted prose. | Deterministic | premature-arrival acceptance regression | Covered |
| BF-05 | Returned and raised machine failures both carry redacted, dereferenceable evidence and a content-free decision trace. | Deterministic | failure-evidence, work-feed, supervisor, and security regressions | Covered |
| BF-06 | Deterministic provider failures do not repeat equivalent profiles; attempts expose typed causes and capability signatures. | Deterministic/live | model-adapter and live-smoke schema-inventory tests | Covered; target profiles pending |
| BF-07 | Unsafe/testless plans stop before review/execution and unchanged plan signatures stop before a second review. | Deterministic | repair-resume and repair-pipeline tests | Covered |
| BF-08 | Existing 1.1 SQLite/artifact state opens in 1.2 without destructive migration. | Deterministic/target | copied incident thread opened with ten history records; SQLite SHA-256 remained byte-identical | Covered in build; target upgrade pending |

## Automatic diagnostics publication criteria (1.3)

| ID | Criterion | Plane | Deterministic evidence | Status |
|---|---|---|---|---|
| DP-01 | Installer and runtime result boundaries queue and attempt publication before returning or restarting. | Deterministic/live | bootstrap, CLI, and diagnostics end-to-end tests | Covered; target authentication pending |
| DP-02 | Remote records use a strict allowlist and exclude prose, prompts, transcripts, raw errors, credentials, paths, and ZIP bytes. | Deterministic | diagnostics sentinel and schema-validation tests | Covered |
| DP-03 | Publication uses an isolated orphan branch and leaves source HEAD/status unchanged. | Deterministic | real local bare-Git integration and CLI-boundary tests | Covered |
| DP-04 | Network/auth/push failure preserves the wrapped result and queues the record for retry. | Deterministic/live | queue recovery and nonblocking-facade tests | Covered; target network pending |
| DP-05 | Replays are idempotent and non-fast-forward races refetch without force-pushing. | Deterministic | sequential/idempotency/race Git tests | Covered |
| DP-06 | `./RUN.sh publish-results` creates a snapshot and flushes queued records. | Deterministic/live | wrapper and real transport command-boundary tests | Covered; target invocation pending |

## Interactive-supervisor design criteria

These 21 rows are the approved interactive-supervisor contract. “Covered” means deterministic evidence exists in this checkout; it does not replace the final target-machine plane.

| ID | Criterion | Plane | Deterministic evidence | Status |
|---|---|---|---|---|
| IS-01 | Child SIGINT terminates the cancellable child and discards partial output. | Deterministic/live | `tests/unit/test_pause.py`; `tests/unit/test_process_runner.py` | Covered; target terminal pending |
| IS-02 | Resume reruns a cancelled node without duplicating an accepted move. | Deterministic | `tests/integration/test_supervisor_pause_resume.py` | Covered |
| IS-03 | A Pangram task ID is checkpointed before pause; resume polls without resubmission. | Deterministic/live | real SQLite Pangram pause regression | Covered; target Pangram pending |
| IS-04 | Repair promotion is checkpoint-consistent before supervision and is not repeated. | Deterministic/live | real SQLite repair-promotion regression | Covered; target repair pending |
| IS-05 | Ctrl+C during a supervisor answer cancels only that answer and leaves the graph paused. | Deterministic/live | `tests/integration/test_supervisor_cli.py` | Covered; target terminal pending |
| IS-06 | Proposal → guard → retry/accept events preserve exact chronology. | Deterministic | `tests/integration/test_live_work_feed.py` | Covered |
| IS-07 | The visible current passage equals the exact checkpointed accepted moves. | Deterministic | live-work-feed integration | Covered |
| IS-08 | Quiet model calls produce contextual heartbeats without flooding active work. | Deterministic/live | work-feed and process-runner unit tests | Covered; live timing pending |
| IS-09 | Incomplete output, raw prompts, and child stdout/stderr never enter the work feed. | Deterministic | supervisor security and work-feed regressions | Covered |
| IS-10 | Repair and Pangram state are visible without changing graph routing. | Deterministic | runtime dependency and pause regressions | Covered |
| IS-11 | A supervisor question is read-only and cannot mutate or resume a checkpoint. | Deterministic/live | same-terminal CLI integration | Covered; owner run pending |
| IS-12 | A proposed graph action waits for explicit owner confirmation. | Deterministic/live | same-terminal CLI integration | Covered; owner run pending |
| IS-13 | Redirect, rollback, rejection, correction, and unchanged-resume invalidation contracts are exact. | Deterministic | supervisor unit/integration tests | Covered |
| IS-14 | Rollback recomputes per-move coverage; legacy coverage requires two-call reconciliation. | Deterministic | supervisor action and runtime coverage tests | Covered |
| IS-15 | A general-rule candidate remains an unpromoted hypothesis. | Deterministic | supervisor and learning-scope unit tests | Covered |
| IS-16 | Malformed, stale, hash-mismatched, bad-coverage, and invalid-route actions fail closed. | Deterministic | real SQLite invalid-action matrix | Covered |
| IS-17 | Leaving and reopening restores the same thread and durable supervisor session. | Deterministic/live | supervisor CLI/session tests | Covered; target reopen pending |
| IS-18 | Credentials, raw prompts, provider transcripts, and hidden reasoning stay absent from all supervisor surfaces. | Deterministic | `tests/regression/test_supervisor_security.py` | Covered |
| IS-19 | Existing owner, repair, and Pangram contracts remain green. | Deterministic/live | full suite and focused detector/repair slices | Covered; live providers pending |
| IS-20 | The exact ZIP is deterministic and passes clean-extraction verification. | Deterministic | release tests and final review record | Pending final ZIP rebuild |
| IS-21 | Real Zorin Ctrl+C → supervisor question → confirmed redirect → same-thread continuation/pause. | Owner/live | target-machine acceptance procedure | **PENDING** |

## Build-environment and live-validation boundary

Target-machine history belongs to earlier releases and is not transferred to this candidate. The current checkout runs real LangGraph/SQLite tests deterministically, including same-thread supervisor reinterrupts and atomic Pangram/repair boundaries. Fresh live Claude/Codex smoke, Pangram version-4 candidate evidence, and the same-terminal owner workflow are still required on the target Zorin machine for the exact final ZIP.

### Pangram async API transport correction — 2026-08-11

Target-machine credential refresh reached Pangram twice but returned 401 both times. Source review showed the runtime still used `Authorization: Bearer`, an undocumented `/models` probe, and a `model` request field. Current Pangram async API documentation specifies `x-api-key` for `POST /task` and `GET /task/{task_id}`, with request body `text` plus optional `public_dashboard_link`. The current candidate follows that transport, uses an authenticated nonexistent-task GET as a zero-task access probe, and leaves the existing version-`4.0` acceptance rule intact. A returned non-`4.0` detector version stops as `bounded_detector_contract_stop` rather than entering code repair or being accepted as Pangram 4.
