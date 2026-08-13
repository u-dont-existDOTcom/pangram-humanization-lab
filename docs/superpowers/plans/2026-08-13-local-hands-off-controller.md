# Local Hands-Off Controller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `./INSTALL-AND-RUN.sh` automatically verify trusted updates, install only when needed, run or resume the exact thread, repair machine failures, and continue without routine terminal commands.

**Architecture:** A standard-library-only `hands_off_controller` package is snapshotted under `.state` before it touches Git, so the updater cannot replace the code currently executing. The runtime writes a versioned atomic outcome record for every controlled child invocation; the persistent parent selects actions from that record rather than terminal text. Candidate updates and repairs run in detached worktrees and reach the installed checkout only after deterministic, protected-path, full-suite, and ancestry gates pass.

**Tech Stack:** Bash, Python 3.10+ standard library for bootstrap/control, existing Python 3.12 virtualenv on Zorin, pytest, local Git worktrees, existing LangGraph SQLite checkpoints, existing Claude/Codex CLI adapters, and the existing repair verification pipeline.

## Global Constraints

- `INSTALL-AND-RUN.sh` remains the single normal command and runs in the foreground.
- The stable update channel is exactly `install/authorial-flow-graph-v1` in the private repository `u-dont-existDOTcom/pangram-humanization-lab`.
- Only fast-forward history is accepted; never force-push, auto-merge, or trust another remote.
- `.state`, the current thread ID, SQLite checkpoints, pending Pangram task ownership, supervisor pauses, accepted moves, and owner directives survive updates.
- Project input, article text, policy, owner labels, learning records, and detector baselines are protected and may not be changed by update or repair control.
- The pre-virtualenv controller imports only Python 3.10 standard-library modules.
- Models may propose changes only in disposable worktrees and may not approve their own patches.
- One initial repair plus one correction is the maximum for one program commit and failure signature.
- Credentials, prompts, transcripts, raw provider output, environments, absolute home paths, and article text do not enter controller journals or Git diagnostics.
- Ctrl+C preserves the existing same-terminal supervisor and never discards a completed checkpoint.

---

### Task 1: Atomic typed child-outcome protocol

**Files:**
- Create: `src/hands_off_controller/__init__.py`
- Create: `src/hands_off_controller/protocol.py`
- Create: `tests/unit/test_controller_protocol.py`
- Modify: `src/authorial_flow/cli.py`
- Modify: `tests/integration/test_cli.py`

**Interfaces:**
- Consumes: `program_version(root: Path)`, existing runtime result dictionaries, `AUTHORIAL_CONTROLLER_RUN_ID`, and `AUTHORIAL_CONTROLLER_OUTCOME_PATH`.
- Produces: `OutcomeKind`, `ControllerOutcome`, `ControllerStop`, `write_outcome(path, outcome)`, `read_outcome(path, expected_run_id)`, `outcome_from_result(...)`, and the exit constants `EXIT_COMPLETED=0`, `EXIT_OWNER_PAUSE=20`, `EXIT_OWNER_DECISION=21`, `EXIT_CREDENTIAL=22`, `EXIT_ACCOUNT_ACTION=23`, `EXIT_MACHINE_RESTART=75`, `EXIT_BOUNDED_MACHINE_STOP=76`, and `EXIT_OWNER_INTERRUPT=130`.

- [ ] **Step 1: Write protocol tests that define exact serialization, stale-run rejection, and atomic replacement**

```python
def test_outcome_round_trip_rejects_another_run_id(tmp_path):
    path = tmp_path / "last-outcome.json"
    value = ControllerOutcome(
        run_id="run-1", kind=OutcomeKind.BOUNDED_MACHINE_STOP,
        exit_code=76, program_commit="abc", thread_id="thread-1",
        phase="generation", failure_signature="sig", failure_class="GENERATION_DEAD_END",
        origin_node="generation", evidence_ref="evidence", human_action="",
    )
    write_outcome(path, value)
    assert read_outcome(path, expected_run_id="run-1") == value
    with pytest.raises(OutcomeError, match="stale controller outcome"):
        read_outcome(path, expected_run_id="run-2")
    assert not list(tmp_path.glob("*.tmp"))
```

- [ ] **Step 2: Run the focused test and observe the missing-package failure**

Run: `.venv/bin/python -m pytest tests/unit/test_controller_protocol.py -q`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'hands_off_controller'`.

- [ ] **Step 3: Implement the standard-library protocol and strict field validation**

```python
OUTCOME_FORMAT = "authorial-flow-controller-outcome-v1"

class OutcomeKind(str, Enum):
    COMPLETED = "completed"
    OWNER_PAUSE = "owner_pause"
    OWNER_DECISION_REQUIRED = "owner_decision_required"
    CREDENTIAL_REQUIRED = "credential_required"
    ACCOUNT_ACTION_REQUIRED = "account_action_required"
    MACHINE_RESTART = "machine_restart"
    BOUNDED_MACHINE_STOP = "bounded_machine_stop"
    OWNER_INTERRUPT = "owner_interrupt"

@dataclass(frozen=True)
class ControllerOutcome:
    run_id: str
    kind: OutcomeKind
    exit_code: int
    program_commit: str
    thread_id: str
    phase: str = ""
    failure_signature: str = ""
    failure_class: str = ""
    origin_node: str = ""
    evidence_ref: str = ""
    human_action: str = ""

def write_outcome(path: Path, outcome: ControllerOutcome) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(outcome.to_payload(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
```

Limit all free strings to their documented lengths, require hexadecimal hashes where applicable, reject unknown keys, and keep `human_action` to an enum-like value such as `PANGRAM_API_KEY`, `PANGRAM_CREDITS`, or `AUTHORIAL_DECISION` rather than prose.

- [ ] **Step 4: Add result classification tests for accepted, supervisor pause, owner interrupt, promoted repair, and bounded stop**

```python
@pytest.mark.parametrize(
    ("result", "kind", "code"),
    [
        ({"status": "accepted"}, OutcomeKind.COMPLETED, 0),
        ({"status": "repair_promoted_restart_required"}, OutcomeKind.MACHINE_RESTART, 75),
        ({"status": "bounded_machine_stop", "failure_class": "PROVIDER_PLUMBING"}, OutcomeKind.BOUNDED_MACHINE_STOP, 76),
    ],
)
def test_outcome_from_result_maps_machine_states(result, kind, code):
    outcome = outcome_from_result(result, run_id="r", program_commit="p", thread_id="t")
    assert (outcome.kind, outcome.exit_code) == (kind, code)
```

- [ ] **Step 5: Make CLI controlled invocations write the record and return its exit code**

Add one shared finalizer instead of duplicating writes in `command_run`, `command_resume`, and `command_answer`:

```python
def _finish_controlled_command(config: RuntimeConfig, result: dict[str, Any], *, phase: str) -> int:
    _publish_runtime_result(config, phase=phase, result=result)
    run_id = os.environ.get("AUTHORIAL_CONTROLLER_RUN_ID", "").strip()
    if not run_id:
        _print_result(result)
        maybe_restart_after_repair(config, result)
        return 0
    current = _read_thread(config)
    outcome = outcome_from_result(
        result, run_id=run_id, program_commit=program_version(config.root),
        thread_id=str(current.get("thread_id") or ""), phase=phase,
    )
    write_outcome(Path(os.environ["AUTHORIAL_CONTROLLER_OUTCOME_PATH"]), outcome)
    _print_result(result)
    return outcome.exit_code
```

When controlled, `repair_promoted_restart_required` writes `machine_restart` and returns 75 instead of calling `os.execv`. Direct legacy use retains the existing same-process restart behavior.

- [ ] **Step 6: Add typed human-stop exceptions without scraping messages**

```python
class ControllerStop(RuntimeError):
    def __init__(self, kind: OutcomeKind, human_action: str, exit_code: int):
        super().__init__(human_action)
        self.kind = kind
        self.human_action = human_action
        self.exit_code = exit_code
```

Use `ControllerStop(OutcomeKind.CREDENTIAL_REQUIRED, "PANGRAM_API_KEY", 22)` for noninteractive missing credentials. Catch it in `main`, write a controlled outcome when a run ID exists, and print only the named action.

- [ ] **Step 7: Run the focused and CLI integration suites**

Run: `.venv/bin/python -m pytest tests/unit/test_controller_protocol.py tests/integration/test_cli.py -q`

Expected: PASS, including a test proving a controlled bounded stop returns 76 while direct `authorial-flow resume` remains backward-compatible.

- [ ] **Step 8: Commit the protocol slice**

```bash
git add src/hands_off_controller src/authorial_flow/cli.py tests/unit/test_controller_protocol.py tests/integration/test_cli.py
git commit -m "feat: add typed controller outcomes"
```

---

### Task 2: Controller state, journal, and exclusive ownership

**Files:**
- Create: `src/hands_off_controller/state.py`
- Create: `tests/unit/test_controller_state.py`

**Interfaces:**
- Consumes: project root and injected process probes for tests.
- Produces: `ControllerPaths.from_root(root)`, `atomic_json_write(path, payload)`, `append_journal(paths, event, payload)`, `ControllerLock.acquire()`, `ControllerLock.release()`, `RepairLedger.start(signature_key)`, and `LastKnownGood` persistence.

- [ ] **Step 1: Write failing tests for live lock refusal and stale lock reclamation**

```python
def test_live_controller_lock_refuses_second_owner(tmp_path):
    probes = FakeProbes(boot_id="boot", live={(55, "100")})
    first = ControllerLock(ControllerPaths.from_root(tmp_path), probes=probes, pid=55, process_start="100")
    first.acquire()
    with pytest.raises(ControllerBusy, match="pid=55"):
        ControllerLock(ControllerPaths.from_root(tmp_path), probes=probes, pid=77, process_start="200").acquire()

def test_dead_or_reused_pid_lock_is_reclaimed(tmp_path):
    paths = ControllerPaths.from_root(tmp_path)
    atomic_json_write(paths.lock, {"format": LOCK_FORMAT, "pid": 55, "boot_id": "old", "process_start": "100"})
    lock = ControllerLock(paths, probes=FakeProbes(boot_id="new", live=set()), pid=77, process_start="200")
    lock.acquire()
    assert json.loads(paths.lock.read_text())["pid"] == 77
```

- [ ] **Step 2: Run the state test and observe the missing-module failure**

Run: `.venv/bin/python -m pytest tests/unit/test_controller_state.py -q`

Expected: FAIL importing `hands_off_controller.state`.

- [ ] **Step 3: Implement exact path ownership and Linux process identity checks**

```python
@dataclass(frozen=True)
class ControllerPaths:
    root: Path
    controller: Path
    lock: Path
    outcome: Path
    journal: Path
    repair_ledger: Path
    last_known_good: Path
    bootstrap: Path
    update_worktrees: Path
    migration_backups: Path

    @classmethod
    def from_root(cls, root: Path) -> "ControllerPaths":
        controller = root.resolve() / ".state" / "controller"
        return cls(root.resolve(), controller, controller / "lock.json", controller / "last-outcome.json",
                   controller / "journal.jsonl", controller / "repair-ledger.json",
                   controller / "last-known-good.json", controller / "bootstrap",
                   controller / "update-worktrees", controller / "migration-backups")
```

Read boot identity from `/proc/sys/kernel/random/boot_id` and process start ticks from field 22 of `/proc/<pid>/stat`. Reclaim only if boot identity differs, the process does not exist, or the exact process-start token differs. The lock file is created with `os.open(..., O_CREAT | O_EXCL, 0o600)`.

- [ ] **Step 4: Write repair-ledger tests for the one-repair-plus-one-correction budget**

```python
def test_repair_ledger_is_keyed_by_program_and_failure(tmp_path):
    ledger = RepairLedger(ControllerPaths.from_root(tmp_path))
    key = ledger.key(program_commit="abc", failure_signature="sig")
    assert ledger.start(key).attempt == 1
    assert ledger.start(key).attempt == 2
    with pytest.raises(RepairBudgetExhausted):
        ledger.start(key)
    assert ledger.start(ledger.key(program_commit="def", failure_signature="sig")).attempt == 1
```

- [ ] **Step 5: Implement content-free journals and bounded backups metadata**

Journal payloads accept only keys in a constant allowlist and reject strings longer than 512 characters. `RepairLedger` stores signatures, counts, dispositions, program commits, and evidence hashes; it never stores stack text or subprocess output.

- [ ] **Step 6: Run the state suite**

Run: `.venv/bin/python -m pytest tests/unit/test_controller_state.py -q`

Expected: PASS.

- [ ] **Step 7: Commit controller state ownership**

```bash
git add src/hands_off_controller/state.py tests/unit/test_controller_state.py
git commit -m "feat: add controller state ownership"
```

---

### Task 3: Immutable pre-virtualenv snapshot and split installer gates

**Files:**
- Create: `scripts/controller_entry.py`
- Create: `scripts/install_runtime.sh`
- Create: `tests/integration/test_controller_entry.py`
- Modify: `INSTALL-AND-RUN.sh`
- Modify: `tests/release/test_release_package.py`

**Interfaces:**
- Consumes: `src/hands_off_controller/`, `python3`, installer arguments, and `.state/controller/bootstrap/`.
- Produces: an immutable package snapshot launched with `python3 -m hands_off_controller`, and `scripts/install_runtime.sh` modes `main` and `verify-candidate`.

- [ ] **Step 1: Write a failing snapshot immutability test**

```python
def test_entry_executes_snapshot_after_source_is_replaced(tmp_path, monkeypatch):
    root = make_minimal_controller_project(tmp_path, marker="old")
    calls = []
    monkeypatch.setattr(os, "execvpe", lambda exe, argv, env: calls.append((exe, argv, env)))
    snapshot = controller_entry.prepare_snapshot(root)
    (root / "src/hands_off_controller/__main__.py").write_text("MARKER='new'\n")
    assert (snapshot / "hands_off_controller/__main__.py").read_text() == "MARKER='old'\n"
    controller_entry.launch_snapshot(root, snapshot, [])
    assert calls[0][2]["PYTHONPATH"] == str(snapshot)
```

- [ ] **Step 2: Run the focused test and observe the missing entry module**

Run: `.venv/bin/python -m pytest tests/integration/test_controller_entry.py::test_entry_executes_snapshot_after_source_is_replaced -q`

Expected: FAIL because `scripts/controller_entry.py` is absent.

- [ ] **Step 3: Implement atomic package snapshotting keyed by exact source bytes**

```python
def package_digest(source: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(source.rglob("*.py")):
        digest.update(path.relative_to(source).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()

def prepare_snapshot(root: Path) -> Path:
    source = root / "src" / "hands_off_controller"
    target = root / ".state" / "controller" / "bootstrap" / package_digest(source)
    if not target.is_dir():
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        shutil.copytree(source, temporary / "hands_off_controller")
        os.replace(temporary, target)
    return target
```

Reject symlinks and any file other than regular `.py` files in the snapshot source.

- [ ] **Step 4: Move the existing installer body into a non-recursive gate script**

`INSTALL-AND-RUN.sh` becomes:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec python3 scripts/controller_entry.py "$@"
```

`scripts/install_runtime.sh` retains version checks, dependency resolution, hashed install, release-baseline reconciliation, repairable pytest preflight, and live smoke. It accepts `--mode main` or `--mode verify-candidate`. Candidate mode uses the caller-provided `AUTHORIAL_VENV_DIR`, runs direct pytest without autonomous mutation, skips live network smoke, and never launches `RUN.sh`.

- [ ] **Step 5: Add release tests proving both launchers are executable and recursive launch is impossible**

```python
def test_installer_wrapper_delegates_once_to_immutable_controller():
    text = Path("INSTALL-AND-RUN.sh").read_text()
    assert "controller_entry.py" in text
    assert "install_runtime.sh" not in text
    gate = Path("scripts/install_runtime.sh").read_text()
    assert "INSTALL-AND-RUN.sh" not in gate
    assert "exec ./RUN.sh" not in gate
```

- [ ] **Step 6: Run entry and release tests**

Run: `.venv/bin/python -m pytest tests/integration/test_controller_entry.py tests/release/test_release_package.py -q`

Expected: PASS.

- [ ] **Step 7: Commit the immutable entry layer**

```bash
git add INSTALL-AND-RUN.sh scripts/controller_entry.py scripts/install_runtime.sh tests/integration/test_controller_entry.py tests/release/test_release_package.py
git commit -m "feat: snapshot the hands-off bootstrap"
```

---

### Task 4: Trusted fast-forward update staging and migration safety

**Files:**
- Create: `src/hands_off_controller/update.py`
- Create: `src/hands_off_controller/install.py`
- Create: `scripts/migrate_state.py`
- Create: `tests/integration/test_controller_update.py`

**Interfaces:**
- Consumes: `ControllerPaths`, exact remote identity, exact stable branch, a `CommandRunner`, and the candidate gate script from Task 3.
- Produces: `RemoteTrust`, `UpdateCandidate`, `UpdateResult`, `TrustedUpdater.check()`, `TrustedUpdater.verify(candidate)`, `TrustedUpdater.promote(candidate)`, `StateBackup.create()`, and `StateBackup.restore_before_progress()`.

- [ ] **Step 1: Write local-bare-repository tests for fast-forward acceptance and divergent-history rejection**

```python
def test_fast_forward_candidate_is_verified_before_installed_head_moves(tmp_path):
    repo, remote, old, new = make_update_fixture(tmp_path)
    verifier = RecordingVerifier(pass_=True)
    updater = TrustedUpdater(repo, ControllerPaths.from_root(repo), TEST_TRUST, verifier=verifier)
    candidate = updater.check()
    assert candidate.commit == new
    assert git(repo, "rev-parse", "HEAD") == old
    result = updater.promote(updater.verify(candidate))
    assert result.status == "promoted"
    assert git(repo, "rev-parse", "HEAD") == new
    assert verifier.saw_head == new

def test_non_fast_forward_remote_is_rejected_without_checkout_change(tmp_path):
    repo, remote, installed = make_diverged_fixture(tmp_path)
    with pytest.raises(UpdateRejected, match="non-fast-forward"):
        TrustedUpdater(repo, ControllerPaths.from_root(repo), TEST_TRUST).check()
    assert git(repo, "rev-parse", "HEAD") == installed
```

- [ ] **Step 2: Run the update test and observe the absent updater**

Run: `.venv/bin/python -m pytest tests/integration/test_controller_update.py -q`

Expected: FAIL importing `hands_off_controller.update`.

- [ ] **Step 3: Implement normalized remote trust and narrow fetch**

```python
@dataclass(frozen=True)
class RemoteTrust:
    repository: str = "u-dont-existDOTcom/pangram-humanization-lab"
    remote_name: str = "origin"
    branch: str = "install/authorial-flow-graph-v1"

def normalize_remote(url: str) -> str:
    value = url.strip().removesuffix(".git")
    for prefix in ("https://github.com/", "ssh://git@github.com/", "git@github.com:"):
        if value.startswith(prefix):
            return value[len(prefix):]
    raise UpdateRejected("untrusted remote URL")
```

Fetch only `+refs/heads/<stable>:refs/remotes/<remote>/<stable>` into the configured remote-tracking ref, then require `git merge-base --is-ancestor HEAD <remote-ref>`. If the stable branch does not exist during first rollout, fail closed; branch creation is a release action, not a local inference.

- [ ] **Step 4: Stage candidates in detached worktrees and run the exact candidate gate**

```python
class CandidateVerifier:
    def verify(self, candidate: UpdateCandidate) -> VerificationReceipt:
        venv = candidate.path / ".controller-verify-venv"
        env = {**os.environ, "AUTHORIAL_VENV_DIR": str(venv), "AUTHORIAL_SKIP_LIVE_SMOKE": "1"}
        commands = [
            ["bash", "scripts/install_runtime.sh", "--mode", "verify-candidate"],
            [str(venv / "bin/python"), "scripts/migrate_state.py", "--state-dir", str(candidate.state_copy), "--check"],
            [str(venv / "bin/python"), "scripts/build_release.py", "--out", str(candidate.release_zip), "--clean-zip-compile"],
        ]
        return run_all(candidate.path, commands, env=env)
```

The candidate state copy excludes artifacts, evidence ZIPs, diagnostics temporary worktrees, and secrets; it includes controller metadata plus SQLite databases using SQLite’s backup API. The migration command validates schema and may modify only the disposable copy.

- [ ] **Step 5: Add tests for bad manifest, failed suite, failed migration, and untouched live state**

```python
@pytest.mark.parametrize("failure", ["manifest", "tests", "migration"])
def test_candidate_gate_failure_preserves_head_and_live_state(tmp_path, failure):
    repo, _, old, _ = make_update_fixture(tmp_path)
    checkpoint = repo / ".state/checkpoints.sqlite"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"live-state")
    updater = TrustedUpdater(repo, ControllerPaths.from_root(repo), TEST_TRUST,
                             verifier=FailingVerifier(failure))
    with pytest.raises(UpdateRejected, match=failure):
        updater.verify(updater.check())
    assert git(repo, "rev-parse", "HEAD") == old
    assert checkpoint.read_bytes() == b"live-state"
```

- [ ] **Step 6: Implement pre-progress backup and fast-forward promotion**

Before `git merge --ff-only`, store `last-known-good.json` with installed commit, candidate commit, manifest hash, and backup ID. After promotion, mark `progress_committed=false`. Only state-migration failure before runtime progress may call `restore_before_progress`; once the child reports any new checkpoint/event sequence, set `progress_committed=true` and require repair-forward recovery.

- [ ] **Step 7: Run updater integration tests**

Run: `.venv/bin/python -m pytest tests/integration/test_controller_update.py -q`

Expected: PASS using only local repositories and no network.

- [ ] **Step 8: Commit trusted update staging**

```bash
git add src/hands_off_controller/update.py src/hands_off_controller/install.py scripts/migrate_state.py tests/integration/test_controller_update.py
git commit -m "feat: verify trusted updates before promotion"
```

---

### Task 5: Persistent foreground supervisor loop

**Files:**
- Create: `src/hands_off_controller/loop.py`
- Create: `src/hands_off_controller/__main__.py`
- Create: `tests/unit/test_controller_loop.py`
- Modify: `RUN.sh`

**Interfaces:**
- Consumes: `TrustedUpdater`, `ControllerLock`, typed outcomes, `.venv/bin/authorial-flow`, and the current-thread marker.
- Produces: `ControllerAction`, `select_action(outcome)`, `ChildInvocation`, `run_child(invocation)`, `HandsOffController.run()`, and CLI subcommands `run`, `status`, and `once` for tests.

- [ ] **Step 1: Write the action-table test before implementing the loop**

```python
@pytest.mark.parametrize(
    ("kind", "action"),
    [
        (OutcomeKind.COMPLETED, ControllerAction.EXIT_SUCCESS),
        (OutcomeKind.OWNER_PAUSE, ControllerAction.EXIT_PAUSED),
        (OutcomeKind.OWNER_DECISION_REQUIRED, ControllerAction.HUMAN_STOP),
        (OutcomeKind.CREDENTIAL_REQUIRED, ControllerAction.HUMAN_STOP),
        (OutcomeKind.ACCOUNT_ACTION_REQUIRED, ControllerAction.HUMAN_STOP),
        (OutcomeKind.MACHINE_RESTART, ControllerAction.RESUME),
        (OutcomeKind.BOUNDED_MACHINE_STOP, ControllerAction.REPAIR),
        (OutcomeKind.OWNER_INTERRUPT, ControllerAction.EXIT_PAUSED),
    ],
)
def test_typed_outcome_selects_action(kind, action):
    assert select_action(outcome(kind)) is action
```

- [ ] **Step 2: Run the loop unit test and observe the missing module**

Run: `.venv/bin/python -m pytest tests/unit/test_controller_loop.py -q`

Expected: FAIL importing `hands_off_controller.loop`.

- [ ] **Step 3: Implement child invocation without stdout parsing**

```python
@dataclass(frozen=True)
class ChildInvocation:
    argv: tuple[str, ...]
    run_id: str
    outcome_path: Path

def run_child(invocation: ChildInvocation, *, root: Path) -> ControllerOutcome:
    invocation.outcome_path.unlink(missing_ok=True)
    env = dict(os.environ)
    env["AUTHORIAL_CONTROLLER_RUN_ID"] = invocation.run_id
    env["AUTHORIAL_CONTROLLER_OUTCOME_PATH"] = str(invocation.outcome_path)
    result = subprocess.run(list(invocation.argv), cwd=root, env=env)
    outcome = read_outcome(invocation.outcome_path, expected_run_id=invocation.run_id)
    if result.returncode != outcome.exit_code:
        raise OutcomeError("child exit and outcome record disagree")
    return outcome
```

While the child owns the terminal, the parent defers SIGINT handling so the runtime’s existing pause controller receives it. Parent cleanup resumes only after the child returns.

- [ ] **Step 4: Test automatic same-thread resume after a program restart**

```python
def test_machine_restart_reloads_then_resumes_same_thread(tmp_path):
    runner = ScriptedChildRunner([outcome(OutcomeKind.MACHINE_RESTART), outcome(OutcomeKind.COMPLETED)])
    controller = HandsOffController(root=tmp_path, updater=NoUpdate(), child_runner=runner,
                                    repair_runner=NeverRepair())
    assert controller.run() == 0
    assert runner.commands == ["resume", "resume"]
    assert runner.thread_ids == ["thread-1", "thread-1"]
```

- [ ] **Step 5: Implement startup order and conditional installation**

The loop acquires the lock, publishes queued diagnostics best-effort when the venv exists, checks the stable branch, verifies/promotes a candidate, runs `scripts/install_runtime.sh --mode main` only if `.venv` is absent or accepted program/dependency hashes changed, and then invokes `run` when no current-thread marker exists or `resume` when it does.

Installer return 3 becomes a typed `credential_required/PANGRAM_API_KEY` stop and return 4 becomes `account_action_required/PANGRAM_CREDITS`. Other nonzero installer results enter outer repair with phase `controller-install`; the parent does not classify them from printed messages.

- [ ] **Step 6: Preserve manual `RUN.sh` commands while routing the normal no-argument path through the controller**

```bash
if [ "$#" -eq 0 ]; then
  exec python3 scripts/controller_entry.py
fi
case "$1" in
  run|resume|status|answer|package|publish-results) exec .venv/bin/authorial-flow "$@" ;;
  *) exec .venv/bin/authorial-flow run "$@" ;;
esac
```

`INSTALL-AND-RUN.sh` and no-argument `RUN.sh` are therefore equivalent one-command entry points; explicit diagnostic and supervisor commands remain available.

- [ ] **Step 7: Run loop and CLI integration tests**

Run: `.venv/bin/python -m pytest tests/unit/test_controller_loop.py tests/integration/test_cli.py tests/integration/test_supervisor_cli.py tests/integration/test_supervisor_pause_resume.py -q`

Expected: PASS, including same-thread and leave-paused cases.

- [ ] **Step 8: Commit the persistent loop**

```bash
git add src/hands_off_controller/loop.py src/hands_off_controller/__main__.py tests/unit/test_controller_loop.py RUN.sh
git commit -m "feat: keep the runtime under persistent supervision"
```

---

### Task 6: Outer-controller repair and race-safe stable-branch publication

**Files:**
- Create: `src/authorial_flow/controller_repair.py`
- Create: `tests/integration/test_controller_repair.py`
- Modify: `src/hands_off_controller/loop.py`
- Modify: `src/authorial_flow/bootstrap_repair.py`
- Modify: `tests/integration/test_bootstrap_repair.py`

**Interfaces:**
- Consumes: a bounded-machine outcome or `OutcomeError`, existing `RuntimeServices`, `_production_repair_cycle`, `RepairLedger`, and stable remote trust.
- Produces: `ControllerFailureEvidence`, `build_controller_failure_evidence(...)`, `run_controller_repair(...)`, and `publish_verified_repair(...)`.

- [ ] **Step 1: Write a failing test proving malformed outcome enters repair without user log collection**

```python
def test_missing_child_outcome_enters_outer_repair(tmp_path):
    repairs = RecordingRepairRunner(result=RepairResult.RESTART)
    controller = HandsOffController(root=tmp_path, updater=NoUpdate(),
                                    child_runner=MissingOutcomeRunner(), repair_runner=repairs)
    controller.run_once()
    assert repairs.calls[0].failure_class == "CONTROLLER_PROTOCOL"
    assert repairs.calls[0].origin_node == "controller-child-outcome"
    assert repairs.calls[0].raw_stdout == ""
```

- [ ] **Step 2: Run focused repair tests and observe the absent repair entry point**

Run: `.venv/bin/python -m pytest tests/integration/test_controller_repair.py -q`

Expected: FAIL importing `authorial_flow.controller_repair`.

- [ ] **Step 3: Build controller evidence as an artifact, not terminal prose**

```python
@dataclass(frozen=True)
class ControllerFailureEvidence:
    failure_class: str
    origin_node: str
    program_commit: str
    thread_id: str
    failure_signature: str
    child_exit: int
    outcome_error: str
    evidence_ref: str
```

Hash the normalized exception type, origin, program commit, child exit, and repository-relative traceback frames. Store detailed local evidence through `ArtifactStore`; pass only its hash into the content-free controller journal.

- [ ] **Step 4: Reuse the production repair cycle with a controller-owned acceptance command**

Build the repair state with `task_mode="P0"`, `source_provenance="CONTROLLER_FAILURE"`, `authorial_information_missing=False`, and an acceptance command that reruns the exact new regression plus `.venv/bin/python -m pytest -q`. The repair must still demonstrate RED/GREEN, pass independent plan and diff review, validate protected snapshots, and use at most one correction.

- [ ] **Step 5: Add local-bare-remote tests for normal push and concurrent remote advance**

```python
def test_verified_repair_pushes_only_when_remote_still_equals_base(tmp_path):
    repo, remote, base, repair = make_repair_remote(tmp_path)
    assert publish_verified_repair(repo, TEST_TRUST, base_commit=base, repair_commit=repair) == "published"
    assert ls_remote(remote, TEST_TRUST.branch) == repair

def test_concurrent_remote_advance_blocks_stale_repair_without_force(tmp_path):
    repo, remote, base, repair = make_repair_remote(tmp_path)
    advance_remote(remote, parent=base)
    assert publish_verified_repair(repo, TEST_TRUST, base_commit=base, repair_commit=repair) == "remote_advanced"
    assert "--force" not in recorded_git_argv()
```

- [ ] **Step 6: Implement race-safe publication and retry-newer-update behavior**

Fetch the stable ref, require it to equal the repair base, and use plain `git push origin <repair>:refs/heads/install/authorial-flow-graph-v1`. If the remote changed, mark the local repair stale, run the updater against the newer remote head, and retry the same thread on the verified newer program before spending another repair attempt.

- [ ] **Step 7: Wire bounded repair dispositions into the persistent loop**

`APPLIED_VERIFIED` returns `RESUME`; `remote_advanced` returns `CHECK_UPDATE`; `STAGED_FOR_OWNER` becomes a typed owner-decision stop only when the evidence says authorial information is missing; all machine-only exhaustion becomes `WAIT_REMOTE_REPAIR` for the second implementation plan.

- [ ] **Step 8: Run repair, protection, and same-thread suites**

Run: `.venv/bin/python -m pytest tests/integration/test_controller_repair.py tests/integration/test_bootstrap_repair.py tests/integration/test_repair_resume.py tests/repair -q`

Expected: PASS.

- [ ] **Step 9: Commit outer repair**

```bash
git add src/authorial_flow/controller_repair.py src/hands_off_controller/loop.py src/authorial_flow/bootstrap_repair.py tests/integration/test_controller_repair.py tests/integration/test_bootstrap_repair.py
git commit -m "feat: repair failures outside the graph"
```

---

### Task 7: Backoff, typed human stops, and end-to-end controller simulation

**Files:**
- Create: `tests/integration/test_hands_off_controller_e2e.py`
- Modify: `src/hands_off_controller/loop.py`
- Modify: `src/hands_off_controller/state.py`
- Modify: `README.md`
- Modify: `docs/migration-cutover.md`
- Modify: `docs/release-checklist.md`

**Interfaces:**
- Consumes: the full local controller and fake clock/network/child/repair components.
- Produces: `BackoffState`, material-change reset logic, concise phase output, and the documented one-command operational contract.

- [ ] **Step 1: Write the end-to-end failure-update-resume test**

```python
def test_one_command_survives_failure_remote_fix_and_same_thread_resume(tmp_path):
    scenario = ControllerScenario(tmp_path, thread_id="thread-1")
    scenario.child_outcomes = [bounded("sig-1"), completed()]
    scenario.repair_results = [remote_advanced_with_verified_commit("new-program")]
    result = scenario.controller.run()
    assert result == 0
    assert scenario.commands == ["resume", "resume"]
    assert scenario.thread_ids == ["thread-1", "thread-1"]
    assert scenario.manual_commands == []
```

- [ ] **Step 2: Add deterministic backoff tests**

```python
def test_backoff_resets_only_on_material_change():
    state = BackoffState()
    assert state.next_delay(fingerprint="same") == 5
    assert state.next_delay(fingerprint="same") == 15
    assert state.next_delay(fingerprint="same") == 60
    assert state.next_delay(fingerprint="new-head") == 5
```

Use the bounded sequence 5, 15, 60, 300, 900 seconds. Display the next attempt time. Ctrl+C during waiting exits safely while preserving the current checkpoint and backoff state.

`WAIT_REMOTE_REPAIR` is an active controller state: after each delay it republishes queued records, fetches the stable branch, and immediately verifies/resumes on a new commit. An unchanged head and failure signature spend no model call and do not ask Joel to say “check results.”

- [ ] **Step 3: Test that human stops never invoke repair**

```python
@pytest.mark.parametrize("kind", [OutcomeKind.CREDENTIAL_REQUIRED, OutcomeKind.ACCOUNT_ACTION_REQUIRED,
                                  OutcomeKind.OWNER_DECISION_REQUIRED, OutcomeKind.OWNER_PAUSE])
def test_human_boundary_never_invokes_repair(tmp_path, kind):
    repairs = NeverRepair()
    result = ControllerScenario(tmp_path, child_outcomes=[outcome(kind)], repair_runner=repairs).controller.run()
    assert repairs.calls == []
    assert result in {20, 21, 22, 23}
```

- [ ] **Step 4: Implement concise phase rendering and material-change fingerprints**

Fingerprints include remote head, program commit, failure signature, network reachability class, and named credential/account state. Do not include exception messages or paths.

- [ ] **Step 5: Update operator documentation**

Document that the only normal command is:

```bash
cd ~/Téléchargements/authorial-flow-graph-v1
./INSTALL-AND-RUN.sh
```

Explain the typed stops, stable branch, last-known-good record, and `./RUN.sh status`. Remove instructions that tell Joel to run `git pull`, `publish-results`, or relay logs as a normal recovery step.

- [ ] **Step 6: Run the full local-controller integration selection**

Run: `.venv/bin/python -m pytest tests/unit/test_controller_protocol.py tests/unit/test_controller_state.py tests/unit/test_controller_loop.py tests/integration/test_controller_entry.py tests/integration/test_controller_update.py tests/integration/test_controller_repair.py tests/integration/test_hands_off_controller_e2e.py -q`

Expected: PASS.

- [ ] **Step 7: Commit end-to-end control and documentation**

```bash
git add src/hands_off_controller tests/integration/test_hands_off_controller_e2e.py README.md docs/migration-cutover.md docs/release-checklist.md
git commit -m "feat: complete the one-command recovery loop"
```

---

### Task 8: Release metadata, clean extraction, and stable-channel rollout

**Files:**
- Modify: `src/authorial_flow/version.py`
- Modify: `pyproject.toml`
- Modify: `tests/unit/test_release_guardrails.py`
- Modify: `MANIFEST.json`
- Modify: `SHA256SUMS.txt`
- Create: `docs/2026-08-13-local-hands-off-controller-review.md`

**Interfaces:**
- Consumes: all prior tasks and existing deterministic release tooling.
- Produces: a verified release commit, stable install ref, compatibility versioned install ref, and target-machine bootstrap acceptance instructions.

- [ ] **Step 1: Add release guardrails for every controller asset**

```python
def test_hands_off_controller_release_members_are_present():
    required = [
        Path("src/hands_off_controller/protocol.py"),
        Path("src/hands_off_controller/state.py"),
        Path("src/hands_off_controller/update.py"),
        Path("src/hands_off_controller/install.py"),
        Path("src/hands_off_controller/loop.py"),
        Path("src/hands_off_controller/__main__.py"),
        Path("scripts/controller_entry.py"),
        Path("scripts/install_runtime.sh"),
        Path("scripts/migrate_state.py"),
    ]
    assert all(path.is_file() for path in required)
```

- [ ] **Step 2: Run the new guardrail before version metadata changes**

Run: `.venv/bin/python -m pytest tests/unit/test_release_guardrails.py -q`

Expected: PASS for assets and FAIL only if the graph-version expectation still names the prior version.

- [ ] **Step 3: Advance the development version consistently**

Set `GRAPH_VERSION` and `pyproject.toml` to the same next development release, update the exact version expectation, and document the compatibility boundary. Do not change policy or project manifests.

- [ ] **Step 4: Run compile, focused suites, and full deterministic suite**

Run: `.venv/bin/python -m compileall -q src tests`

Run: `.venv/bin/python -m pytest tests/unit tests/regression -q`

Run: `.venv/bin/python -m pytest tests/integration tests/repair tests/release -q`

Run: `.venv/bin/python -m pytest -q`

Expected: every command exits 0.

- [ ] **Step 5: Build from a clean extraction and verify launchers**

Run: `.venv/bin/python scripts/build_release.py --out /tmp/authorial-flow-hands-off.zip --clean-zip-compile`

Expected: `verification=PASS`, with both launchers executable and no `.state`, `.venv`, worktree, result, or evidence files in the ZIP.

- [ ] **Step 6: Write root release metadata and commit it separately**

Run: `.venv/bin/python scripts/build_release.py --write-root-metadata`

Run: `git add MANIFEST.json SHA256SUMS.txt && git commit -m "release: finalize hands-off controller metadata"`

Expected: the metadata source commit points to the last non-metadata release commit.

- [ ] **Step 7: Rebuild and byte-compare root metadata with the ZIP**

Run: `.venv/bin/python scripts/build_release.py --out /tmp/authorial-flow-hands-off-final.zip --clean-zip-compile`

Extract `MANIFEST.json` and `SHA256SUMS.txt` from the ZIP and compare each byte-for-byte with the root files. Expected: both comparisons match.

- [ ] **Step 8: Record exact verification evidence**

Write `docs/2026-08-13-local-hands-off-controller-review.md` with commits, test counts, release SHA-256, protected-path hashes, and remaining target-machine acceptance. Commit it with:

```bash
git add docs/2026-08-13-local-hands-off-controller-review.md
git commit -m "docs: record hands-off controller verification"
```

- [ ] **Step 9: Publish without force**

Create or fast-forward `install/authorial-flow-graph-v1` to the verified commit. Fast-forward the existing versioned install branch to the same commit for the one-time migration. Update the current development PR. Any remote-parent mismatch aborts publication.

- [ ] **Step 10: Perform the one final Zorin bootstrap acceptance**

Joel runs exactly:

```bash
cd ~/Téléchargements/authorial-flow-graph-v1 &&
git pull --ff-only origin install/authorial-flow-graph-v1-1.3.0-dev1 &&
./INSTALL-AND-RUN.sh
```

This is the final branch-specific command. Acceptance requires a deliberate machine-path failure to publish diagnostics, repair or accept a newer stable commit, and resume the same thread without another command or “check results” message.
