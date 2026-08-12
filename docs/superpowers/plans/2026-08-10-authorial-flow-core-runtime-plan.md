# Authorial Flow Graph v1 — Core Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy harness/autopilot/supervisor execution path with one durable LangGraph runtime that can run Basic Thought-Flow end to end, persist checkpoints, expose heartbeat status, enforce hard regressions/fidelity gates, call Pangram only downstream, and pause/resume for owner judgment.

**Architecture:** Build the runtime bottom-up: deterministic storage/state/process primitives first; provider adapters second; hard regression and Basic Thought-Flow nodes third; graph/interrupt/CLI last. The writer never sees owner regression examples or the completed source paragraph in Basic Flow. SQLite checkpoints store compact references while raw provider payloads live in a content-addressed artifact store.

**Tech Stack:** Python 3.12 target (>=3.10 supported), `langgraph==1.2.9`, `langgraph-checkpoint-sqlite==3.1.0`, stdlib `sqlite3`, `httpx`, `pydantic>=2`, `pytest`, `pytest-timeout`.

## Global Constraints

- LangGraph is the sole live orchestration runtime; legacy supervisor/harness code is regression evidence only.
- `SqliteSaver` must be created with a safe serializer configuration; set `LANGGRAPH_STRICT_MSGPACK=true` in launcher/test environments.
- `thread_id` is content-addressed from protected inputs + policy/regression/program versions; changed protected input creates a new thread lineage.
- Billable/remote calls checkpoint a stable request identity before execution and reuse successful artifacts on replay.
- Owner flow regressions and semantic-relation regressions are hard gates; model-derived source-order positives are diagnostic only.
- Pangram is never called before hard local/editorial gates pass.
- First Pangram-Human candidate lineage is frozen; detector output never silently replaces the editorial winner.
- Normal operation never asks the user to upload logs/intermediate ZIPs and never prints an internal `UPLOAD THIS FILE` path.
- Owner labels/policy/source files are never writer exemplars and are read-only to repair agents.
- `PASTE_INTO_PROJECT_INSTRUCTIONS.txt` must be <8,000 characters; release tests fail at >=8,000.
- All local user commands/path examples use `~/Téléchargements`.

---

## File Map

- `pyproject.toml` — package metadata, dependency ranges, test extras, console entry point.
- `requirements.lock` — exact wheel/version lock generated from `pyproject.toml` and checked into release.
- `src/authorial_flow/state.py` — typed LangGraph state and reducers.
- `src/authorial_flow/config.py` — immutable runtime budgets/paths/version identity.
- `src/authorial_flow/artifacts.py` — content-addressed raw artifact store.
- `src/authorial_flow/events.py` — append-only event journal.
- `src/authorial_flow/secrets.py` — redaction and child-environment isolation.
- `src/authorial_flow/process_runner.py` — nonblocking subprocess runner + 10-second heartbeat.
- `src/authorial_flow/models/claude_cli.py` — Claude CLI structured call adapter.
- `src/authorial_flow/models/codex_cli.py` — Codex CLI schema-constrained adapter.
- `src/authorial_flow/models/pangram.py` — async task client with idempotent task reuse.
- `src/authorial_flow/policy.py` — policy snapshot discovery/hashing.
- `src/authorial_flow/nodes/regression.py` — owner/semantic hard startup suites + diagnostic positives.
- `src/authorial_flow/nodes/represent.py` — Basic Flow semantic representation with authority obligations.
- `src/authorial_flow/nodes/pressure.py` — candidate-blind dual-reader precommitment.
- `src/authorial_flow/nodes/generate.py` — one semantic move writer + atomicity split.
- `src/authorial_flow/nodes/flow.py` — entry/full edge and global organization gates.
- `src/authorial_flow/nodes/fidelity.py` — relation + semantic fidelity guards.
- `src/authorial_flow/nodes/stopping.py` — stop/rollback/disposition routing.
- `src/authorial_flow/nodes/cold_audit.py` — completed-output cold audit orchestration.
- `src/authorial_flow/nodes/revise.py` — bounded candidate revision from explicit cold-audit defects.
- `src/authorial_flow/candidates.py` — candidate snapshot/editorial freeze lineage.
- `src/authorial_flow/nodes/detector_search.py` — Pangram node + bounded detector-safe variants hook.
- `src/authorial_flow/nodes/owner_interrupt.py` — LangGraph `interrupt()` payload and resume validation.
- `src/authorial_flow/graph.py` — StateGraph assembly and SQLite compilation.
- `src/authorial_flow/cli.py` — run/resume/status command surface.
- `INSTALL-AND-RUN.sh`, `RUN.sh` — idempotent local entrypoints.
- `tests/unit/*`, `tests/regression/*`, `tests/integration/*` — deterministic evidence for every runtime guarantee.

---

### Task 1: Package Skeleton, Dependencies, and Release Guardrails

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.lock`
- Create: `.gitignore`
- Create: `src/authorial_flow/__init__.py`
- Create: `src/authorial_flow/version.py`
- Create: `PASTE_INTO_PROJECT_INSTRUCTIONS.txt`
- Create: `tests/unit/test_release_guardrails.py`

**Interfaces:**
- Produces: `authorial_flow.version.GRAPH_VERSION: str`
- Produces: `authorial-flow` console command mapped later to `authorial_flow.cli:main`.

- [ ] **Step 1: Write failing release-guardrail tests**

```python
# tests/unit/test_release_guardrails.py
from pathlib import Path


def test_project_instructions_under_limit():
    text = Path("PASTE_INTO_PROJECT_INSTRUCTIONS.txt").read_text()
    assert 0 < len(text) < 8000


def test_project_instructions_do_not_inline_master():
    text = Path("PASTE_INTO_PROJECT_INSTRUCTIONS.txt").read_text()
    assert "# INSTRUCTIONS FOR WRITING/EDITING JOEL'S ARTICLES" not in text


def test_graph_version_is_explicit():
    from authorial_flow.version import GRAPH_VERSION
    assert GRAPH_VERSION == "1.0.0-dev1"
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python3 -m pytest tests/unit/test_release_guardrails.py -q`

Expected: FAIL because package/release files do not yet exist.

- [ ] **Step 3: Create the package metadata and version**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=75", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "authorial-flow-graph"
version = "1.0.0.dev1"
requires-python = ">=3.10"
dependencies = [
  "langgraph==1.2.9",
  "langgraph-checkpoint-sqlite==3.1.0",
  "httpx>=0.28,<0.29",
  "pydantic>=2.11,<3",
]

[project.optional-dependencies]
test = ["pytest>=8.4,<9", "pytest-timeout>=2.4,<3"]

[project.scripts]
authorial-flow = "authorial_flow.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
addopts = "-ra"
testpaths = ["tests"]
```

```python
# src/authorial_flow/version.py
GRAPH_VERSION = "1.0.0-dev1"
```

Create `PASTE_INTO_PROJECT_INSTRUCTIONS.txt` as a compact routing summary that tells ChatGPT to read the full policy snapshot from Project Sources rather than duplicating it.

- [ ] **Step 4: Create `.gitignore`**

```gitignore
.venv/
.state/
__pycache__/
.pytest_cache/
*.pyc
*.egg-info/
dist/
build/
```

- [ ] **Step 5: Generate an exact lock file in a disposable venv**

Run:

```bash
python3 -m venv .plan-lock-venv
.plan-lock-venv/bin/python -m pip install -U pip
.plan-lock-venv/bin/pip install -e '.[test]'
.plan-lock-venv/bin/pip freeze --exclude-editable > requirements.lock
rm -rf .plan-lock-venv
```

Expected: `requirements.lock` contains exact installed versions including LangGraph 1.2.9 and SQLite checkpointer 3.1.0.

- [ ] **Step 6: Run guardrail tests**

Run: `python3 -m pytest tests/unit/test_release_guardrails.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml requirements.lock .gitignore PASTE_INTO_PROJECT_INSTRUCTIONS.txt src tests/unit/test_release_guardrails.py
git commit -m "build: scaffold authorial flow runtime"
```

---

### Task 2: Runtime Config, Typed State, Artifact Store, and Event Journal

**Files:**
- Create: `src/authorial_flow/config.py`
- Create: `src/authorial_flow/state.py`
- Create: `src/authorial_flow/artifacts.py`
- Create: `src/authorial_flow/events.py`
- Test: `tests/unit/test_state_storage.py`

**Interfaces:**
- Produces: `RuntimeConfig.from_root(root: Path) -> RuntimeConfig`
- Produces: `AuthorialState(TypedDict)` compact graph state.
- Produces: `ArtifactStore.put_bytes(data, ext, metadata) -> ArtifactRef`
- Produces: `EventJournal.append(kind, payload) -> int`

- [ ] **Step 1: Write failing storage tests**

```python
# tests/unit/test_state_storage.py
import json
from pathlib import Path
from authorial_flow.artifacts import ArtifactStore
from authorial_flow.events import EventJournal
from authorial_flow.config import RuntimeConfig


def test_artifact_store_is_content_addressed(tmp_path: Path):
    store = ArtifactStore(tmp_path / "artifacts")
    a = store.put_bytes(b"same", "txt", {"producer": "test"})
    b = store.put_bytes(b"same", "txt", {"producer": "test"})
    assert a.sha256 == b.sha256
    assert a.path == b.path
    assert a.path.read_bytes() == b"same"


def test_event_sequence_is_append_only(tmp_path: Path):
    journal = EventJournal(tmp_path / "events.jsonl")
    assert journal.append("node.start", {"node": "bootstrap"}) == 1
    assert journal.append("node.end", {"node": "bootstrap"}) == 2
    rows = [json.loads(x) for x in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert [r["sequence"] for r in rows] == [1, 2]


def test_runtime_config_uses_state_below_root(tmp_path: Path):
    cfg = RuntimeConfig.from_root(tmp_path)
    assert cfg.state_dir == tmp_path / ".state"
    assert cfg.heartbeat_seconds == 10
```

- [ ] **Step 2: Verify failure**

Run: `pytest tests/unit/test_state_storage.py -q`

Expected: import failures.

- [ ] **Step 3: Implement immutable runtime config**

```python
# src/authorial_flow/config.py
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class RuntimeConfig:
    root: Path
    state_dir: Path
    heartbeat_seconds: int = 10
    model_timeout_seconds: int = 1800
    pangram_timeout_seconds: int = 900
    writer_attempts: int = 4
    max_rollbacks: int = 8

    @classmethod
    def from_root(cls, root: Path) -> "RuntimeConfig":
        root = root.resolve()
        return cls(root=root, state_dir=root / ".state")
```

- [ ] **Step 4: Implement `ArtifactRef` and atomic content-addressed writes**

```python
# src/authorial_flow/artifacts.py
from dataclasses import dataclass
from hashlib import sha256
import json, os
from pathlib import Path

@dataclass(frozen=True)
class ArtifactRef:
    sha256: str
    path: Path
    metadata_path: Path

class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root

    def put_bytes(self, data: bytes, ext: str, metadata: dict) -> ArtifactRef:
        digest = sha256(data).hexdigest()
        bucket = self.root / digest[:2]
        bucket.mkdir(parents=True, exist_ok=True)
        path = bucket / f"{digest}.{ext.lstrip('.')}"
        meta = bucket / f"{digest}.meta.json"
        if not path.exists():
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, path)
        if not meta.exists():
            meta.write_text(json.dumps({"sha256": digest, **metadata}, sort_keys=True, indent=2) + "\n")
        return ArtifactRef(digest, path, meta)
```

- [ ] **Step 5: Implement append-only event journal with file locking**

Use `fcntl.flock` on Linux and derive the next sequence from the final valid JSONL row while holding the lock.

```python
# src/authorial_flow/events.py
import fcntl, json, time
from pathlib import Path

class EventJournal:
    def __init__(self, path: Path):
        self.path = path

    def append(self, kind: str, payload: dict) -> int:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+", encoding="utf-8") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            fh.seek(0)
            rows = [line for line in fh.read().splitlines() if line.strip()]
            seq = (json.loads(rows[-1])["sequence"] if rows else 0) + 1
            fh.seek(0, 2)
            fh.write(json.dumps({"sequence": seq, "time": time.time(), "kind": kind, **payload}) + "\n")
            fh.flush()
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            return seq
```

- [ ] **Step 6: Define compact typed graph state**

Create `AuthorialState` matching the approved spec fields, but store large payloads as `str` artifact hashes/refs. Use `Annotated[list[T], operator.add]` only for true append-only fields; overwrite snapshots for current-node results.

- [ ] **Step 7: Run tests**

Run: `pytest tests/unit/test_state_storage.py -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/authorial_flow/{config.py,state.py,artifacts.py,events.py} tests/unit/test_state_storage.py
git commit -m "feat: add durable state and artifact primitives"
```

---

### Task 3: Secret Isolation and Nonblocking Process Runner with Heartbeat

**Files:**
- Create: `src/authorial_flow/secrets.py`
- Create: `src/authorial_flow/process_runner.py`
- Test: `tests/unit/test_process_runner.py`
- Fixture: `tests/fixtures/silent_child.py`

**Interfaces:**
- Produces: `child_env(base: Mapping[str, str], deny: set[str]) -> dict[str, str]`
- Produces: `ProcessRunner.run(ProcessSpec) -> ProcessResult`
- Produces heartbeat callback records at least every configured interval while child is alive.

- [ ] **Step 1: Write a silent child fixture**

```python
# tests/fixtures/silent_child.py
import sys, time
print("started", flush=True)
time.sleep(float(sys.argv[1]))
print("finished", flush=True)
```

- [ ] **Step 2: Write failing heartbeat/secret tests**

```python
# tests/unit/test_process_runner.py
import os, sys, time
from pathlib import Path
from authorial_flow.process_runner import ProcessRunner, ProcessSpec
from authorial_flow.secrets import child_env


def test_child_env_strips_pangram_secret(monkeypatch):
    env = {"PATH": os.environ["PATH"], "PANGRAM_API_KEY": "secret", "KEEP": "x"}
    got = child_env(env, {"PANGRAM_API_KEY"})
    assert "PANGRAM_API_KEY" not in got
    assert got["KEEP"] == "x"


def test_silent_child_emits_heartbeats(tmp_path: Path):
    beats = []
    runner = ProcessRunner(heartbeat_seconds=0.1, on_heartbeat=beats.append)
    result = runner.run(ProcessSpec(
        argv=[sys.executable, "tests/fixtures/silent_child.py", "0.35"],
        cwd=Path.cwd(), timeout_seconds=2,
    ))
    assert result.returncode == 0
    assert len(beats) >= 2
    assert result.stdout.endswith("finished\n")
```

- [ ] **Step 3: Confirm failure**

Run: `pytest tests/unit/test_process_runner.py -q`

Expected: import failures.

- [ ] **Step 4: Implement secret helpers**

```python
# src/authorial_flow/secrets.py
from collections.abc import Mapping

def child_env(base: Mapping[str, str], deny: set[str]) -> dict[str, str]:
    return {k: v for k, v in base.items() if k not in deny}

def redact_argv(argv: list[str]) -> list[str]:
    return ["***" if "key=" in x.lower() or "token=" in x.lower() else x for x in argv]
```

- [ ] **Step 5: Implement selector-based subprocess draining**

`ProcessRunner` must use `subprocess.Popen(..., stdout=PIPE, stderr=PIPE, text=False)`, set both pipes nonblocking, register them with `selectors.DefaultSelector`, drain available bytes, and emit heartbeat callbacks on wall-clock schedule independent of child output. It must terminate then kill after grace on timeout and return captured stdout/stderr, PID, duration, and termination reason.

- [ ] **Step 6: Add Ctrl+C behavior test**

Mock `Popen`/signal handling or run a 5-second fixture in a subprocess test; verify `KeyboardInterrupt` triggers child termination and re-raises after writing a terminal event through a callback.

- [ ] **Step 7: Run tests**

Run: `pytest tests/unit/test_process_runner.py -q`

Expected: PASS with heartbeat test completing <2 seconds.

- [ ] **Step 8: Commit**

```bash
git add src/authorial_flow/{secrets.py,process_runner.py} tests/unit/test_process_runner.py tests/fixtures/silent_child.py
git commit -m "feat: add observable nonblocking process runner"
```

---

### Task 4: Claude and Codex Structured CLI Adapters

**Files:**
- Create: `src/authorial_flow/models/__init__.py`
- Create: `src/authorial_flow/models/common.py`
- Create: `src/authorial_flow/models/claude_cli.py`
- Create: `src/authorial_flow/models/codex_cli.py`
- Test: `tests/unit/test_model_adapters.py`

**Interfaces:**
- Produces: `ModelCall(prompt, schema, role, request_id) -> ModelResult`
- Produces: `ClaudeCLI.call(call, runner, store) -> ModelResult`
- Produces: `CodexCLI.call(call, runner, store) -> ModelResult`
- `ModelResult` includes exact resolved model, CLI version, parsed JSON/text, stdout/stderr refs, request_id.

- [ ] **Step 1: Write parser/request-identity tests**

```python
# tests/unit/test_model_adapters.py
from authorial_flow.models.common import stable_request_id, extract_json_object


def test_request_identity_changes_with_prompt_or_schema():
    a = stable_request_id("claude", "role", "p", {"type": "object"})
    b = stable_request_id("claude", "role", "q", {"type": "object"})
    assert a != b


def test_json_extractor_accepts_wrapped_payload():
    assert extract_json_object('prefix {"verdict":"PASS"} suffix') == {"verdict": "PASS"}
```

- [ ] **Step 2: Implement common data classes and JSON extraction**

Use SHA-256 over provider/role/model candidate/prompt/schema canonical JSON for request identity. Reject multiple ambiguous JSON objects rather than guessing.

- [ ] **Step 3: Implement Claude CLI adapter using stdin task payload**

The task prompt goes through stdin; the short CLI prompt only instructs the model to return the requested representation. Try cached resolved model first, then configured aliases. Do not pass Pangram credentials in the child environment. Persist every attempt's stdout/stderr through `ArtifactStore`.

- [ ] **Step 4: Implement Codex schema-constrained adapter**

Invoke:

```text
codex exec --ephemeral --sandbox read-only --skip-git-repo-check \
  --config model_reasoning_effort="high" \
  --output-schema <schema.json> --output-last-message <output.json> -
```

The adapter creates the schema/output paths inside `.state/artifacts/tmp/<request_id>/`, validates the returned JSON against the requested Pydantic/JSON schema at the caller boundary, then content-addresses and removes the temporary directory.

- [ ] **Step 5: Add mocked `ProcessRunner` tests for model fallback and diagnostics**

Test first model nonzero → second model success; malformed JSON → retry; all failures → `ProviderFailure` carrying attempt artifact refs, not raw secrets.

- [ ] **Step 6: Run tests**

Run: `pytest tests/unit/test_model_adapters.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/authorial_flow/models tests/unit/test_model_adapters.py
git commit -m "feat: add structured Claude and Codex adapters"
```

---

### Task 5: Pangram Async Client with Checkpointable Task Identity

**Files:**
- Create: `src/authorial_flow/models/pangram.py`
- Test: `tests/unit/test_pangram.py`

**Interfaces:**
- Produces: `PangramClient.ensure_model("pangram-4")`
- Produces: `PangramClient.submit(text, candidate_hash) -> PangramTask`
- Produces: `PangramClient.poll(task_id) -> PangramResult`
- No method submits when a checkpoint already contains a task ID for same text/model identity.

- [ ] **Step 1: Write tests with `httpx.MockTransport`**

```python
# tests/unit/test_pangram.py
import httpx
from authorial_flow.models.pangram import PangramClient


def test_submit_payload_and_poll_success():
    calls = []
    def handler(req: httpx.Request):
        calls.append((req.method, req.url.path))
        if req.url.path == "/models":
            return httpx.Response(200, json={"models": [{"name": "pangram-4"}]})
        if req.url.path == "/task" and req.method == "POST":
            return httpx.Response(200, json={"task_id": "t1"})
        return httpx.Response(200, json={"stage": "STAGE_SUCCESS", "version": "4.0", "prediction_short": "Human", "fraction_ai": 0, "fraction_ai_assisted": 0, "windows": []})
    client = PangramClient("k", httpx.Client(transport=httpx.MockTransport(handler), base_url="https://text.external-api.pangram.com"))
    client.ensure_model("pangram-4")
    task = client.submit("hello", "abc")
    result = client.poll(task.task_id)
    assert result.is_human is True
    assert calls.count(("POST", "/task")) == 1
```

- [ ] **Step 2: Implement model access, submit, and poll**

Persist only task/result data passed back to node callers; never persist the key. Normalize result acceptance to explicit fields (`version == "4.0"`, Human, zero AI/assisted, no AI windows).

- [ ] **Step 3: Add resume/idempotency test at node boundary**

The node receives `pangram_pending={request_identity: task_id}`; if present it polls directly and the mock asserts zero POSTs.

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_pangram.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/authorial_flow/models/pangram.py tests/unit/test_pangram.py
git commit -m "feat: add resumable Pangram client"
```

---

### Task 6: Policy Snapshot, Project Identity, and Hard Regression Provenance

**Files:**
- Create: `src/authorial_flow/policy.py`
- Create: `src/authorial_flow/project.py`
- Create: `src/authorial_flow/nodes/bootstrap.py`
- Create: `src/authorial_flow/nodes/regression.py`
- Create: `tests/regression/test_regression_provenance.py`
- Populate: `policy/joel-articles-4.12.0-candidate/`
- Populate: `project/` with migrated development fixtures.

**Interfaces:**
- Produces: `PolicySnapshot.load(path) -> PolicySnapshot`
- Produces: `ProjectInputs.load(project_dir) -> ProjectInputs`
- Produces: `compute_thread_id(inputs, policy, graph_version, learning_version) -> str`
- Produces: `run_hard_regressions(ctx) -> RegressionSummary`

- [ ] **Step 1: Copy the approved policy snapshot and migrated fixtures verbatim**

Copy the exact current Project Source versions for required policy files. Copy legacy free-will `INPUT.md`, requirements/context, owner flow gold, semantic-relation gold, diagnostic positive file, and Pangram source baseline. Record SHA-256 in `policy/MANIFEST.json` and `project/MANIFEST.json`.

- [ ] **Step 2: Write provenance tests**

```python
# tests/regression/test_regression_provenance.py
from authorial_flow.nodes.regression import suite_identity, cached_result_matches


def test_stale_other_suite_cannot_pass(tmp_path):
    expected_hash, expected_ids = suite_identity({"cases": [{"id": "a"}, {"id": "b"}]})
    stale = {"suite_sha256": expected_hash, "case_ids": ["x"], "pass": True}
    assert cached_result_matches(stale, expected_hash, expected_ids) is False


def test_diagnostic_positive_is_not_hard_gate():
    from authorial_flow.nodes.regression import RegressionSummary
    summary = RegressionSummary(owner_flow_pass=True, semantic_pass=True, positive_diagnostic_pass=False)
    assert summary.hard_pass is True
```

- [ ] **Step 3: Implement policy/project hash validation and thread identity**

Thread ID must hash canonical JSON containing source hashes, requirements/context hash, owner/semantic gold hash, policy manifest hash, graph version, and learning version. Diagnostic-positive hash is recorded but cannot alter hard-pass semantics.

- [ ] **Step 4: Implement regression result provenance records**

Every suite result includes suite hash, ordered case IDs, prompt/program version, provider/model identity, child exit code, stdout/stderr refs, result artifact ref, and hard/diagnostic status.

- [ ] **Step 5: Run regression tests**

Run: `pytest tests/regression/test_regression_provenance.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add policy project src/authorial_flow/{policy.py,project.py} src/authorial_flow/nodes/{bootstrap.py,regression.py} tests/regression/test_regression_provenance.py
git commit -m "feat: bind policy project and regression provenance"
```

---

### Task 7: Authority-Aware Basic Representation and Atomic Move Splitting

**Files:**
- Create: `src/authorial_flow/authority.py`
- Create: `src/authorial_flow/nodes/represent.py`
- Create: `src/authorial_flow/nodes/generate.py`
- Create: `src/authorial_flow/prompts/represent.md`
- Create: `src/authorial_flow/prompts/writer.md`
- Test: `tests/unit/test_representation_atomicity.py`

**Interfaces:**
- Produces: `AuthorityUnit(id, text, authority, must_preserve, exact_lock, disposition)`
- Produces: `represent_source(...) -> RepresentationResult`
- Produces: `candidate_semantic_spans(text: str) -> list[str]`

- [ ] **Step 1: Write authority/coverage tests**

```python
# tests/unit/test_representation_atomicity.py
from authorial_flow.authority import Authority, AuthorityUnit
from authorial_flow.nodes.generate import candidate_semantic_spans


def test_ai_provisional_is_not_automatically_mandatory():
    unit = AuthorityUnit(id="u1", text="AI bridge", authority=Authority.AI_PROVISIONAL)
    assert unit.must_preserve is False


def test_owner_locked_is_mandatory():
    unit = AuthorityUnit(id="u2", text="exact memory", authority=Authority.OWNER_LOCKED)
    assert unit.must_preserve is True


def test_atomicity_splits_polished_second_move():
    spans = candidate_semantic_spans("Choices arise from conditions, which raises the question of who chooses.")
    assert len(spans) == 2
```

- [ ] **Step 2: Implement authority enum/data model**

```python
from enum import StrEnum
from pydantic import BaseModel

class Authority(StrEnum):
    OWNER_LOCKED = "OWNER_LOCKED"
    OWNER_GROUNDED = "OWNER_GROUNDED"
    AI_PROVISIONAL = "AI_PROVISIONAL"
    RESEARCH_PROVISIONAL = "RESEARCH_PROVISIONAL"
    OPEN_AUTHORIAL = "OPEN_AUTHORIAL"

class AuthorityUnit(BaseModel):
    id: str
    text: str
    authority: Authority
    exact_lock: bool = False
    disposition: str = "unresolved"

    @property
    def must_preserve(self) -> bool:
        return self.authority in {Authority.OWNER_LOCKED, Authority.OWNER_GROUNDED}
```

- [ ] **Step 3: Implement Basic representation prompt/schema**

The prompt sees source + provenance metadata only inside the representation node. It explicitly forbids treating inherited AI bridges/order/stopping point as owner authority. Output contains units, section job, and exact-lock reasons; writer receives units, not raw source.

- [ ] **Step 4: Implement deterministic atomic splitter**

Split hard boundaries: multiple sentences, semicolon/em-dash turns, substantive colon joins, `, which ...`, and pronoun-led `, and that/this/it/they...` propositional continuations. Keep a single compound predicate intact.

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_representation_atomicity.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/authorial_flow/{authority.py,nodes/represent.py,nodes/generate.py,prompts} tests/unit/test_representation_atomicity.py
git commit -m "feat: add authority-aware atomic representation"
```

---

### Task 8: Candidate-Blind Pressure, Local Flow, Fidelity, and Stop/Rollback Nodes

**Files:**
- Create: `src/authorial_flow/nodes/pressure.py`
- Create: `src/authorial_flow/nodes/flow.py`
- Create: `src/authorial_flow/nodes/fidelity.py`
- Create: `src/authorial_flow/nodes/stopping.py`
- Create: `src/authorial_flow/prompts/pressure.md`
- Create: `src/authorial_flow/prompts/entry_edge.md`
- Create: `src/authorial_flow/prompts/full_edge.md`
- Create: `src/authorial_flow/prompts/relation_guard.md`
- Create: `src/authorial_flow/prompts/semantic_guard.md`
- Test: `tests/regression/test_known_flow_cases.py`
- Test: `tests/regression/test_known_relation_cases.py`

**Interfaces:**
- Produces: `PressureVote`, `CommittedPressure`
- Produces: `EdgeResult`, `FidelityResult`, `StopDecision`
- `commit_pressure(votes)` gives credible OPEN vote veto over premature stop; stop requires agreed/strong conditions.

- [ ] **Step 1: Encode the existing owner-labeled bad edges as fixtures**

Tests load `project/HUMAN-FLOW-GOLD.json`; they never embed those strings in writer prompts/code.

- [ ] **Step 2: Write deterministic vote aggregation tests**

```python
from authorial_flow.nodes.pressure import PressureVote, commit_pressure


def test_open_vote_vetoes_ordinary_premature_stop():
    result = commit_pressure([
        PressureVote(state="NATURAL_STOP", confidence=.84, live_pressure=""),
        PressureVote(state="OPEN", confidence=.81, live_pressure="what follows?"),
    ])
    assert result.state == "OPEN"
```

- [ ] **Step 3: Implement pressure reader node**

Run Claude/Codex concurrently via `ThreadPoolExecutor(max_workers=2)` because providers are independent; graph state mutation occurs only after both results return. Persist votes separately before aggregation.

- [ ] **Step 4: Implement entry/full edge judges**

Entry judge receives only precommitted pressure, immediate previous move, and entry span. Full edge judge receives accepted prose + atomic candidate but cannot see raw source/owner gold. Later candidate material cannot alter the precommitted state.

- [ ] **Step 5: Implement relation/semantic fidelity guards**

Fidelity node may see source/authority units. It enforces exact owner-grounded obligations while permitting AI-provisional relation replacement/disposition. Test the legacy invented `answers the second question` and `so choices happen...` failures from semantic-gold fixtures.

- [ ] **Step 6: Implement stop/rollback route**

`NATURAL_STOP` + unresolved must-preserve units → bounded rollback/replan. `NATURAL_STOP` + only provisional unresolved units → disposition provisional units and stop. Equivalent rejected branches are hashed from pressure + normalized candidate + failure class.

- [ ] **Step 7: Run regression tests**

Run: `pytest tests/regression/test_known_flow_cases.py tests/regression/test_known_relation_cases.py -q`

Expected: PASS for known owner/semantic cases; source-order diagnostic may fail without failing suite.

- [ ] **Step 8: Commit**

```bash
git add src/authorial_flow/nodes src/authorial_flow/prompts tests/regression
git commit -m "feat: enforce live flow and relational fidelity"
```

---

### Task 9: Global Cold Organization Audit, Editorial Candidate Freeze, and Pangram-Downstream Policy

**Files:**
- Create: `src/authorial_flow/nodes/cold_audit.py`
- Create: `src/authorial_flow/nodes/revise.py`
- Create: `src/authorial_flow/candidates.py`
- Create: `src/authorial_flow/nodes/detector_search.py`
- Create: `src/authorial_flow/prompts/cold_audit.md`
- Create: `src/authorial_flow/prompts/cold_revision.md`
- Test: `tests/unit/test_candidate_freeze.py`
- Test: `tests/integration/test_detector_downstream.py`

**Interfaces:**
- Produces: `ColdAuditResult`
- Produces: `CandidateRecord`, `CandidateLineage`
- Produces: `freeze_editorial_winner(candidates) -> CandidateRecord`
- Detector node accepts only a frozen editorial winner or a meaning-equivalent detector variant linked to it.

- [ ] **Step 1: Write editorial-freeze tests**

```python
# tests/unit/test_candidate_freeze.py
from authorial_flow.candidates import CandidateRecord, choose_editorial_winner


def test_detector_score_cannot_change_editorial_ranking():
    better = CandidateRecord(id="a", text="better", editorial_score=9.0, pangram=None)
    weaker = CandidateRecord(id="b", text="weaker", editorial_score=7.0, pangram={"prediction":"Human"})
    assert choose_editorial_winner([weaker, better]).id == "a"
```

- [ ] **Step 2: Implement cold audit schema and prompt**

Audit checks semantic sanity again, curious-reader chain, functional redundancy, invisible-outline/global shape, false completeness/symmetry, stopping point, and authority/fidelity. It returns defects, not rewritten prose. `revise.py` receives only the frozen candidate plus explicit defect records and must preserve every authority obligation. Run audit 1, revise only if defects exist, audit 2, and run audit 3 only when audit 2 still finds a legitimate defect; a no-defect pass ends the loop without paraphrasing for novelty.

- [ ] **Step 3: Implement candidate store and lineage freeze**

A frozen record stores text artifact ref, accepted move list, authority disposition ref, audit refs, editorial rank inputs, and candidate lineage ID. Frozen records are immutable; variants create child lineage records.

- [ ] **Step 4: Write Pangram-skipped integration test**

Mock `PangramClient.submit` to raise if called. Feed a candidate with `final_local_gates.hard_pass=False`; run detector node; assert return status `SKIPPED_LOCAL_FAILURE` and no Pangram call.

- [ ] **Step 5: Implement downstream detector node and bounded meaning-preserving variant search**

Submit only frozen candidates with `hard_pass=True`. On Human, mark first-Human lineage frozen. On non-Human, preserve the editorial winner unchanged and generate a bounded child-lineage search limited to empirically justified local operations: contraction/negation realization, caveat realization, relation-aware list topology with identical semantic items, phrase order/boundary, or another promoted detector hypothesis. Every variant must rerun authority/fidelity/coherence/cold-audit gates before Pangram. If no equally good variant passes, presentation retains the editorial winner with detector status and may additionally expose the strongest Pangram-Human child only when it is materially useful; detector status never changes the parent editorial ranking.

Add tests for: (a) failing editorial winner remains recommended when a weaker Human variant exists; (b) semantic delta in a detector variant is rejected before Pangram; (c) first Human child lineage freezes and later tiny-score wins cannot replace it.

- [ ] **Step 6: Run tests**

Run: `pytest tests/unit/test_candidate_freeze.py tests/integration/test_detector_downstream.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/authorial_flow/{candidates.py,nodes/cold_audit.py,nodes/revise.py,nodes/detector_search.py,prompts/cold_audit.md,prompts/cold_revision.md} tests/unit/test_candidate_freeze.py tests/integration/test_detector_downstream.py
git commit -m "feat: freeze editorial winners before detector testing"
```

---

### Task 10: LangGraph Assembly, SQLite Checkpointing, and Durable Owner Interrupt

**Files:**
- Create: `src/authorial_flow/routing.py`
- Create: `src/authorial_flow/nodes/owner_interrupt.py`
- Create: `src/authorial_flow/graph.py`
- Test: `tests/integration/test_graph_resume.py`

**Interfaces:**
- Produces: `open_graph(config, dependencies) -> ContextManager[CompiledStateGraph]`, keeping the SQLite saver alive for the graph lifetime.
- Uses: `with SqliteSaver.from_conn_string(str(config.checkpoint_db)) as checkpointer:`
- Owner node calls `interrupt(payload)`; caller resumes with `Command(resume=owner_response)` using same `thread_id`.

- [ ] **Step 1: Write a minimal interrupt/resume test with in-memory deterministic node doubles**

```python
# tests/integration/test_graph_resume.py
from langgraph.types import Command
from authorial_flow.graph import build_graph


def test_owner_interrupt_resumes_same_thread(tmp_path, fake_dependencies):
    cfg = {"configurable": {"thread_id": "thread-1"}}
    with open_graph(fake_dependencies.config(tmp_path), fake_dependencies) as app:
        first = app.invoke({"status": "start"}, cfg)
        assert "__interrupt__" in first
        assert first["__interrupt__"][0].value["kind"] == "FINAL_REVIEW"
        second = app.invoke(Command(resume={"kind": "ACCEPT"}), cfg)
        assert second["status"] == "accepted"
```

- [ ] **Step 2: Implement owner response validation**

Accepted kinds for core plan: `ACCEPT`, `BAD_EDGE`, `STOP_BEFORE`, `MEANING_ISSUE`, `VOICE_ISSUE`, `DEFER`. Validate move index bounds before mutating owner-learning files; core plan stores response artifact and route only—learning persistence is Plan 2.

- [ ] **Step 3: Assemble StateGraph using explicit conditional edges**

Use `StateGraph(AuthorialState)`, `START`, `END`. Keep subgraph boundaries explicit: regressions → representation → generation loop → cold audit → freeze → detector → owner interrupt → finalize. `open_graph()` is a context manager that opens `SqliteSaver.from_conn_string(str(config.checkpoint_db))`, compiles the graph, yields it, and closes the saver only after the caller finishes. Keep `LANGGRAPH_STRICT_MSGPACK=true` in launcher/test environments.

- [ ] **Step 4: Verify SQLite resume after process recreation**

Open graph context A, run to interrupt, close context A, open graph context B against the same `.state/checkpoints.sqlite`, resume the same `thread_id`; assert accepted state and no repeated remote-call mock count.

- [ ] **Step 5: Run integration test**

Run: `pytest tests/integration/test_graph_resume.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/authorial_flow/{routing.py,graph.py,nodes/owner_interrupt.py} tests/integration/test_graph_resume.py
git commit -m "feat: assemble checkpointed thought-flow graph"
```

---

### Task 11: CLI, One-Command Launcher, Status Heartbeat, and Automatic Evidence Package

**Files:**
- Create: `src/authorial_flow/cli.py`
- Create: `src/authorial_flow/finalize.py`
- Create: `INSTALL-AND-RUN.sh`
- Create: `RUN.sh`
- Create: `README.md`
- Test: `tests/integration/test_cli.py`

**Interfaces:**
- `authorial-flow run [source]`
- `authorial-flow resume`
- `authorial-flow status`
- `authorial-flow answer '<json>'`
- `authorial-flow package --reason final|bounded-failure`

- [ ] **Step 1: Write CLI help/path tests**

```python
# tests/integration/test_cli.py
from authorial_flow.cli import parser


def test_cli_has_required_commands():
    p = parser()
    text = p.format_help()
    for name in ["run", "resume", "status", "answer", "package"]:
        assert name in text
```

- [ ] **Step 2: Implement CLI configuration/thread selection**

Default root is repository root, default source is `project/INPUT.md`. `run` computes content-addressed thread identity and starts/resumes that thread. `status` reads checkpoint + latest event without starting model calls.

- [ ] **Step 3: Implement terminal heartbeat formatter**

Render one line every 10 seconds:

```text
thread=<12> | node=<name> | phase=<phase> | model=<provider/model> | pid=<pid> | elapsed=<mm:ss> | retry=<n> | moves=<n> | <last event>
```

Use carriage-return update when TTY; append timestamped line when redirected to file.

- [ ] **Step 4: Implement deterministic evidence package**

Package current policy/project manifests, final/last candidate, graph checkpoint metadata export, event journal, relevant artifact metadata/raw outputs, regression evidence, Pangram raw result, and owner response. Use relative paths and SHA256SUMS. Never include secrets or `.venv`.

- [ ] **Step 5: Implement `INSTALL-AND-RUN.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export LANGGRAPH_STRICT_MSGPACK=true
PYTHON="${PYTHON:-python3}"
if ! "$PYTHON" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3,10) else 1)
PY
then
  echo "Python 3.10+ is required." >&2
  exit 2
fi
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/pip install --requirement requirements.lock
.venv/bin/pip install --no-deps -e .
.venv/bin/python -m pytest -q
exec .venv/bin/authorial-flow run "$@"
```

`RUN.sh` performs no installation, exports strict msgpack, and calls `.venv/bin/authorial-flow run` or resume based on arguments.

- [ ] **Step 6: Add resume-after-Ctrl+C integration test with fake provider**

Launch CLI in subprocess with fake long node, send SIGINT after checkpoint event, restart CLI, assert it resumes without incrementing fake remote request count.

- [ ] **Step 7: Run tests**

Run: `pytest tests/integration/test_cli.py tests/integration/test_graph_resume.py -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/authorial_flow/{cli.py,finalize.py} INSTALL-AND-RUN.sh RUN.sh README.md tests/integration/test_cli.py
git commit -m "feat: add one-command resumable CLI runtime"
```

---

### Task 12: Core End-to-End Mock Run and Legacy Failure Regression Cut

**Files:**
- Create: `tests/integration/test_basic_flow_e2e.py`
- Create: `tests/fixtures/legacy_failures/`
- Create: `docs/core-runtime-verification.md`

**Interfaces:**
- Consumes all core interfaces.
- Produces a complete deterministic mocked run from source → hard regressions → Basic Thought-Flow → cold audit → editorial freeze → Pangram-Human mock → owner interrupt → resume/accept → evidence package.

- [ ] **Step 1: Convert the known legacy failures into fixtures**

Include machine-readable records for: two owner bad edges, later-clause rescue, invented answer relation, invented `so` relation, premature natural-stop rollback, stale regression contamination, near-copy replay, Pangram-Human/editorially bad candidate, missing package asset, and silent-child observability. Each fixture records provenance and expected failure class; do not turn model-inferred positives into owner gold.

- [ ] **Step 2: Write full mocked e2e test**

Use deterministic fake Claude/Codex/Pangram adapters. Assert:

```python
assert final.status == "accepted"
assert fake_pangram.submit_count == 1
assert fake_writer.seen_owner_gold is False
assert evidence_zip.exists()
with zipfile.ZipFile(evidence_zip) as z:
    payload = b"\n".join(z.read(name) for name in z.namelist() if not name.endswith("/"))
assert b"PANGRAM_API_KEY" not in payload
assert b"secret-test-value" not in payload
```

- [ ] **Step 3: Add failure-path e2e test**

Feed a fidelity-invalid candidate and assert Pangram submit count remains zero, status is machine-blocked/repairable, and no owner interrupt is emitted.

- [ ] **Step 4: Run core suite**

Run: `pytest tests/unit tests/regression tests/integration -q`

Expected: all PASS.

- [ ] **Step 5: Document exact completed/pending boundaries**

`docs/core-runtime-verification.md` must state that Plan 1 proves Basic Thought-Flow orchestration and persistence, but P3/P4/research escalation, scoped learning, autonomous code repair, and optimizer promotion remain Plan 2/3 work.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/legacy_failures tests/integration/test_basic_flow_e2e.py docs/core-runtime-verification.md
git commit -m "test: verify core thought-flow runtime end to end"
```

---

## Core Plan Verification Gate

Run from a clean checkout/venv:

```bash
export LANGGRAPH_STRICT_MSGPACK=true
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install --no-deps -e .
.venv/bin/python -m pytest tests/unit tests/regression tests/integration -q
.venv/bin/authorial-flow --help
```

Expected: all tests pass, CLI help works, no network is required for mocked suite, and a clean mocked run can pause/resume across a fresh Python process using SQLite.

## Plan Self-Review

- Spec coverage in this plan: sole LangGraph runtime, SQLite checkpoints, content-addressed artifacts, strict secret isolation, heartbeat observability, owner/semantic hard regressions, diagnostic positives, Basic Thought-Flow atomic generation, local/global flow audit, relational fidelity, stopping/rollback, editorial freeze before Pangram, Pangram resumability, owner interrupt, one-command CLI, evidence package.
- Explicitly deferred to Plan 2: automatic provenance/mode inference, full semantic-sanity P3/P4/research escalation, faithful-vs-better-reasoned alternatives, scoped learning store, advanced candidate presentation.
- Explicitly deferred to Plan 3: autonomous executable repair, optimizer promotion, optional DSPy/GEPA, final live-provider cutover/release verification.
- Placeholder scan: no unresolved placeholder tokens, cross-task shorthand, or undefined future interface is used as an implementation instruction.
- Type/interface consistency: Plan 1 defines the storage/model/state/node interfaces consumed by Plans 2 and 3.
