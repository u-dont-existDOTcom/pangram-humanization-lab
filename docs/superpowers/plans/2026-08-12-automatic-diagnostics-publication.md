# Automatic Diagnostics Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically publish a privacy-safe diagnostic record for installer and runtime outcomes to a separate Git branch without changing the installed source checkout or blocking article execution.

**Architecture:** A new diagnostics module owns allowlisted summary construction, an atomic local outbox, and an isolated Git transport. Installer/bootstrap and CLI result boundaries call one nonblocking facade; a manual `publish-results` command creates a snapshot and retries queued records.

**Tech Stack:** Python 3.10+, standard library, Git CLI, pytest, existing `RuntimeConfig`/journal/decision-trace contracts.

## Global Constraints

- Article, project, policy, owner-gold, semantic-gold, and promoted learning material remain P0 and byte-identical.
- Default remote repository identity is exactly `u-dont-existDOTcom/pangram-humanization-lab`.
- Default branch is exactly `diagnostics/authorial-flow-graph-v1`.
- No full evidence ZIP, prose, prompt, transcript, stdout/stderr body, exception message, credential, environment value, or full local path may enter a remote diagnostic.
- Publication is nonblocking, bounded, idempotent, non-force-pushing, and unable to mutate the source worktree.

---

### Task 1: Allowlisted diagnostic records and atomic outbox

**Files:**
- Create: `src/authorial_flow/diagnostics.py`
- Create: `tests/unit/test_diagnostics.py`

**Interfaces:**
- Produces: `build_diagnostic_record(config, *, phase, outcome, result=None, report_path=None, command=None, returncode=None, now=None) -> dict[str, Any]`
- Produces: `queue_diagnostic(config, record) -> Path`
- Produces: `load_queued_diagnostics(config) -> tuple[Path, ...]`

- [ ] **Step 1: Write failing record tests** with hand-derived literals for known status/failure/provider fields and sentinels in every prohibited input channel.

```python
record = build_diagnostic_record(
    cfg,
    phase="installer-live-smoke",
    outcome="credential_required",
    result={"accepted_moves": ["PROSE-SENTINEL"], "failure_class": "PROVIDER_PLUMBING"},
    report_path=report,
    command=[".venv/bin/python", "scripts/live_smoke.py", "--pangram"],
    returncode=3,
    now=1786518307.0,
)
encoded = json.dumps(record, sort_keys=True)
assert record["command_kind"] == "live_smoke"
assert record["providers"]["pangram"]["status"] == "credential_required"
assert "PROSE-SENTINEL" not in encoded
assert "SECRET-SENTINEL" not in encoded
assert "/home/joel" not in encoded
```

- [ ] **Step 2: Run Task 1 tests and observe failure because `authorial_flow.diagnostics` does not exist.**

Run: `.venv/bin/python -m pytest -q tests/unit/test_diagnostics.py`

Expected: collection error naming the missing module.

- [ ] **Step 3: Implement the smallest allowlisted builder and atomic outbox.** Unknown identifiers become `UNCLASSIFIED` plus SHA-256; JSON is written through a same-directory temporary file and `os.replace` with mode `0600`.

- [ ] **Step 4: Run Task 1 tests and the existing secret/security slice.**

Run: `.venv/bin/python -m pytest -q tests/unit/test_diagnostics.py tests/regression/test_supervisor_security.py tests/repair/test_failure_evidence.py`

Expected: all pass.

- [ ] **Step 5: Commit Task 1.**

```bash
git add src/authorial_flow/diagnostics.py tests/unit/test_diagnostics.py
git commit -m "feat: build privacy-safe diagnostic records"
```

### Task 2: Isolated diagnostics-branch Git transport

**Files:**
- Modify: `src/authorial_flow/diagnostics.py`
- Create: `tests/integration/test_diagnostics_git.py`

**Interfaces:**
- Produces: `PublicationResult(status, run_id, branch, queued_count, commit_sha, failure_kind, attempts)`
- Produces: `publish_queued_diagnostics(config, *, remote_url=None, remote_name=None, branch=None, timeout_seconds=45) -> PublicationResult`
- Produces: `publish_diagnostic(config, record, **transport_options) -> PublicationResult`

- [ ] **Step 1: Write failing real-Git integration tests.** Initialize a source repository and separate bare remote, record source HEAD/status, publish two queued records, and inspect the remote branch with `git show`.

```python
before_head = git(source, "rev-parse", "HEAD")
before_status = git(source, "status", "--porcelain=v1", "--untracked-files=all")
result = publish_diagnostic(cfg, record, remote_url=str(remote), branch=DIAGNOSTICS_BRANCH)
assert result.status == "published"
assert git(source, "rev-parse", "HEAD") == before_head
assert git(source, "status", "--porcelain=v1", "--untracked-files=all") == before_status
remote_json = git(remote, "show", f"{DIAGNOSTICS_BRANCH}:LATEST.json")
assert json.loads(remote_json)["run_id"] == record["run_id"]
```

- [ ] **Step 2: Run the Git integration tests and observe missing publisher failures.**

Run: `.venv/bin/python -m pytest -q tests/integration/test_diagnostics_git.py`

Expected: import/attribute failure for the transport API.

- [ ] **Step 3: Implement the disposable diagnostics checkout and bounded fast-forward retry.** Use `GIT_TERMINAL_PROMPT=0`, fixed commit identity, validated refs, depth-one fetch of only the diagnostics branch, no force push, and enum-only failure classification.

- [ ] **Step 4: Add and run queue recovery, idempotency, timeout/failure, and sentinel tests.** A failed remote must retain the record and return `queued`; the same queued record must disappear only after a later verified push.

Run: `.venv/bin/python -m pytest -q tests/unit/test_diagnostics.py tests/integration/test_diagnostics_git.py`

Expected: all pass, including source HEAD/status invariance.

- [ ] **Step 5: Commit Task 2.**

```bash
git add src/authorial_flow/diagnostics.py tests/integration/test_diagnostics_git.py
git commit -m "feat: publish diagnostics on an isolated Git branch"
```

### Task 3: Installer/runtime integration and manual retry

**Files:**
- Modify: `src/authorial_flow/bootstrap_repair.py`
- Modify: `src/authorial_flow/cli.py`
- Modify: `RUN.sh`
- Modify: `tests/integration/test_bootstrap_repair.py`
- Modify: `tests/integration/test_cli.py`
- Create: `tests/integration/test_diagnostics_end_to_end.py`

**Interfaces:**
- Consumes: `publish_diagnostic` and `publish_queued_diagnostics` from Tasks 1-2.
- Produces: `authorial-flow publish-results` and `./RUN.sh publish-results`.

- [ ] **Step 1: Write failing integration tests for all result boundaries.** Use a real local bare diagnostics remote and assert committed summaries for initial preflight pass, credential-required smoke, account-action-required smoke, repair exhaustion, runtime bounded stop, accepted completion, supervisor pause, and manual publication.

- [ ] **Step 2: Run the focused integration tests and observe that no diagnostics branch is created.**

Run: `.venv/bin/python -m pytest -q tests/integration/test_bootstrap_repair.py tests/integration/test_cli.py tests/integration/test_diagnostics_end_to_end.py`

Expected: new assertions fail because result boundaries do not call the publisher and the CLI subcommand is absent.

- [ ] **Step 3: Integrate one nonblocking publication facade.** Every result boundary passes enums, counts, hashes, and report path only; it never passes command stdout/stderr or article fields. Publish before repair `execv`, and preserve every wrapped return/exit code.

- [ ] **Step 4: Implement `publish-results`.** The command creates one status snapshot from current thread/event metadata, queues it, flushes all pending records, prints one content-free status line, and returns zero for `published` or `nothing_to_publish`, nonzero for a still-queued manual request.

- [ ] **Step 5: Run the focused integration, CLI, bootstrap, supervisor, and release slices.**

Run: `.venv/bin/python -m pytest -q tests/integration/test_bootstrap_repair.py tests/integration/test_cli.py tests/integration/test_diagnostics_end_to_end.py tests/integration/test_supervisor_cli.py tests/release/test_release_package.py`

Expected: all pass with source result codes unchanged.

- [ ] **Step 6: Commit Task 3.**

```bash
git add src/authorial_flow/bootstrap_repair.py src/authorial_flow/cli.py RUN.sh tests/integration/test_bootstrap_repair.py tests/integration/test_cli.py tests/integration/test_diagnostics_end_to_end.py
git commit -m "feat: publish installer and runtime results automatically"
```

### Task 4: Release, documentation, and exact verification

**Files:**
- Modify: `src/authorial_flow/version.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `docs/acceptance-matrix.md`
- Modify: `docs/migration-cutover.md`
- Modify: `docs/release-checklist.md`
- Modify: `tests/unit/test_release_guardrails.py`
- Regenerate: `MANIFEST.json`
- Regenerate: `SHA256SUMS.txt`
- Create: `docs/2026-08-12-automatic-diagnostics-publication-review.md`

**Interfaces:**
- Produces: installable runtime `1.3.0-dev1` and exact release evidence.

- [ ] **Step 1: Bump runtime and graph release metadata to `1.3.0-dev1`; document automatic branch publication, privacy exclusions, queue behavior, and manual retry.**

- [ ] **Step 2: Add release assertions that protected `project/` and `policy/` trees are unchanged from `1.2.0-dev1`, project instructions remain below 8,000 characters, and diagnostics source/tests/docs enter the manifest.**

- [ ] **Step 3: Regenerate release metadata with the project release builder.**

Run: `.venv/bin/python scripts/build_release.py --root .`

Expected: manifest and SHA-256 inventory regenerate without modifying protected content.

- [ ] **Step 4: Run fresh full verification.**

Run: `env -u PANGRAM_API_KEY -u BRAVE_SEARCH_API_KEY -u OPENAI_API_KEY -u ANTHROPIC_API_KEY .venv/bin/python -m pytest -q`

Run: `.venv/bin/python scripts/build_release.py --root . --verify`

Expected: zero failures and successful exact release verification.

- [ ] **Step 5: Build a disposable clone/install against a local bare source remote and local bare diagnostics remote.** Confirm `INSTALL-AND-RUN.sh` reaches the diagnostics branch with live smoke disabled and source `.state` preserved.

- [ ] **Step 6: Record exact commands, counts, hashes, protected-tree comparison, and remaining target-machine boundaries in the review document; commit the release.**

```bash
git add src/authorial_flow/version.py pyproject.toml README.md docs tests MANIFEST.json SHA256SUMS.txt
git commit -m "release: authorial flow graph 1.3.0-dev1"
```
