# Interactive Same-Terminal Supervisor Pause Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let Joel press Ctrl+C during a real Authorial Flow run, inspect and question a safe checkpointed supervisor, confirm a direction change, and continue on the same LangGraph thread without accepting partial model output or weakening any gate.

**Architecture:** A process-local `PauseController` converts SIGINT into a pending owner-pause request. Cancelable model subprocesses terminate and raise a dedicated exception; in-process atomic operations finish and checkpoint their result before the graph routes to one durable `supervisor_pause` interrupt. A versioned allowlisted work feed supplies both live terminal events and safe supervisor snapshots. The CLI owns the free-form conversation and confirmation UI; only a validated confirmed `SupervisorAction` enters graph state.

**Tech Stack:** Python 3.10+, LangGraph 1.2.9, SQLite checkpointer, Pydantic 2, `httpx`, `pytest`, existing Claude/Codex CLI adapters, existing content-addressed `ArtifactStore` and append-only `EventJournal`.

## Global Constraints

- Implement against source commit `9683918db65c9907a081d177d22ccd6953f12415`, release SHA-256 `7bbdcefc354e1ff5ef45b57aa76b8cf55800a26b7796f3501e82452c0a84d140`.
- Preserve existing thread `f51ae3b6a22e44371ee58c4abbcf49a4e2302fe5cf1a3ec71365d77d3e0daac0`; never delete or replace `.state`, `checkpoints.sqlite`, or `current-thread.json` during upgrade.
- Article and policy material remain P0/report-only. Do not edit project inputs, source prose, owner gold, semantic gold, policy files, learning fixtures, or Pangram acceptance rules.
- Ctrl+C during Claude/Codex execution must terminate the child, discard partial stdout/stderr as a candidate, and pause on the same thread.
- Ctrl+C during Pangram submit/poll, repair promotion, or another short in-process atomic operation records a pending pause and reaches supervision only after the operation's safe update is returned for checkpointing.
- A free-form supervisor question and a model-proposed action make no graph mutation. Only an owner-confirmed normalized action may resume the interrupt.
- Never expose raw prompts, hidden reasoning, arbitrary state dictionaries, provider transcripts, child environments, API keys, or secret-bearing strings.
- Preserve the exact Pangram contract: returned version `4.0`, Human, zero AI fraction, zero AI-assisted fraction, and no AI/assisted windows.
- Do not add a browser dashboard or attachable `supervise` command in this release.
- Keep all new state fields optional and default-safe so the existing SQLite thread can resume without migration.
- Add no third-party dependency; use the standard library plus already pinned packages.
- Every behavior begins with a failing test and ends with the smallest passing implementation plus the relevant regression slice.
- The current extracted planning tree has no Git metadata. The commit commands below apply in the Git-backed execution checkout created/reconciled for implementation; do not claim these commits in an unversioned extraction.

## File and Responsibility Map

| File | Responsibility |
| --- | --- |
| `src/authorial_flow/pause.py` | Pause request state, operation context, dedicated cancellation exception, temporary SIGINT handler. |
| `src/authorial_flow/work_feed.py` | Versioned event allowlists, secret redaction, immediate terminal rendering, quiet-period heartbeat suppression. |
| `src/authorial_flow/supervisor.py` | Safe snapshot/session storage, reply/action schemas, confirmation effects, invalidation, coverage reconciliation contract. |
| `src/authorial_flow/prompts/owner_supervisor.md` | Snapshot-grounded supervisor role and strict no-mutation/no-hidden-reasoning rules. |
| `src/authorial_flow/events.py` | Chronological reads and corrupt-tail reporting while retaining locked append semantics. |
| `src/authorial_flow/process_runner.py` | Pause-aware child cancellation and provider/model/role context. |
| `src/authorial_flow/models/claude_cli.py`, `codex_cli.py` | Pass model-call context into `ProcessRunner`; do not stream transcripts. |
| `src/authorial_flow/state.py` | Optional durable pause, directive, rejection, per-move coverage, and session fields. |
| `src/authorial_flow/learning.py` | Store a general-rule candidate as an unpromoted reusable hypothesis. |
| `src/authorial_flow/nodes/generate.py` | Add current-article directives and explicitly rejected proposals to writer-visible input without exposing owner-gold examples. |
| `src/authorial_flow/nodes/owner_interrupt.py` | LangGraph supervisor interrupt and fail-closed action application. |
| `src/authorial_flow/runtime.py` | Pause-aware node guard, work events, directives, coverage ledger/reconciliation, atomic boundaries. |
| `src/authorial_flow/graph.py`, `routing.py` | One supervisor node and pause-aware routes from every machine node. |
| `src/authorial_flow/cli.py` | Same-terminal signal scope, supervisor Q&A/confirmation loop, pending-session reopen. |
| `tests/unit/test_pause.py` | Pause controller and child cancellation. |
| `tests/unit/test_work_feed.py` | Event schema, order, redaction, heartbeat quieting, corrupt-tail reads. |
| `tests/unit/test_supervisor.py` | Action validation, snapshot safety, invalidation, rollback coverage, hypothesis scope. |
| `tests/integration/test_supervisor_pause_resume.py` | Real SQLite interrupt/reopen/resume, malformed/stale actions, no duplicate move. |
| `tests/integration/test_live_work_feed.py` | Exact proposal/guard/retry/accept/current-passage chronology. |
| `tests/integration/test_supervisor_cli.py` | Free-form Q&A, confirmation, Ctrl+C inside Q&A, leave-paused, reopen. |
| Existing detector, repair, CLI, release tests | Atomic Pangram/repair pause and no-regression coverage. |

---

### Task 1: Pause Controller and Cancelable Process Boundary

**Files:**
- Create: `src/authorial_flow/pause.py`
- Modify: `src/authorial_flow/process_runner.py:13-160`
- Modify: `src/authorial_flow/models/claude_cli.py:44-53`
- Modify: `src/authorial_flow/models/codex_cli.py:45-58`
- Create: `tests/unit/test_pause.py`
- Modify: `tests/unit/test_process_runner.py:20-52`
- Modify: `tests/unit/test_model_adapters.py:40-88`

**Interfaces:**
- Produces: `OperationContext`, `PauseObservation`, `PauseController`, `OwnerPauseRequested`, `temporary_sigint_pause(...)`.
- Extends: `ProcessSpec.operation: OperationContext | None` and `ProcessRunner(..., pause_controller=None, on_start=None)`.
- Guarantees: a paused child returns no `ProcessResult`; `OwnerPauseRequested.partial_output_discarded` is always true.

- [ ] **Step 1: Write failing controller and child-cancellation tests**

```python
# tests/unit/test_pause.py
import os
import sys
import threading
from pathlib import Path

import pytest

from authorial_flow.pause import OperationContext, OwnerPauseRequested, PauseController
from authorial_flow.process_runner import ProcessRunner, ProcessSpec


def test_requested_pause_terminates_child_and_discards_partial_output():
    controller = PauseController()
    started = threading.Event()
    caught = []
    runner = ProcessRunner(
        heartbeat_seconds=0.05,
        pause_controller=controller,
        on_start=lambda payload: started.set(),
    )

    def invoke():
        try:
            runner.run(ProcessSpec(
                argv=[sys.executable, "tests/fixtures/silent_child.py", "5"],
                cwd=Path.cwd(),
                timeout_seconds=10,
                operation=OperationContext(
                    node="generation", operation="model_call", provider="claude",
                    model="claude-opus-5", role="writer", cancelable=True,
                ),
            ))
        except OwnerPauseRequested as exc:
            caught.append(exc)

    worker = threading.Thread(target=invoke)
    worker.start()
    assert started.wait(2)
    controller.request()
    worker.join(3)

    assert not worker.is_alive()
    assert len(caught) == 1
    assert caught[0].partial_output_discarded is True
    assert caught[0].operation.role == "writer"
    with pytest.raises(ProcessLookupError):
        os.kill(caught[0].pid, 0)


def test_pause_requested_before_spawn_starts_no_child():
    controller = PauseController()
    controller.request()
    starts = []
    runner = ProcessRunner(0.1, pause_controller=controller, on_start=starts.append)
    with pytest.raises(OwnerPauseRequested):
        runner.run(ProcessSpec(
            argv=[sys.executable, "tests/fixtures/silent_child.py", "0.1"],
            cwd=Path.cwd(), timeout_seconds=2,
            operation=OperationContext(node="generation", operation="model_call", cancelable=True),
        ))
    assert starts == []
```

Add adapter assertions:

```python
assert runner.specs[0].operation.provider == "claude"
assert runner.specs[0].operation.model == "claude-opus-5"
assert runner.specs[0].operation.role == "edge"
assert runner.specs[0].operation.cancelable is True
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
python -m pytest -q tests/unit/test_pause.py tests/unit/test_process_runner.py tests/unit/test_model_adapters.py
```

Expected: collection fails because `authorial_flow.pause` and `ProcessSpec.operation` do not exist.

- [ ] **Step 3: Implement the pause primitives**

Use this public shape in `pause.py`:

```python
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import signal
import threading
import time
from collections.abc import Callable, Iterator


@dataclass(frozen=True)
class OperationContext:
    node: str = ""
    operation: str = ""
    provider: str = ""
    model: str = ""
    role: str = ""
    cancelable: bool = False


@dataclass(frozen=True)
class PauseObservation:
    requested: bool
    requested_at: float
    operation: OperationContext | None


class OwnerPauseRequested(RuntimeError):
    def __init__(self, operation: OperationContext, *, pid: int = 0):
        self.operation = operation
        self.pid = pid
        self.partial_output_discarded = True
        super().__init__("owner requested a checkpointed supervisor pause")


class PauseController:
    def __init__(self) -> None:
        self._requested = threading.Event()
        self._lock = threading.RLock()
        self._requested_at = 0.0
        self._operation: OperationContext | None = None

    def request(self) -> PauseObservation:
        with self._lock:
            if not self._requested.is_set():
                self._requested_at = time.time()
                self._requested.set()
            return self.observe()

    def observe(self) -> PauseObservation:
        with self._lock:
            return PauseObservation(self._requested.is_set(), self._requested_at, self._operation)

    def requested(self) -> bool:
        return self._requested.is_set()

    def acknowledge(self) -> None:
        with self._lock:
            self._requested.clear()
            self._requested_at = 0.0

    @contextmanager
    def operation(self, value: OperationContext) -> Iterator[None]:
        with self._lock:
            self._operation = value
        try:
            yield
        finally:
            with self._lock:
                self._operation = None


@contextmanager
def temporary_sigint_pause(
    controller: PauseController,
    on_request: Callable[[PauseObservation], None],
) -> Iterator[None]:
    previous = signal.getsignal(signal.SIGINT)

    def handler(_signum, _frame):
        on_request(controller.request())

    signal.signal(signal.SIGINT, handler)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous)
```

- [ ] **Step 4: Make `ProcessRunner` poll the controller without returning partial pipes**

Add `operation` to `ProcessSpec`, add `pause_controller` and `on_start`, and wrap the existing subprocess lifetime in `controller.operation(context)`. Immediately after spawn call `on_start` with only `pid`, `provider`, `model`, `role`, `node`, and `operation`. In the polling loop, before timeout handling and after each selector drain, use:

```python
if self.pause_controller is not None and self.pause_controller.requested():
    termination_reason = "owner_pause"
    self._terminate(proc, spec.terminate_grace_seconds)
    raise OwnerPauseRequested(spec.operation or OperationContext(), pid=proc.pid)
```

Retain the existing `KeyboardInterrupt` terminate-then-kill fallback for the supervisor conversation, where the temporary graph SIGINT handler is not installed. Do not construct or return `ProcessResult` after `OwnerPauseRequested`.

Pass exact adapter context:

```python
operation=OperationContext(
    node="", operation="model_call", provider="claude",
    model=model, role=call.role, cancelable=True,
)
```

and the corresponding `provider="codex"` context in `CodexCLI`.

- [ ] **Step 5: Run GREEN and the existing process/model regressions**

Run:

```bash
python -m pytest -q tests/unit/test_pause.py tests/unit/test_process_runner.py tests/unit/test_model_adapters.py
```

Expected: all selected tests pass; timeout and stdin behavior remain unchanged.

- [ ] **Step 6: Commit the process boundary**

```bash
git add src/authorial_flow/pause.py src/authorial_flow/process_runner.py src/authorial_flow/models/claude_cli.py src/authorial_flow/models/codex_cli.py tests/unit/test_pause.py tests/unit/test_process_runner.py tests/unit/test_model_adapters.py
git commit -m "feat: add owner pause process boundary"
```

---

### Task 2: Versioned Safe Work Feed and Chronological Journal Reads

**Files:**
- Create: `src/authorial_flow/work_feed.py`
- Modify: `src/authorial_flow/events.py:9-34`
- Modify: `src/authorial_flow/runtime.py:169-253`
- Create: `tests/unit/test_work_feed.py`
- Modify: `tests/unit/test_state_storage.py:17-22`

**Interfaces:**
- Produces: `JournalRead`, `EventJournal.read_since(sequence=0)`, `WorkFeed.emit(...)`, `WorkFeed.heartbeat(...)`, `render_work_event(...)`.
- Event kinds are exactly: `flow.phase`, `model.start`, `model.heartbeat`, `proposal.complete`, `guard.result`, `generation.retry`, `move.accepted`, `passage.current`, `detector.state`, `repair.state`, `supervisor.paused`, `supervisor.action`.
- `WorkFeed` accepts only kind-specific fields and replaces configured secret values before persistence or rendering.

- [ ] **Step 1: Write failing journal, allowlist, order, and quiet-heartbeat tests**

```python
# tests/unit/test_work_feed.py
import json

from authorial_flow.events import EventJournal
from authorial_flow.work_feed import WorkFeed


def test_work_feed_is_allowlisted_redacted_and_chronological(tmp_path):
    rendered = []
    journal = EventJournal(tmp_path / "events.jsonl")
    feed = WorkFeed(
        journal=journal,
        renderer=rendered.append,
        secret_values=lambda: ["SECRET-FIXTURE"],
        silent_seconds=10,
    )
    feed.emit("proposal.complete", {
        "node": "generation", "proposal_ref": "p1", "proposal_sha256": "a" * 64,
        "text": "candidate SECRET-FIXTURE", "prompt": "must disappear",
    })
    feed.emit("guard.result", {
        "node": "generation", "gate": "fidelity", "verdict": "FAIL",
        "reason": "reason SECRET-FIXTURE", "raw_stdout": "must disappear",
    })
    read = journal.read_since(0)
    assert [row["kind"] for row in read.events] == ["proposal.complete", "guard.result"]
    blob = json.dumps(read.events) + "\n".join(rendered)
    assert "SECRET-FIXTURE" not in blob
    assert "prompt" not in blob
    assert "raw_stdout" not in blob
    assert "[REDACTED]" in blob


def test_substantive_event_restarts_heartbeat_quiet_period(tmp_path):
    now = [0.0]
    journal = EventJournal(tmp_path / "events.jsonl")
    feed = WorkFeed(journal=journal, renderer=lambda _line: None, clock=lambda: now[0], silent_seconds=10)
    feed.emit("model.start", {"provider":"claude", "model":"opus", "role":"writer", "pid":7})
    now[0] = 9.9
    assert feed.heartbeat({"provider":"claude", "model":"opus", "role":"writer", "pid":7, "elapsed_seconds":9.9}) is None
    now[0] = 10.0
    assert feed.heartbeat({"provider":"claude", "model":"opus", "role":"writer", "pid":7, "elapsed_seconds":10}) is not None
    feed.emit("guard.result", {"gate":"fidelity", "verdict":"PASS", "reason":"ok"})
    now[0] = 19.0
    assert feed.heartbeat({"provider":"claude", "model":"opus", "role":"writer", "pid":7, "elapsed_seconds":19}) is None


def test_journal_stops_at_corrupt_tail_and_reports_it(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text('{"sequence":1,"kind":"flow.phase"}\n{"sequence":2')
    read = EventJournal(path).read_since(0)
    assert [row["sequence"] for row in read.events] == [1]
    assert read.corrupt_line == 2
    assert read.corrupt_tail == '{"sequence":2'
```

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
python -m pytest -q tests/unit/test_work_feed.py tests/unit/test_state_storage.py
```

Expected: import/attribute failures for `WorkFeed` and `read_since`.

- [ ] **Step 3: Add chronological read results without treating a damaged tail as state authority**

Implement this result shape in `events.py`:

```python
@dataclass(frozen=True)
class JournalRead:
    events: tuple[dict, ...]
    corrupt_line: int = 0
    corrupt_tail: str = ""


def read_since(self, sequence: int = 0) -> JournalRead:
    if not self.path.exists():
        return JournalRead(())
    rows = []
    for line_no, raw in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            return JournalRead(tuple(rows), line_no, raw)
        if int(row.get("sequence", 0)) > sequence:
            rows.append(row)
    return JournalRead(tuple(rows))
```

Make `latest()` return the final valid event from `read_since(0)`. Keep append locking, fsync, monotonic sequence, and the existing valid-file behavior unchanged. If append encounters an already damaged tail, raise a bounded journal error rather than writing events after unreadable bytes.

- [ ] **Step 4: Implement the event schema and renderer**

Define `EVENT_FIELDS` as a literal mapping, for example:

```python
EVENT_FIELDS = {
    "flow.phase": frozenset({"thread_id", "node", "phase", "job"}),
    "model.start": frozenset({"node", "provider", "model", "role", "pid"}),
    "model.heartbeat": frozenset({"node", "provider", "model", "role", "pid", "elapsed_seconds"}),
    "proposal.complete": frozenset({"node", "proposal_ref", "proposal_sha256", "text"}),
    "guard.result": frozenset({"node", "gate", "verdict", "reason", "proposal_ref"}),
    "generation.retry": frozenset({"node", "stage", "reason", "retry_count", "proposal_ref"}),
    "move.accepted": frozenset({"node", "move_index", "proposal_ref", "text", "covered_unit_ids"}),
    "passage.current": frozenset({"node", "accepted_moves", "text", "text_sha256"}),
    "detector.state": frozenset({"stage", "task_id", "candidate_ref", "version", "result", "reason"}),
    "repair.state": frozenset({"phase", "repair_attempt", "failure_class", "repair_commit", "pass", "reason"}),
    "supervisor.paused": frozenset({"thread_id", "node", "operation", "pause_mode", "resume_node", "snapshot_ref"}),
    "supervisor.action": frozenset({"thread_id", "action_kind", "scope", "restart_depth", "resume_node", "reason"}),
}
```

`emit()` must:

1. reject an unknown event kind;
2. copy only fields listed for that kind;
3. recursively replace every nonempty configured secret value with `[REDACTED]`;
4. append `schema_version=1` through `EventJournal`;
5. render the sanitized event immediately;
6. reset `last_substantive_at` for every event except `model.heartbeat`.

The renderer may show full candidate/passage text because those are explicit article artifacts. It must never accept or render `prompt`, `stdout`, `stderr`, `env`, `argv`, or credential fields.

- [ ] **Step 5: Route runner start/heartbeat through `WorkFeed`**

Add `pause_controller` and `work_feed` to `RuntimeServices`. In `from_config`, construct one feed and wire:

```python
runner = ProcessRunner(
    config.heartbeat_seconds,
    pause_controller=pause_controller,
    on_start=lambda payload: work_feed.emit("model.start", payload),
    on_heartbeat=work_feed.heartbeat,
)
```

In `for_tests`, use `WorkFeed(journal=None, renderer=lambda _line: None)` and a fresh `PauseController` so existing direct dependency tests stay silent and deterministic.

- [ ] **Step 6: Run GREEN**

```bash
python -m pytest -q tests/unit/test_work_feed.py tests/unit/test_state_storage.py tests/unit/test_process_runner.py tests/unit/test_model_adapters.py
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit the work feed**

```bash
git add src/authorial_flow/events.py src/authorial_flow/work_feed.py src/authorial_flow/runtime.py tests/unit/test_work_feed.py tests/unit/test_state_storage.py
git commit -m "feat: add safe live work feed"
```

---

### Task 3: Safe Supervisor Snapshot, Actions, Invalidation, and Hypothesis Scope

**Files:**
- Create: `src/authorial_flow/supervisor.py`
- Create: `src/authorial_flow/prompts/owner_supervisor.md`
- Modify: `src/authorial_flow/state.py:7-109`
- Modify: `src/authorial_flow/learning.py:12-150`
- Create: `tests/unit/test_supervisor.py`
- Modify: `tests/unit/test_learning_scope.py:4-23`

**Interfaces:**
- Produces: `SupervisorAction`, `SupervisorReply`, `SupervisorSnapshot`, `SupervisorSessionStore`, `build_supervisor_snapshot(...)`, `normalize_action(...)`, `apply_supervisor_action(...)`, `CoverageReconciliationBlocked`.
- Consumes only: allowlisted checkpoint fields, recent allowlisted work events, content-addressed proposal artifacts, validated per-move coverage.
- A `GENERAL_RULE_CANDIDATE` creates `LearningScope.REUSABLE_HYPOTHESIS`; it is absent from `promoted_rules()` until the existing promotion gate passes.

- [ ] **Step 1: Write failing action and snapshot safety tests**

```python
# tests/unit/test_supervisor.py
import json
from hashlib import sha256

import pytest

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.events import EventJournal
from authorial_flow.learning import LearningScope, LearningStore
from authorial_flow.supervisor import (
    CoverageReconciliationBlocked, SupervisorAction, apply_supervisor_action,
    build_supervisor_snapshot,
)


def test_snapshot_contains_only_safe_operational_state(tmp_path):
    journal = EventJournal(tmp_path / "events.jsonl")
    journal.append("proposal.complete", {
        "schema_version":1, "proposal_ref":"proposal-1", "proposal_sha256":"a" * 64,
        "text":"Complete unaccepted proposal.", "node":"generation",
    })
    state = {
        "thread_id":"thread-1", "source_hash":"source-hash", "task_mode":"P2S",
        "section_job":"follow the question", "accepted_moves":["Accepted."],
        "atom_coverage":{"u1":True}, "entry_edge_result":{"verdict":"FAIL","reason":"bad edge"},
        "pangram_task_id":"task-1", "PANGRAM_API_KEY":"SECRET", "raw_prompt":"HIDDEN",
    }
    snapshot = build_supervisor_snapshot(state, journal=journal, store=ArtifactStore(tmp_path / "artifacts"))
    blob = json.dumps(snapshot.model_dump(mode="json"))
    assert "Complete unaccepted proposal." in blob
    assert "Accepted." in blob
    assert "task-1" in blob
    assert "SECRET" not in blob
    assert "HIDDEN" not in blob
    assert "raw_prompt" not in blob


def test_rollback_truncates_moves_and_recomputes_coverage():
    moves = ["one", "two", "three"]
    state = {
        "accepted_moves":moves,
        "accepted_move_coverage":[
            {"move_sha256":sha256(b"one").hexdigest(), "covered_unit_ids":["u1"]},
            {"move_sha256":sha256(b"two").hexdigest(), "covered_unit_ids":["u2"]},
            {"move_sha256":sha256(b"three").hexdigest(), "covered_unit_ids":["u3"]},
        ],
        "atom_coverage":{"u1":True,"u2":True,"u3":True},
        "candidate_ref":"stale", "pangram_task_id":"remote-task",
        "supervisor_resume_node":"generation", "supervisor_pre_pause_status":"continue_generation",
    }
    update = apply_supervisor_action(
        state,
        SupervisorAction(kind="ROLLBACK", rollback_count=2, reason="The turn went wrong."),
    )
    assert update["accepted_moves"] == ["one"]
    assert update["atom_coverage"] == {"u1":True,"u2":False,"u3":False}
    assert update["candidate_ref"] == ""
    assert update["pangram_task_id"] == ""
    assert update["supervisor_resume_node"] == "generation"


def test_legacy_rollback_fails_closed_without_validated_reconciliation():
    state = {"accepted_moves":["one","two"], "accepted_move_coverage":[]}
    with pytest.raises(CoverageReconciliationBlocked):
        apply_supervisor_action(
            state, SupervisorAction(kind="ROLLBACK", rollback_count=1, reason="bad"),
            reconcile_coverage=lambda _state: None,
        )


def test_general_rule_candidate_is_not_promoted(tmp_path):
    store = LearningStore(tmp_path)
    state = {"project_id":"p", "supervisor_resume_node":"generation"}
    update = apply_supervisor_action(
        state,
        SupervisorAction(
            kind="REDIRECT", instruction="Follow the concrete contradiction.",
            scope="GENERAL_RULE_CANDIDATE", restart_depth="GENERATION_FROM_PREFIX",
            reason="Try this here and preserve it only as a hypothesis.",
        ),
        learning_store=store,
    )
    record = store.get(update["new_supervisor_learning_ref"])
    assert record.scope is LearningScope.REUSABLE_HYPOTHESIS
    assert store.promoted_rules() == []
```

Also assert:

- `REJECT_PROPOSAL` fails when the proposal ref/hash differs from the current safe snapshot;
- `CORRECT_MEANING` clears representation and prose fields but preserves `source_ref`, `requirements_ref`, `owner_gold_ref`, `protected_input_hashes`, and `thread_id`;
- `RESUME_UNCHANGED` preserves an atomically completed Pangram task ID and uses the stored resume node;
- invalid counts, scopes, and restart depths fail before mutation.

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
python -m pytest -q tests/unit/test_supervisor.py tests/unit/test_learning_scope.py
```

Expected: import failures for `authorial_flow.supervisor` and no reusable-hypothesis append route.

- [ ] **Step 3: Add strict reply/action models**

Use Pydantic models with `ConfigDict(extra="forbid")`. Keep the action flat and explicit:

```python
class SupervisorAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["RESUME_UNCHANGED", "REJECT_PROPOSAL", "ROLLBACK", "REDIRECT", "CORRECT_MEANING"]
    reason: str
    instruction: str = ""
    scope: Literal["NONE", "NEXT_ATTEMPT", "CURRENT_ARTICLE", "GENERAL_RULE_CANDIDATE"] = "NONE"
    restart_depth: Literal["CURRENT_STAGE", "GENERATION_FROM_PREFIX", "REPRESENTATION_FROM_SOURCE"] = "CURRENT_STAGE"
    rollback_count: int = 0
    proposal_ref: str = ""
    proposal_sha256: str = ""


class ProposedSupervisorAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["NONE", "RESUME_UNCHANGED", "REJECT_PROPOSAL", "ROLLBACK", "REDIRECT", "CORRECT_MEANING"]
    reason: str = ""
    instruction: str = ""
    scope: Literal["NONE", "NEXT_ATTEMPT", "CURRENT_ARTICLE", "GENERAL_RULE_CANDIDATE"] = "NONE"
    restart_depth: Literal["CURRENT_STAGE", "GENERATION_FROM_PREFIX", "REPRESENTATION_FROM_SOURCE"] = "CURRENT_STAGE"
    rollback_count: int = 0
    proposal_ref: str = ""
    proposal_sha256: str = ""


class SupervisorReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str
    inferences: list[str]
    uncertainties: list[str]
    proposed_action: ProposedSupervisorAction
```

The validator must require nonempty `instruction` for `REDIRECT`/`CORRECT_MEANING`, a non-`NONE` scope for `REDIRECT`, positive `rollback_count` for `ROLLBACK`, and exact ref/hash for `REJECT_PROPOSAL`. Controller code recomputes effects and invalidated fields; it never trusts a model-authored effect list.

- [ ] **Step 4: Add optional backward-compatible state fields**

Append these optional keys to `AuthorialState`:

```python
accepted_move_coverage: list[dict[str, Any]]
coverage_reconciliation_required: bool
owner_directives: list[dict[str, Any]]
consumed_directive_ids: list[str]
rejected_proposals: list[dict[str, Any]]
owner_authority_corrections: list[dict[str, Any]]
supervisor_resume_node: str
supervisor_snapshot_ref: str
supervisor_session_ref: str
supervisor_pause_mode: str
supervisor_pre_pause_status: str
supervisor_interrupted_node: str
supervisor_interrupted_operation: str
supervisor_validation_error: str
new_supervisor_learning_ref: str
```

Do not make any field required and do not alter reducers on existing keys.

- [ ] **Step 5: Implement explicit invalidation maps**

Use concrete empty values because LangGraph state updates do not delete omitted keys. Preserve only `regressions_hard_pass` inside `final_local_gates` when prose is invalidated.

```python
PROSE_DOWNSTREAM_CLEAR = {
    "candidate_ref":"", "candidate_text_ref":"", "candidate_spans":[],
    "entry_edge_result":{}, "full_edge_result":{}, "relation_result":{},
    "semantic_result":{}, "stop_result":{},
    "recommended_candidate_ref":"", "pending_detector_variant_ref":"",
    "pangram_human_variant_ref":"", "pangram_result_ref":"",
    "pangram_task_id":"", "pangram_request_identity":"",
    "pangram_candidate_ref":"", "pangram_submitted_at":0.0,
    "detector_returned_version":"", "detector_account_action":"",
    "interrupt_payload":{}, "owner_response":{}, "active_interrupt_kind":"",
}

REPRESENTATION_CLEAR = {
    "section_job":"", "atom_refs":[], "atom_coverage":{},
    "accepted_moves":[], "accepted_move_coverage":[], "accepted_prefix_hash":"",
    "move_index":0, "retry_count":0, "rollback_count":0,
    "semantic_sanity_ref":"", "resolved_concept_ref":"", "developmental_ref":"",
    "research_ref":"", "faithful_position_ref":"", "better_reasoned_alternative_ref":"",
}
```

Every action must set a concrete `supervisor_resume_node`, restore/set a non-pause status, clear `supervisor_validation_error`, and leave `thread_id`, source/project refs, protected hashes, immutable regression refs, and policy identity unchanged.

- [ ] **Step 6: Add safe snapshot and durable transcript storage**

`build_supervisor_snapshot()` copies only named safe fields, derives `current_passage = " ".join(accepted_moves)`, and selects the newest `proposal.complete` not matched by a later `move.accepted` for the same `proposal_ref`. Store snapshots content-addressably. Store conversation turns separately at `.state/supervisor/<thread-id>/<pause-id>.jsonl`; the checkpoint keeps the stable relative `supervisor_session_ref`, so questions append transcript turns without mutating graph state.

The supervisor prompt must say:

```markdown
Answer only from the supplied safe snapshot and visible session transcript.
Label inferences and uncertainty. Never claim access to hidden reasoning, raw prompts,
provider transcripts, credentials, or state fields absent from the snapshot.
You may propose one action, but you cannot apply it. Use kind NONE when the owner is only asking a question.
Never weaken semantic, fidelity, cold-audit, regression, repair, or Pangram gates.
```

- [ ] **Step 7: Add reusable hypotheses without auto-promotion**

Add `LearningKind.OWNER_DIRECTION` and `LearningStore.append_hypothesis(...)`, persisting an event with scope `REUSABLE_HYPOTHESIS`. Extend `records()` to load both `OWNER_JUDGMENT` and `HYPOTHESIS` base events. Do not change `promoted_rules()`; only records later promoted to `GENERAL_RULE` may appear there.

- [ ] **Step 8: Run GREEN**

```bash
python -m pytest -q tests/unit/test_supervisor.py tests/unit/test_learning_scope.py tests/regression/test_learning_isolation.py
```

Expected: all selected tests pass, including existing owner-gold isolation.

- [ ] **Step 9: Commit the supervisor state model**

```bash
git add src/authorial_flow/supervisor.py src/authorial_flow/prompts/owner_supervisor.md src/authorial_flow/state.py src/authorial_flow/learning.py tests/unit/test_supervisor.py tests/unit/test_learning_scope.py
git commit -m "feat: add validated supervisor actions"
```

---

### Task 4: Checkpointed Supervisor Graph Interrupt and Pause-Aware Routing

**Files:**
- Modify: `src/authorial_flow/nodes/owner_interrupt.py:133-167`
- Modify: `src/authorial_flow/graph.py:23-84`
- Modify: `src/authorial_flow/routing.py:6-109`
- Modify: `src/authorial_flow/runtime.py:1192-1248,1415-1435`
- Create: `tests/integration/test_supervisor_pause_resume.py`
- Modify: `tests/integration/test_graph_resume.py`

**Interfaces:**
- Consumes: `PauseController`, `OwnerPauseRequested`, safe snapshot/action functions from Tasks 1–3.
- Produces: `supervisor_pause` graph node, `route_after_supervisor(state)`, and pause-aware routes from all machine nodes.
- Guarantees: cancelled work resumes its interrupted node; atomically completed work resumes its natural next node.

- [ ] **Step 1: Write failing real-LangGraph pause/reopen/resume tests**

```python
# tests/integration/test_supervisor_pause_resume.py
import pytest

pytest.importorskip("langgraph")
from langgraph.types import Command

from authorial_flow.config import RuntimeConfig
from authorial_flow.graph import open_graph
from authorial_flow.runtime import build_runtime_dependencies


def test_cancelled_generation_pauses_and_resumes_same_thread_without_duplicate_move(tmp_path, runtime_services):
    cfg = RuntimeConfig.from_root(tmp_path)
    runtime_services.pause_controller.request()
    deps = build_runtime_dependencies(cfg, project_root=runtime_services.project_root, services=runtime_services)
    graph_config = {"configurable":{"thread_id":"same-thread"}}
    seed = runtime_services.represented_state(accepted_moves=["preserved"])

    with open_graph(cfg, deps) as app:
        first = app.invoke(seed, graph_config)
        assert first["__interrupt__"][0].value["kind"] == "SUPERVISOR"
        assert first["thread_id"] == "same-thread"
        assert first["accepted_moves"] == ["preserved"]
        assert first["supervisor_resume_node"] == "generation"

    with open_graph(cfg, deps) as app:
        second = app.invoke(Command(resume={
            "kind":"RESUME_UNCHANGED", "reason":"Continue.", "instruction":"",
            "scope":"NONE", "restart_depth":"CURRENT_STAGE", "rollback_count":0,
            "proposal_ref":"", "proposal_sha256":"",
        }), graph_config)
        assert second["thread_id"] == "same-thread"
        assert second["accepted_moves"].count("preserved") == 1
```

Add a malformed-action case that resumes with `{"kind":"ROLLBACK","rollback_count":0}` and asserts the invocation returns a fresh `SUPERVISOR` interrupt with `supervisor_validation_error`, unchanged `accepted_moves`, and unchanged `pangram_task_id`.

- [ ] **Step 2: Run the integration test and verify RED**

```bash
python -m pytest -q tests/integration/test_supervisor_pause_resume.py tests/integration/test_graph_resume.py
```

Expected: no supervisor node/route exists.

- [ ] **Step 3: Add one supervisor dependency and node**

Extend `GraphDependencies`:

```python
supervisor: NodeFn = _noop
```

Register `supervisor_pause`, then use conditional edges from it to every legal resume destination:

```python
builder.add_node("supervisor_pause", dependencies.supervisor)
builder.add_conditional_edges(
    "supervisor_pause", route_after_supervisor,
    {name:name for name in (
        "regressions", "representation", "generation", "cold_audit", "freeze",
        "detector", "owner_review", "owner_ambiguity", "research_adoption",
        "owner_learning", "repair", "repair_restart", "finalize", "supervisor_pause",
    )},
)
```

Build the dependency as a closure over services/project root. The node calls `interrupt(snapshot_payload)`, validates/applies the returned action, emits `supervisor.action`, and returns the action update. On validation, stale-reference, or coverage-reconciliation failure, return:

```python
{
    "status":"supervisor_action_invalid",
    "supervisor_validation_error":str(exc),
    "supervisor_resume_node":snapshot.resume_node,
}
```

The invalid status routes to a new durable interrupt while preserving the original
natural resume destination for a later valid action.

- [ ] **Step 4: Make every machine route recognize a pause before its ordinary status**

Add:

```python
SUPERVISOR_STATUSES = {"supervisor_pause_requested", "supervisor_action_invalid"}


def _pause_route(state):
    return "supervisor_pause" if str(state.get("status") or "") in SUPERVISOR_STATUSES else ""
```

Call it first in `route_after_regressions`, `route_after_representation`, `route_generation`, `route_after_cold_audit`, `route_after_detector`, `route_after_owner_learning`, and `route_after_repair`. Replace the direct `freeze -> detector` edge with a `route_after_freeze` conditional returning `supervisor_pause` or `detector`. Add `supervisor_pause` to every corresponding mapping.

`route_after_supervisor` returns `supervisor_pause` for invalid actions; otherwise it validates `supervisor_resume_node` against the fixed allowed set and fails closed to `supervisor_pause` on an unknown value.

- [ ] **Step 5: Make `_guarded_node` convert the pause into a durable update**

Change its signature to accept a natural-next resolver:

```python
def _guarded_node(name, fn, services, natural_next):
```

Required order:

1. emit `flow.phase`;
2. if a pause is already pending, create a cancelled pause update with `resume_node=name` without calling `fn`;
3. call `fn`;
4. catch `OwnerPauseRequested` before generic exceptions and create a cancelled pause update with `resume_node=name`;
5. if `fn` returns normally while a request is pending, merge `state + update`, compute `resume_node=natural_next(merged)`, and create an `ATOMIC_COMPLETE` pause update containing all returned fields;
6. persist the safe snapshot and session ref, emit `supervisor.paused`, acknowledge the controller, and return `status=supervisor_pause_requested`;
7. retain the existing `KeyboardInterrupt` and machine-failure handling.

Pass exact natural-next resolvers in `build_runtime_dependencies`: existing route functions for conditional nodes, `lambda _state: "detector"` for freeze, and `route_after_repair` for repair promotion.

- [ ] **Step 6: Run GREEN and existing graph routing tests**

```bash
python -m pytest -q tests/integration/test_supervisor_pause_resume.py tests/integration/test_graph_resume.py tests/unit/test_failure_routing.py tests/integration/test_repair_resume.py
```

Expected: new same-thread supervisor tests pass and existing owner/machine interrupts still resume.

- [ ] **Step 7: Commit the graph control path**

```bash
git add src/authorial_flow/nodes/owner_interrupt.py src/authorial_flow/graph.py src/authorial_flow/routing.py src/authorial_flow/runtime.py tests/integration/test_supervisor_pause_resume.py tests/integration/test_graph_resume.py
git commit -m "feat: checkpoint owner supervisor pauses"
```

---

### Task 5: Runtime Events, Directives, Proposal Rejection, and Per-Move Coverage

**Files:**
- Modify: `src/authorial_flow/runtime.py:256-287,512-697,715-1181,1250-1413`
- Modify: `src/authorial_flow/nodes/generate.py:55-68`
- Modify: `src/authorial_flow/supervisor.py`
- Create: `tests/integration/test_live_work_feed.py`
- Create: `tests/integration/test_supervisor_actions.py`
- Modify: `tests/integration/test_runtime_dependencies.py`

**Interfaces:**
- Produces: exact operational events, `accepted_move_coverage`, directive prompt blocks, rejected-proposal memory, strict legacy coverage reconciliation.
- A `NEXT_ATTEMPT` directive is consumed only when its generation attempt returns a checkpointable update; an interrupted attempt is retried with the directive.
- A proposal event is complete only after a model call returns and its text artifact is stored.

- [ ] **Step 1: Write the failing exact-order feed test**

```python
# tests/integration/test_live_work_feed.py
def test_fake_flow_prints_complete_operational_sequence_and_exact_current_passage(tmp_path, flow_services):
    state = flow_services.represented_state()
    first = flow_services.dependencies.generation(state)       # first guard fails
    state.update(first)
    second = flow_services.dependencies.generation(state)      # second proposal passes

    rows = flow_services.journal.read_since(0).events
    kinds = [row["kind"] for row in rows if row["kind"] in {
        "proposal.complete", "guard.result", "generation.retry",
        "move.accepted", "passage.current",
    }]
    assert kinds == [
        "proposal.complete", "guard.result", "generation.retry",
        "proposal.complete", "guard.result", "guard.result", "move.accepted", "passage.current",
    ]
    passage = [row for row in rows if row["kind"] == "passage.current"][-1]
    assert passage["accepted_moves"] == second["accepted_moves"]
    assert passage["text"].encode("utf-8") == " ".join(second["accepted_moves"]).encode("utf-8")
```

Also test that a writer returning partial/multiple spans never emits `move.accepted`, and that a `proposal.complete` event contains only the complete stored candidate—not runner stdout fragments.

- [ ] **Step 2: Write failing directive, rejection, and correction tests**

```python
def test_next_attempt_directive_is_consumed_after_one_checkpointed_generation(flow_services):
    state = flow_services.represented_state(owner_directives=[{
        "id":"d1", "instruction":"Start from the concrete contradiction.",
        "scope":"NEXT_ATTEMPT", "restart_depth":"CURRENT_STAGE", "consumed":False,
    }])
    update = flow_services.dependencies.generation(state)
    writer_prompt = flow_services.claude.calls_for("writer")[-1].prompt
    assert "Start from the concrete contradiction." in writer_prompt
    assert "d1" in update["consumed_directive_ids"]

    state.update(update)
    flow_services.dependencies.generation(state)
    second_prompt = flow_services.claude.calls_for("writer")[-1].prompt
    assert "Start from the concrete contradiction." not in second_prompt


def test_rejected_proposal_and_owner_reason_reach_writer_but_owner_gold_does_not(flow_services):
    rejected_ref = flow_services.store.put_text("Do not repeat this proposal.", "md", {"kind":"proposal"}).sha256
    state = flow_services.represented_state(rejected_proposals=[{
        "proposal_ref":rejected_ref, "proposal_sha256":rejected_ref,
        "reason":"It dodges the live question.",
    }])
    flow_services.dependencies.generation(state)
    prompt = flow_services.claude.calls_for("writer")[-1].prompt
    assert "Do not repeat this proposal." in prompt
    assert "It dodges the live question." in prompt
    assert "owner-neg-sidestep-live-question" not in prompt
```

Add a meaning-correction representation test asserting the correction is supplied to the representation prompt and installed as an `OWNER_GROUNDED` authority unit without changing the source artifact bytes.

- [ ] **Step 3: Run the new tests and verify RED**

```bash
python -m pytest -q tests/integration/test_live_work_feed.py tests/integration/test_supervisor_actions.py tests/integration/test_runtime_dependencies.py
```

Expected: event sequence/directive/coverage assertions fail.

- [ ] **Step 4: Seed and maintain the per-move coverage ledger**

Seed:

```python
"accepted_move_coverage": [],
"coverage_reconciliation_required": False,
"owner_directives": [],
"consumed_directive_ids": [],
"rejected_proposals": [],
"owner_authority_corrections": [],
```

On a fidelity-pass acceptance append:

```python
coverage_row = {
    "move_sha256": sha256(candidate.encode("utf-8")).hexdigest(),
    "covered_unit_ids": sorted({uid for uid in fidelity["covered_unit_ids"] if uid in coverage}),
}
```

On the existing automatic one-move rollback, truncate `accepted_move_coverage` with `accepted_moves`, then recompute every `atom_coverage` value from retained rows. If cold revision changes the complete text, set `accepted_move_coverage=[]` and `coverage_reconciliation_required=True`; retain aggregate coverage because the existing strict whole-candidate fidelity pass preserves the represented meaning.

- [ ] **Step 5: Implement bounded two-call coverage reconciliation**

When rollback sees a missing, length-mismatched, or hash-mismatched ledger:

1. call Codex role `coverage_reconciliation` with the authority units and numbered accepted moves, requiring one row per move with the exact index/hash and `covered_unit_ids`;
2. reject unknown unit IDs, duplicate/missing indices, or hash mismatch locally;
3. call separate Codex role `coverage_reconciliation_check` with source, units, moves, and proposed mapping, requiring `{"verdict":"PASS|FAIL","reason":"..."}`;
4. accept only `PASS`; otherwise raise `CoverageReconciliationBlocked` and return to the supervisor interrupt without truncating anything.

Use strict schemas:

```python
MOVE_COVERAGE_SCHEMA = {
    "type":"object", "additionalProperties":False,
    "properties":{"moves":{"type":"array","items":{
        "type":"object", "additionalProperties":False,
        "properties":{
            "index":{"type":"integer"}, "move_sha256":{"type":"string"},
            "covered_unit_ids":{"type":"array","items":{"type":"string"}},
        },
        "required":["index","move_sha256","covered_unit_ids"],
    }}},
    "required":["moves"],
}
```

- [ ] **Step 6: Add directive application without modifying policy files**

Create a helper that returns applicable directive text for a stage. `CURRENT_ARTICLE` and `GENERAL_RULE_CANDIDATE` apply to representation, developmental/research representation, writer generation, cold audit/revision, entry/full/fidelity guards, and detector-variant fidelity/audit. `NEXT_ATTEMPT` applies only to the next checkpointable writer attempt.

Append a bounded JSON block named `CONFIRMED OWNER DIRECTIONS` to applicable model inputs. Never splice instructions into the canonical policy prompt files.

For `CORRECT_MEANING`, append all durable `owner_authority_corrections` to the representation input and ensure each becomes an `AuthorityUnit` with `authority=OWNER_GROUNDED`, `exact_lock=False`, and reason `owner supervisor meaning correction`, even if the representation model omits it.

- [ ] **Step 7: Extend writer input with article-local rejections**

Change the signature to:

```python
def writer_payload(
    section_job: str,
    units: list[AuthorityUnit],
    accepted_moves: list[str],
    pressure: dict,
    promoted_rules: list[dict] | None = None,
    owner_directives: list[dict] | None = None,
    rejected_proposals: list[dict] | None = None,
) -> dict:
```

Include only the current article's explicitly confirmed directive/rejection text. Keep raw source, owner-gold cases, locked-test bodies, and unrelated learning records absent.

- [ ] **Step 8: Emit explicit proposal, guard, retry, acceptance, detector, and repair events**

Add a small `_emit(services, kind, payload)` helper. Required emission points:

- store the complete writer candidate, then `proposal.complete` before any guard;
- `guard.result` after deterministic edge, entry edge, full edge, local relation, model fidelity, each cold audit, and each detector-variant fidelity/audit;
- `generation.retry` with the actual rejected stage/reason before each retry update;
- wrapper-level `move.accepted` and `passage.current` from the exact returned `accepted_moves` update;
- `detector.state` for access check, submitted task checkpoint, poll, returned version/result, retry/account stop;
- replace existing `repair:<phase>` direct print/journal calls with `repair.state` while retaining the same visible phase names.

Never emit `ModelResult.text`, stdout/stderr refs, prompts, or child environments as work-feed fields.

- [ ] **Step 9: Run GREEN and no-leak regressions**

```bash
python -m pytest -q tests/integration/test_live_work_feed.py tests/integration/test_supervisor_actions.py tests/integration/test_runtime_dependencies.py tests/regression/test_learning_isolation.py tests/unit/test_developmental_authority.py
```

Expected: exact order and directive-scope tests pass; owner-gold isolation remains green.

- [ ] **Step 10: Commit runtime steering semantics**

```bash
git add src/authorial_flow/runtime.py src/authorial_flow/nodes/generate.py src/authorial_flow/supervisor.py tests/integration/test_live_work_feed.py tests/integration/test_supervisor_actions.py tests/integration/test_runtime_dependencies.py
git commit -m "feat: expose and steer checkpointed authorial work"
```

---

### Task 6: Same-Terminal Supervisor Conversation and Confirmation UI

**Files:**
- Modify: `src/authorial_flow/cli.py:111-120,407-505`
- Modify: `src/authorial_flow/supervisor.py`
- Create: `tests/integration/test_supervisor_cli.py`
- Modify: `tests/integration/test_cli.py`
- Modify: `RUN.sh:8-16` only if command forwarding needs correction; do not add `supervise`.

**Interfaces:**
- Produces: `_supervisor_interrupt(result)`, `_invoke_with_pause_signal(...)`, `run_supervisor_loop(...)`, `_continue_with_supervision(...)`.
- Consumes: safe snapshot/session ref and the configured Codex adapter under role `owner_supervisor`.
- Returns: a confirmed `SupervisorAction` payload or `None` for leave-paused/noninteractive mode.

- [ ] **Step 1: Write failing CLI behavior tests**

```python
# tests/integration/test_supervisor_cli.py
def test_question_does_not_resume_graph_until_action_is_confirmed(monkeypatch, supervisor_cli_fixture):
    calls = []
    supervisor_cli_fixture.queue_graph_results(
        supervisor_cli_fixture.paused_result(),
        {"status":"continue_generation", "accepted_moves":["kept"]},
    )
    supervisor_cli_fixture.queue_inputs(
        "Why is it rewriting this paragraph?",
        "Redirect it toward the contradiction.",
        "y",
    )
    supervisor_cli_fixture.queue_supervisor_replies(
        {"answer":"The writer is retrying after a fidelity failure.", "inferences":[], "uncertainties":[],
         "proposed_action":{"kind":"NONE","reason":"","instruction":"","scope":"NONE","restart_depth":"CURRENT_STAGE","rollback_count":0,"proposal_ref":"","proposal_sha256":""}},
        {"answer":"I can redirect the remaining generation.", "inferences":[], "uncertainties":[],
         "proposed_action":{"kind":"REDIRECT","reason":"Follow Joel's correction.","instruction":"Develop the concrete contradiction.","scope":"CURRENT_ARTICLE","restart_depth":"GENERATION_FROM_PREFIX","rollback_count":0,"proposal_ref":"","proposal_sha256":""}},
    )

    supervisor_cli_fixture.run()
    calls = supervisor_cli_fixture.graph_calls
    assert len(calls) == 2
    assert calls[0].initial is None
    assert calls[1].initial.resume["kind"] == "REDIRECT"
    assert calls[1].initial.resume["instruction"] == "Develop the concrete contradiction."


def test_leave_keeps_interrupt_pending_and_reopen_loads_same_session(supervisor_cli_fixture):
    paused = supervisor_cli_fixture.paused_result(session_ref="thread-1/pause-1.jsonl")
    supervisor_cli_fixture.queue_graph_results(paused)
    supervisor_cli_fixture.queue_inputs("leave")
    supervisor_cli_fixture.run()
    assert len(supervisor_cli_fixture.graph_calls) == 1
    assert supervisor_cli_fixture.session_store.read("thread-1/pause-1.jsonl")


def test_ctrl_c_during_supervisor_answer_keeps_graph_paused(supervisor_cli_fixture):
    supervisor_cli_fixture.queue_graph_results(supervisor_cli_fixture.paused_result())
    supervisor_cli_fixture.queue_inputs("What is happening?", "leave")
    supervisor_cli_fixture.queue_supervisor_exceptions(KeyboardInterrupt())
    supervisor_cli_fixture.run()
    assert len(supervisor_cli_fixture.graph_calls) == 1
    assert "still paused" in supervisor_cli_fixture.stderr.lower()
```

- [ ] **Step 2: Run the CLI tests and verify RED**

```bash
python -m pytest -q tests/integration/test_supervisor_cli.py tests/integration/test_cli.py
```

Expected: same-terminal loop helpers do not exist.

- [ ] **Step 3: Install SIGINT only while graph machine work is running**

Wrap each `app.invoke(...)` used for ordinary machine execution with:

```python
with temporary_sigint_pause(services.pause_controller, render_pause_request):
    result = app.invoke(initial, graph_config)
```

`render_pause_request` prints one line. If `observation.operation.cancelable` is true, say the active model call is being cancelled; otherwise say the pause is pending while the current atomic operation reaches its checkpoint boundary. Restore the prior SIGINT handler before entering supervisor Q&A.

- [ ] **Step 4: Implement the safe free-form supervisor loop**

Required loop behavior:

```python
while True:
    user_text = input("supervisor> ").strip()
    if user_text.lower() in {"leave", "leave paused", "exit"}:
        print("Run remains paused. ./RUN.sh will reopen this supervisor session.")
        return None
    session_store.append(session_ref, "user", user_text)
    try:
        reply = ask_owner_supervisor(snapshot, session_store.read(session_ref), services)
    except KeyboardInterrupt:
        print("Supervisor answer cancelled; the graph is still paused.", file=sys.stderr)
        continue
    session_store.append(session_ref, "assistant", reply.answer)
    render_supervisor_reply(reply)
    if reply.proposed_action.kind == "NONE":
        continue
    action, effect = normalize_action(reply.proposed_action, snapshot)
    render_confirmed_effect(effect)
    if input("Apply this action? [y/N] ").strip().lower() not in {"y", "yes"}:
        continue
    return action
```

`ask_owner_supervisor` uses `ModelCall(..., role="owner_supervisor")` with only the safe snapshot and visible transcript. The controller, not the model, renders exact fields cleared, moves removed, scope, restart depth, and resume node.

- [ ] **Step 5: Reuse one continuation driver from run/resume/answer**

After any graph invocation, detect an interrupt whose payload kind is `SUPERVISOR`. If interactive, open the loop immediately; if the owner confirms, call the same graph on the same thread with `Command(resume=action.model_dump(mode="json"))`; if the owner leaves, return without finalization or generic owner JSON output. Repeat if another supervisor interrupt is reached.

If stdin is noninteractive, print a bounded message that the run remains paused and exit zero; do not invent an action. `./RUN.sh` already selects `resume` when `current-thread.json` exists, so it must reopen the pending interrupt. Preserve existing owner-review `answer` behavior and machine-restart handling.

- [ ] **Step 6: Run GREEN and full CLI regressions**

```bash
python -m pytest -q tests/integration/test_supervisor_cli.py tests/integration/test_cli.py tests/integration/test_graph_resume.py
```

Expected: all selected tests pass; CLI help still contains only `run`, `resume`, `status`, `answer`, and `package`.

- [ ] **Step 7: Commit the terminal experience**

```bash
git add src/authorial_flow/cli.py src/authorial_flow/supervisor.py tests/integration/test_supervisor_cli.py tests/integration/test_cli.py RUN.sh
git commit -m "feat: open supervisor conversation on ctrl-c"
```

---

### Task 7: Atomic Pangram/Repair Boundaries and Security Regression Matrix

**Files:**
- Modify: `tests/integration/test_runtime_dependencies.py:732-884`
- Modify: `tests/integration/test_repair_resume.py`
- Modify: `tests/integration/test_supervisor_pause_resume.py`
- Create: `tests/regression/test_supervisor_security.py`
- Modify production files only when a failing acceptance test exposes a missing boundary.

**Interfaces:**
- Verifies the combined Tasks 1–6 contract rather than introducing a second pause mechanism.
- Uses real LangGraph/SQLite with fake provider and Pangram/repair boundaries.

- [ ] **Step 1: Add the Pangram task-ID-before-pause regression**

Create a fake async Pangram whose `submit()` calls `services.pause_controller.request()` immediately before returning `PangramTask("task-1", ...)`. Run detector through the real graph and assert:

```python
assert first["__interrupt__"][0].value["kind"] == "SUPERVISOR"
assert first["pangram_task_id"] == "task-1"
assert first["supervisor_pause_mode"] == "ATOMIC_COMPLETE"
assert first["supervisor_resume_node"] == "detector"
assert pangram.submits == 1
```

Reopen SQLite, resume unchanged, and assert the client polls `task-1` without a second submit.

- [ ] **Step 2: Add repair-promotion consistency regression**

Use a repair dependency that requests pause and returns:

```python
{
    "status":"repair_promoted_restart_required",
    "restart_required":True,
    "program_version":"new-program",
    "repair_commit":"repair-sha",
    "repair_resume_node":"generation",
}
```

Assert the checkpointed supervisor state contains the promoted commit/version, pause mode `ATOMIC_COMPLETE`, and natural resume node `repair_restart`. Resume and verify the existing `MACHINE_RESTART` boundary is reached without promoting twice.

- [ ] **Step 3: Add stale-reference and malformed-action regressions**

Assert each case returns another supervisor interrupt and leaves all content/detector fields byte-for-byte unchanged:

- rejection ref differs from the snapshot ref;
- rejection hash differs from the artifact hash;
- rollback count is zero or greater than move count;
- coverage reconciliation returns a missing move or unknown unit;
- action contains an extra key;
- resume node is outside the fixed allowed set.

- [ ] **Step 4: Add end-to-end secret/non-disclosure regression**

```python
# tests/regression/test_supervisor_security.py
def test_secret_fixture_and_raw_operational_material_never_reach_feed_snapshot_or_supervisor_prompt(supervisor_security_fixture):
    secret = "PANGRAM-SECRET-FIXTURE-4927"
    result = supervisor_security_fixture.run_with(
        environment={"PANGRAM_API_KEY":secret},
        raw_prompt=f"hidden prompt {secret}",
        stdout=f"partial output {secret}",
        stderr=f"provider error {secret}",
    )
    for blob in (
        result.terminal_text, result.events_text, result.snapshot_text,
        result.supervisor_prompt, result.session_text,
    ):
        assert secret not in blob
        assert "hidden prompt" not in blob
        assert "partial output" not in blob
    assert "[REDACTED]" in result.events_text or "[REDACTED]" in result.terminal_text
```

Also assert complete article proposal text remains visible, proving redaction does not erase the artifact Joel needs to judge.

- [ ] **Step 5: Run RED, implement only exposed boundary gaps, then run GREEN**

```bash
python -m pytest -q \
  tests/integration/test_supervisor_pause_resume.py \
  tests/integration/test_runtime_dependencies.py \
  tests/integration/test_repair_resume.py \
  tests/regression/test_supervisor_security.py
```

Expected after repairs: all selected tests pass; Pangram submit count is one and repair promotion count is one.

- [ ] **Step 6: Run all existing detector/repair regressions**

```bash
python -m pytest -q tests/unit/test_pangram.py tests/integration/test_detector_downstream.py tests/repair tests/integration/test_repair_resume.py tests/integration/test_bootstrap_repair.py
```

Expected: all tests pass; version-4 and autonomous-repair contracts are unchanged.

- [ ] **Step 7: Commit atomic/security coverage**

```bash
git add tests/integration/test_runtime_dependencies.py tests/integration/test_repair_resume.py tests/integration/test_supervisor_pause_resume.py tests/regression/test_supervisor_security.py src/authorial_flow
git commit -m "test: lock supervisor atomic and security boundaries"
```

---

### Task 8: Documentation, Versioning, Migration, and Release Assertions

**Files:**
- Modify: `README.md`
- Modify: `docs/acceptance-matrix.md`
- Modify: `docs/migration-cutover.md`
- Modify: `docs/release-checklist.md`
- Create: `docs/2026-08-12-interactive-supervisor-review.md`
- Modify: `src/authorial_flow/version.py`
- Modify: `pyproject.toml`
- Modify: `tests/release/test_release_package.py`

**Interfaces:**
- Documents the exact owner interaction and the deterministic/live/owner evidence boundary.
- Bumps runtime version while preserving backward-compatible checkpoint fields and in-place `.state` reuse.

- [ ] **Step 1: Write failing release-documentation assertions**

Add a test that requires the exact behavior in the shipped release:

```python
def test_release_documents_interactive_same_terminal_supervisor():
    readme = (REPO / "README.md").read_text()
    checklist = (REPO / "docs" / "release-checklist.md").read_text()
    matrix = (REPO / "docs" / "acceptance-matrix.md").read_text()
    for token in [
        "Ctrl+C", "same terminal", "leave paused", "same thread",
        "discard", "Pangram task ID", "confirmed action",
    ]:
        assert token.lower() in readme.lower()
    assert "supervisor question" in matrix.lower()
    assert "target Zorin" in checklist
```

- [ ] **Step 2: Run the release assertion and verify RED**

```bash
python -m pytest -q tests/release/test_release_package.py::test_release_documents_interactive_same_terminal_supervisor
```

Expected: documentation tokens are absent.

- [ ] **Step 3: Update owner-facing docs without overstating live validation**

README must explain:

1. normal live events show complete proposals, guard reasons, accepted moves/current passage, repair, and Pangram state;
2. Ctrl+C cancels a child call or waits for an atomic checkpoint, then opens supervision in the same terminal;
3. free-form questions are read-only;
4. a proposed redirect/rollback/rejection/correction displays exact effects and requires confirmation;
5. `leave` keeps the thread paused and the next `./RUN.sh` reopens it;
6. no hidden chain-of-thought, raw prompts, transcripts, or credentials are shown.

Add acceptance-matrix rows for the 21 design criteria and distinguish deterministic coverage from the still-required real Zorin run. Migration docs must state that the new optional fields require no destructive database migration. Release checklist must require a real bad-looking Thought-Flow run, Ctrl+C, one supervisor question, one confirmed redirect, and same-thread continuation/pause before target approval.

- [ ] **Step 4: Bump the feature version**

Set:

```python
# src/authorial_flow/version.py
GRAPH_VERSION = "1.1.0-dev1"
```

and:

```toml
# pyproject.toml
version = "1.1.0.dev1"
```

Do not change the release archive root `authorial-flow-graph-v1`. Existing installations resume from `current-thread.json`; they do not recompute the preserved thread ID.

- [ ] **Step 5: Record exact deterministic evidence and pending live evidence**

The review document must identify:

- baseline commit and release SHA-256;
- implementation commit once available;
- exact test commands/counts;
- exact release ZIP filename/SHA-256 once built;
- project-instruction character count;
- target-machine Claude/Codex/Pangram/supervisor acceptance as pending until actually run;
- no claim that deterministic fakes prove terminal signal behavior on Zorin.

- [ ] **Step 6: Run GREEN and packaging unit regressions**

```bash
python -m pytest -q tests/release/test_release_package.py
python -c 'from pathlib import Path; p=Path("PASTE_INTO_PROJECT_INSTRUCTIONS.txt"); n=len(p.read_text()); print(n); raise SystemExit(n>8000)'
```

Expected: release tests pass and the instruction count is at most 8,000.

- [ ] **Step 7: Commit documentation/versioning**

```bash
git add README.md docs/acceptance-matrix.md docs/migration-cutover.md docs/release-checklist.md docs/2026-08-12-interactive-supervisor-review.md src/authorial_flow/version.py pyproject.toml tests/release/test_release_package.py
git commit -m "docs: specify interactive supervisor acceptance"
```

---

### Task 9: Full Verification, Exact ZIP, and Candidate Handoff

**Files:**
- Modify only if a verification failure reveals a defect in the implemented behavior.
- Generate outside the release root: `artifacts/authorial-flow-graph-v1-<commit8>-interactive-supervisor-release.zip`
- Update after successful verification: `docs/2026-08-12-interactive-supervisor-review.md`

**Interfaces:**
- Consumes the complete implementation and every prior test.
- Produces one deterministic candidate ZIP and an evidence-backed handoff; target approval remains separate.

- [ ] **Step 1: Run the complete deterministic suite from the implementation checkout**

```bash
python -m pytest -q
```

Expected: zero failures. A dependency-gated skip is acceptable only if it is the pre-existing LangGraph installation gate and is named in the review; in the installed execution environment, the real LangGraph/SQLite tests must run.

- [ ] **Step 2: Run source/privacy scans**

```bash
rg -n 'PANGRAM_API_KEY|BRAVE_SEARCH_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY' src tests
rg -n 'raw_prompt|raw_stdout|raw_stderr|chain.of.thought|hidden reasoning' src/authorial_flow
```

Expected: credential names occur only in intentional key handling/denylist/test code; no fixture value or path copies credentials, prompts, or provider transcripts into work-feed/snapshot/session payloads.

- [ ] **Step 3: Build the exact deterministic release ZIP**

```bash
commit8="$(git rev-parse --short=8 HEAD)"
python scripts/build_release.py \
  --repo . \
  --out "../artifacts/authorial-flow-graph-v1-${commit8}-interactive-supervisor-release.zip" \
  --clean-zip-compile
```

Expected terminal fields: `source_commit=...`, `graph_version=1.1.0-dev1`, `project_instructions_chars=<8001`, and `verification=PASS`.

- [ ] **Step 4: Verify the exact ZIP independently and test clean extraction**

```bash
commit8="$(git rev-parse --short=8 HEAD)"
zip_path="../artifacts/authorial-flow-graph-v1-${commit8}-interactive-supervisor-release.zip"
python -m authorial_flow.release verify "$zip_path" --clean-zip-compile
sha256sum "$zip_path"
tmp_root="$(mktemp -d)"
unzip -q "$zip_path" -d "$tmp_root"
"$tmp_root/authorial-flow-graph-v1/.venv/bin/python" -V 2>/dev/null || python3 -m compileall -q "$tmp_root/authorial-flow-graph-v1/src" "$tmp_root/authorial-flow-graph-v1/tests"
```

Expected: release verification and compile pass. Remove only the explicit `mktemp` directory after recording results.

- [ ] **Step 5: Re-run the supervisor-critical slices against the final checkout**

```bash
python -m pytest -q \
  tests/unit/test_pause.py \
  tests/unit/test_work_feed.py \
  tests/unit/test_supervisor.py \
  tests/integration/test_supervisor_pause_resume.py \
  tests/integration/test_live_work_feed.py \
  tests/integration/test_supervisor_actions.py \
  tests/integration/test_supervisor_cli.py \
  tests/regression/test_supervisor_security.py \
  tests/integration/test_runtime_dependencies.py \
  tests/integration/test_repair_resume.py \
  tests/release/test_release_package.py
```

Expected: zero failures.

- [ ] **Step 6: Complete the review record and commit only the recorded evidence change**

Insert the actual commands, counts, commit, ZIP filename, ZIP SHA-256, and instruction character count into `docs/2026-08-12-interactive-supervisor-review.md`. Keep all Zorin live fields explicitly `PENDING`.

```bash
git add docs/2026-08-12-interactive-supervisor-review.md
git commit -m "docs: record supervisor release verification"
```

Because this evidence commit changes the release contents and source commit, rebuild and reverify the ZIP once more after this commit; record the replacement filename/hash and do not deliver the pre-evidence ZIP.

- [ ] **Step 7: Prepare the target-machine acceptance command and expected evidence**

Use the existing one-command workflow from `~/Téléchargements`:

```bash
cd ~/Téléchargements/authorial-flow-graph-v1 && ./INSTALL-AND-RUN.sh
```

During a real Thought-Flow model call, Joel presses Ctrl+C, asks what the supervisor thinks is happening, confirms one bounded redirect, then either continues or types `leave`. The runtime itself must retain and report the thread ID, pause snapshot, confirmed action, and resumed/paused state; do not ask Joel to package routine logs manually.

Target approval requires:

- exact suite on extracted ZIP;
- live Claude and Codex smoke;
- zero-task Pangram auth probe;
- first real task ID checkpoint and returned version check;
- bad-looking run observed live;
- Ctrl+C supervisor question;
- one confirmed redirect;
- same-thread continuation or durable continued pause.

Until all are demonstrated, label the release `candidate, deterministic verification passed; target-machine supervisor acceptance pending`.

---

## Self-Review Coverage Matrix

| Approved criterion | Plan coverage |
| --- | --- |
| Child SIGINT terminates/discards partial output | Tasks 1, 7 |
| Resume reruns cancelled node without duplicate move | Task 4 |
| Pangram task ID checkpoint before pause/poll resume | Tasks 4, 7 |
| Repair promotion consistent before pause | Tasks 4, 7 |
| Ctrl+C inside supervisor cancels answer only | Task 6 |
| Exact proposal → guard → retry → accept chronology | Tasks 2, 5 |
| Current passage equals checkpoint moves | Task 5 |
| Contextual quiet heartbeats | Tasks 1, 2 |
| No incomplete output/raw prompts in feed | Tasks 1, 2, 7 |
| Repair/Pangram state visible without route changes | Tasks 5, 7 |
| Questions do not mutate checkpoints | Tasks 3, 6 |
| Proposed action waits for confirmation | Tasks 3, 6 |
| All action invalidation contracts | Tasks 3, 5 |
| Rollback coverage and legacy reconciliation | Tasks 3, 5 |
| General-rule candidate remains unpromoted | Task 3 |
| Malformed/stale actions fail closed | Tasks 3, 4, 7 |
| Leave/reopen restores thread/session | Tasks 3, 4, 6 |
| Secrets/prompts/transcripts absent | Tasks 2, 3, 7 |
| Existing owner/repair/Pangram regressions green | Tasks 4, 7, 9 |
| Exact ZIP deterministic and clean-extraction verified | Tasks 8, 9 |
| Real Zorin Ctrl+C → question → redirect → same thread | Task 9, explicitly pending until run |

## Plan Self-Review Results

- **Spec coverage:** all 21 acceptance criteria map to at least one failing regression and one implementation task.
- **Scope:** one coherent release subsystem; no browser dashboard, attachable supervisor, automatic action, global-rule auto-promotion, or gate weakening entered the plan.
- **Type consistency:** `SupervisorAction`, directive scopes, restart depths, pause modes, event kinds, state keys, and resume-node names use one spelling throughout.
- **Backward compatibility:** all state additions are optional; legacy per-move coverage fails closed into bounded reconciliation; `.state` and thread identity remain preserved.
- **Authority:** source/article/policy files stay P0 and immutable; meaning corrections are separate owner-grounded state.
- **Placeholder scan:** no `TBD`, `TODO`, “implement later,” or unassigned error-handling step remains.
- **Largest implementation risk:** LangGraph's interaction between a resumed invalid action and a second interrupt. Task 4 locks this with a real SQLite test before runtime/CLI integration proceeds.
