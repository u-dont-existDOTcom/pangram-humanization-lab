# Privacy-Safe Remote Rescue Watch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an hourly ChatGPT Work condition watch detect unresolved outer-controller failures on GitHub, publish only fully verified fast-forward repairs, and remain silent when no irreducible human action is required.

**Architecture:** The local controller publishes a second, narrowly allowlisted repair capsule to the orphan branch `repairs/authorial-flow-graph-v1`; the existing diagnostics branch remains content-free and unchanged. A repository-owned resolver determines whether a failure lineage is still open. The scheduled Work iteration follows a committed runbook and may advance the stable install branch only after real RED/GREEN, integration, full-suite, protected-path, privacy, and current-parent gates execute successfully.

**Tech Stack:** Existing Python diagnostics/Git publication code, Pydantic validation where the installed runtime is available, local Git orphan worktrees, pytest, GitHub connector actions, and ChatGPT Work hourly condition watches.

## Global Constraints

- Implement only after the local hands-off controller plan passes deterministic verification.
- `diagnostics/authorial-flow-graph-v1` remains content-free and backward-compatible.
- Repair capsules publish only to `repairs/authorial-flow-graph-v1` in `u-dont-existDOTcom/pangram-humanization-lab`.
- Article text, project-source prose, prompts, transcripts, raw provider output, environments, credentials, absolute home paths, and evidence ZIP bytes are forbidden remotely.
- Unsafe or unclassifiable fields are omitted; redaction is not treated as proof that arbitrary text is safe.
- A remote repair must prove RED before the patch and GREEN after it, then pass targeted, integration, full-suite, protected-path, privacy, and independent review gates.
- The stable install branch advances only by normal fast-forward. Never force-push or auto-merge.
- The watch acts at most hourly and notifies Joel only for credential, account, repository-permission, or substantive authorial blockers.
- A Work run that cannot execute every gate records `remote_repair_blocked` and changes no code.

---

### Task 1: Strict repair-capsule schema and privacy proof

**Files:**
- Create: `src/authorial_flow/repair_capsule.py`
- Create: `tests/unit/test_repair_capsule.py`
- Create: `tests/fixtures/repair_capsule/unsafe-output.txt`

**Interfaces:**
- Consumes: typed controller outcomes, repository-relative traceback frames, repair verification records, protected source hashes, and explicit secret values.
- Produces: `REPAIR_CAPSULE_FORMAT`, `RepairCapsule`, `RepairDisposition`, `build_repair_capsule(...)`, `validate_repair_capsule(payload)`, `safe_test_excerpt(text, forbidden_values)`, and `failure_lineage_id(...)`.

- [ ] **Step 1: Write failing schema and privacy tests**

```python
def test_capsule_omits_unsafe_test_output_instead_of_redacting_it(tmp_path):
    source_sentence = "This is private article wording that must never leave the machine."
    capsule = build_repair_capsule(
        outcome=bounded_outcome(),
        frames=[("src/authorial_flow/cli.py", "command_resume", 638)],
        test_output=f"FAILED {Path.home()}/Téléchargements/test.py\n{source_sentence}",
        forbidden_values=[source_sentence, str(Path.home())],
    )
    payload = capsule.model_dump(mode="json")
    rendered = json.dumps(payload, ensure_ascii=False)
    assert source_sentence not in rendered
    assert str(Path.home()) not in rendered
    assert payload["test_excerpt"] == ""
    assert payload["test_output_sha256"]
```

- [ ] **Step 2: Run the focused test and observe the missing capsule module**

Run: `.venv/bin/python -m pytest tests/unit/test_repair_capsule.py -q`

Expected: FAIL importing `authorial_flow.repair_capsule`.

- [ ] **Step 3: Implement an exact-key Pydantic schema**

```python
class RepairFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    function: str
    line: int = Field(ge=1)

class RepairCapsule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    format: Literal["authorial-flow-repair-capsule-v1"]
    run_id: str
    lineage_id: str
    failure_signature: str
    program_commit: str
    install_commit: str
    thread_hash: str
    failure_class: str
    phase: str
    origin_node: str
    child_exit: int
    retry_count: int = Field(ge=0)
    frames: list[RepairFrame] = Field(max_length=20)
    declared_regression: list[str]
    test_excerpt: str = Field(max_length=6000)
    test_output_sha256: str
    local_evidence_sha256: str
```

Thread IDs are hashed before publication. Frame paths must be repository-relative, use `/`, exclude `..`, and start with an allowlisted code/test prefix. No source-code line or exception message is included.

Create `tests/fixtures/repair_capsule/unsafe-output.txt` with these literal canaries:

```text
FAILED /home/joel/Téléchargements/authorial-flow-graph-v1/tests/test_private.py
PANGRAM_API_KEY=fixture-secret-never-publish
This is private article wording that must never leave the machine.
```

- [ ] **Step 4: Implement fail-closed test-excerpt classification**

Allow only bounded pytest control lines matching explicit regular expressions for collection, node IDs, assertion summaries without compared values, counts, durations, and return codes. Reject the entire excerpt if any line contains a home path, URL, environment assignment, secret value, non-ASCII control character, quoted payload longer than 80 characters, or a 24-character source n-gram.

- [ ] **Step 5: Add exact round-trip and unknown-key rejection tests**

```python
def test_capsule_round_trip_rejects_extra_fields():
    payload = valid_capsule().model_dump(mode="json")
    assert RepairCapsule.model_validate(payload).model_dump(mode="json") == payload
    with pytest.raises(ValidationError):
        RepairCapsule.model_validate({**payload, "raw_stderr": "forbidden"})
```

- [ ] **Step 6: Run the capsule unit suite**

Run: `.venv/bin/python -m pytest tests/unit/test_repair_capsule.py -q`

Expected: PASS.

- [ ] **Step 7: Commit the capsule contract**

```bash
git add src/authorial_flow/repair_capsule.py tests/unit/test_repair_capsule.py tests/fixtures/repair_capsule/unsafe-output.txt
git commit -m "feat: define privacy-safe repair capsules"
```

---

### Task 2: Queued orphan-branch capsule publication

**Files:**
- Create: `src/authorial_flow/repair_publication.py`
- Create: `tests/integration/test_repair_publication_git.py`
- Modify: `src/authorial_flow/diagnostics.py`
- Modify: `src/authorial_flow/cli.py`
- Modify: `RUN.sh`

**Interfaces:**
- Consumes: validated `RepairCapsule` and `RepairDisposition`, configured Git remotes, and `.state/repair-publication/outbox/`.
- Produces: `REPAIRS_BRANCH`, `queue_repair_record(...)`, `publish_queued_repair_records(...)`, `safely_publish_repair_record(...)`, and CLI command `publish-repair-results`.

- [ ] **Step 1: Write a failing local-Git test for orphan publication without source-checkout mutation**

```python
def test_repair_capsule_publishes_to_orphan_branch_without_switching_source(tmp_path):
    repo, remote = init_source_and_bare_remote(tmp_path)
    cfg = RuntimeConfig.from_root(repo)
    source_head = git(repo, "rev-parse", "HEAD")
    source_branch = git(repo, "branch", "--show-current")
    queue_repair_record(cfg, valid_capsule().model_dump(mode="json"))
    result = publish_queued_repair_records(cfg, remote_url=str(remote))
    assert result.status == "published"
    assert git(repo, "rev-parse", "HEAD") == source_head
    assert git(repo, "branch", "--show-current") == source_branch
    assert read_remote_json(remote, REPAIRS_BRANCH, "runs/run-1.json")["format"] == REPAIR_CAPSULE_FORMAT
```

- [ ] **Step 2: Run the Git test and observe the missing publisher**

Run: `.venv/bin/python -m pytest tests/integration/test_repair_publication_git.py -q`

Expected: FAIL importing `authorial_flow.repair_publication`.

- [ ] **Step 3: Implement a separate queue and orphan checkout**

Use the proven diagnostics transport pattern but do not generalize by moving the existing 926-line diagnostics module in this release. Repair records use:

```text
runs/<run_id>.json
dispositions/<lineage_id>/<program_or_repair_commit>.json
```

The publisher validates every queued file again immediately before staging, uses an isolated `.state/repair-publication/tmp/<uuid>/` checkout, fetches or initializes only the repair branch, commits deterministic paths, and pushes normally. Network or authentication failure leaves the queue intact.

- [ ] **Step 4: Add race and retry tests**

```python
def test_remote_advance_retries_without_losing_queue(tmp_path):
    cfg, remote = race_fixture(tmp_path)
    queued = queue_repair_record(cfg, valid_capsule().model_dump(mode="json"))
    result = publish_queued_repair_records(cfg, remote_url=str(remote), before_push=advance_once)
    assert result.status == "queued"
    assert queued.exists()
    assert publish_queued_repair_records(cfg, remote_url=str(remote)).status == "published"
    assert not queued.exists()
```

- [ ] **Step 5: Integrate publication at bounded outer-repair exhaustion**

The local loop queues and best-effort publishes the capsule only after its own verified repair budget is exhausted or the controller protocol itself cannot run. Successful local repair publishes a disposition linking the lineage to the new repair commit. This publication never changes the child’s exit/outcome.

- [ ] **Step 6: Expose a manual diagnostic command without making it part of normal recovery**

Add `publish-repair-results` beside `publish-results` in the explicit `RUN.sh` command allowlist. Documentation labels it diagnostic-only; the hands-off controller retries automatically.

- [ ] **Step 7: Run diagnostics and repair-publication suites together**

Run: `.venv/bin/python -m pytest tests/unit/test_diagnostics.py tests/integration/test_diagnostics_git.py tests/integration/test_repair_publication_git.py -q`

Expected: PASS and unchanged diagnostics behavior.

- [ ] **Step 8: Commit repair publication**

```bash
git add src/authorial_flow/repair_publication.py src/authorial_flow/diagnostics.py src/authorial_flow/cli.py RUN.sh tests/integration/test_repair_publication_git.py
git commit -m "feat: publish repair capsules separately"
```

---

### Task 3: Unresolved-lineage resolver and remote repair disposition

**Files:**
- Create: `src/authorial_flow/repair_lineage.py`
- Create: `scripts/resolve_remote_repairs.py`
- Create: `tests/unit/test_repair_lineage.py`
- Create: `tests/integration/test_remote_repair_resolver.py`

**Interfaces:**
- Consumes: diagnostics records, repair capsules, and repair dispositions checked out from their orphan branches.
- Produces: `LineageState`, `resolve_lineages(...)`, and JSON CLI output containing `unresolved`, `resolved`, `blocked`, and `invalid` lists.

- [ ] **Step 1: Write resolution-order tests**

```python
def test_later_accepted_result_resolves_same_failure_lineage():
    capsule = repair_capsule(run_id="r1", lineage_id="lineage")
    accepted = diagnostic(run_id="r2", lineage_id="lineage", outcome="accepted", timestamp=2)
    state = resolve_lineages([capsule], [accepted], [])
    assert state.unresolved == ()
    assert state.resolved[0].reason == "accepted"

def test_newer_program_restart_resolves_old_program_failure():
    capsule = repair_capsule(program_commit="old", lineage_id="lineage")
    restart = diagnostic(lineage_id="lineage", outcome="repair_promoted_restart_required", program_commit="new")
    assert resolve_lineages([capsule], [restart], []).resolved[0].program_commit == "new"
```

- [ ] **Step 2: Run the resolver tests and observe the missing module**

Run: `.venv/bin/python -m pytest tests/unit/test_repair_lineage.py -q`

Expected: FAIL importing `authorial_flow.repair_lineage`.

- [ ] **Step 3: Implement deterministic lineage precedence**

Order records by typed timestamp plus run ID. A lineage is resolved only by a later accepted/completed result, a later restart on a different program commit, or an `APPLIED_VERIFIED` disposition naming a commit. `remote_repair_blocked` remains unresolved but prevents another attempt on unchanged capsule/program context. Invalid records never participate.

- [ ] **Step 4: Implement a read-only resolver script**

```bash
.venv/bin/python scripts/resolve_remote_repairs.py \
  --diagnostics-checkout /path/to/diagnostics \
  --repairs-checkout /path/to/repairs \
  --json
```

The script prints no article data and exits 0 when there are no unresolved lineages, 10 when unresolved lineages exist, and 2 for invalid branch data.

- [ ] **Step 5: Run unit and integration resolution tests**

Run: `.venv/bin/python -m pytest tests/unit/test_repair_lineage.py tests/integration/test_remote_repair_resolver.py -q`

Expected: PASS.

- [ ] **Step 6: Commit lineage resolution**

```bash
git add src/authorial_flow/repair_lineage.py scripts/resolve_remote_repairs.py tests/unit/test_repair_lineage.py tests/integration/test_remote_repair_resolver.py
git commit -m "feat: resolve remote repair lineages"
```

---

### Task 4: Repository-owned rescue runbook and verification command

**Files:**
- Create: `src/authorial_flow/remote_repair_gate.py`
- Create: `docs/remote-rescue-watch.md`
- Create: `scripts/verify_remote_repair.py`
- Create: `tests/integration/test_remote_repair_gate.py`
- Modify: `docs/release-checklist.md`

**Interfaces:**
- Consumes: one unresolved validated capsule, its base stable commit, and a candidate repair commit.
- Produces: `verify_remote_repair(...)`, a `remote-repair-verification-v1` JSON receipt, and one of `APPLIED_VERIFIED`, `REMOTE_ADVANCED`, `VERIFICATION_REJECTED`, or `REMOTE_REPAIR_BLOCKED`.

- [ ] **Step 1: Write a failing gate test that rejects claimed success without real RED/GREEN**

```python
def test_remote_gate_rejects_candidate_without_red_green_receipt(tmp_path):
    repo, capsule, candidate = remote_gate_fixture(tmp_path)
    result = verify_remote_repair(repo, capsule, candidate)
    assert result.pass_ is False
    assert result.reason == "MISSING_RED_GREEN_PROOF"
```

- [ ] **Step 2: Run the gate test and observe the missing verifier**

Run: `.venv/bin/python -m pytest tests/integration/test_remote_repair_gate.py -q`

Expected: FAIL importing `authorial_flow.remote_repair_gate`.

- [ ] **Step 3: Implement the exact gate sequence**

The verifier runs, in order:

```python
commands = [
    declared_regression_command,
    [sys.executable, "-m", "compileall", "-q", "src", "tests"],
    [sys.executable, "-m", "pytest", "tests/unit", "tests/regression", "-q"],
    [sys.executable, "-m", "pytest", "tests/integration", "-q"],
    [sys.executable, "-m", "pytest", "-q"],
]
```

It validates the existing RED/GREEN receipt against the declared regression, captures project/policy/learning hashes before and after, runs the capsule privacy validator, performs independent diff review, confirms the candidate descends from the capsule’s program commit, refetches the stable branch, and requires its head still to equal the candidate base.

`scripts/verify_remote_repair.py` is a thin argument parser that calls `authorial_flow.remote_repair_gate.verify_remote_repair`; all testable gate logic stays in the importable module.

- [ ] **Step 4: Add rejection tests for protected drift, privacy failure, stale parent, and skipped full suite**

Each test asserts that no Git push command is attempted.

- [ ] **Step 5: Write the Work iteration runbook with fail-closed commands**

The runbook requires the Work iteration to:

1. fetch both orphan branches and the stable install branch;
2. run `scripts/resolve_remote_repairs.py`;
3. select only the newest unresolved, unblocked lineage;
4. inspect the capsule and repository without retrieving local-only evidence;
5. create a disposable repair branch from the exact capsule program commit;
6. add a regression and record real RED/GREEN proof;
7. run `scripts/verify_remote_repair.py`;
8. push normally only on `APPLIED_VERIFIED` and unchanged stable parent;
9. publish a disposition to the repair branch;
10. stay silent unless a typed irreducible blocker remains.

- [ ] **Step 6: Run remote-gate integration tests**

Run: `.venv/bin/python -m pytest tests/integration/test_remote_repair_gate.py -q`

Expected: PASS.

- [ ] **Step 7: Commit the rescue gate and runbook**

```bash
git add src/authorial_flow/remote_repair_gate.py docs/remote-rescue-watch.md scripts/verify_remote_repair.py tests/integration/test_remote_repair_gate.py docs/release-checklist.md
git commit -m "feat: gate remote rescue repairs"
```

---

### Task 5: Hourly condition watch and end-to-end privacy acceptance

**Files:**
- Create: `tests/integration/test_remote_rescue_e2e.py`
- Create: `docs/2026-08-13-remote-rescue-watch-review.md`
- Modify: `README.md`
- Modify: `tests/unit/test_release_guardrails.py`
- Modify: `MANIFEST.json`
- Modify: `SHA256SUMS.txt`

**Interfaces:**
- Consumes: committed runbook, connected GitHub access, validated branches, and ChatGPT Automations.
- Produces: one enabled hourly condition watch, a verified stable-branch repair path, and exact review evidence.

- [ ] **Step 1: Write the end-to-end local simulation before enabling the watch**

```python
def test_unresolved_capsule_verified_repair_and_later_resume(tmp_path):
    scenario = RemoteRescueScenario(tmp_path)
    scenario.publish_bounded_capsule(lineage="lineage-1", program="old")
    candidate = scenario.repair_with_real_red_green()
    receipt = scenario.verify(candidate)
    assert receipt.disposition == "APPLIED_VERIFIED"
    scenario.fast_forward_stable(candidate)
    scenario.publish_runtime_result(outcome="accepted", program=candidate)
    assert scenario.resolve().unresolved == ()
```

- [ ] **Step 2: Run all privacy and remote-repair tests**

Run: `.venv/bin/python -m pytest tests/unit/test_repair_capsule.py tests/unit/test_repair_lineage.py tests/integration/test_repair_publication_git.py tests/integration/test_remote_repair_resolver.py tests/integration/test_remote_repair_gate.py tests/integration/test_remote_rescue_e2e.py -q`

Expected: PASS.

- [ ] **Step 3: Add release guardrails and run the full deterministic suite**

Run: `.venv/bin/python -m compileall -q src tests`

Run: `.venv/bin/python -m pytest -q`

Expected: every test exits 0, including secret fixtures and article-text canaries absent from generated branch records.

- [ ] **Step 4: Build and verify the clean release**

Run: `.venv/bin/python scripts/build_release.py --out /tmp/authorial-flow-remote-rescue.zip --clean-zip-compile`

Expected: `verification=PASS`.

- [ ] **Step 5: Publish the verified code before scheduling**

Fast-forward the development and stable install branches with no force. Create the empty repair branch only through the tested publisher so it has the exact orphan layout.

- [ ] **Step 6: Perform a harmless GitHub read and create the hourly condition watch**

Use the exact automation prompt:

```text
Inspect u-dont-existDOTcom/pangram-humanization-lab for unresolved validated Authorial Flow repair lineages by following docs/remote-rescue-watch.md at the current stable install commit. Act on at most the newest eligible lineage. Change code or the stable install branch only when the committed resolver and remote-repair verifier both run successfully and return APPLIED_VERIFIED with real RED/GREEN, protected-path, privacy, full-suite, independent-review, and unchanged-parent evidence. Never force-push or merge competing history. If nothing is unresolved or the same failure is already blocked on unchanged context, stay silent. Notify Joel only when the recorded blocker is a credential, account, repository-permission, or substantive authorial decision; never ask him to collect logs.
```

Schedule: `RRULE:FREQ=HOURLY`, timing mode `condition_watch`, using Joel’s personal timezone.

- [ ] **Step 7: Run one deliberate target-machine rescue acceptance**

Induce a harmless test-only outer-controller defect on a non-authoritative acceptance fixture, verify that Zorin publishes the capsule and waits, allow the hourly watch to produce a verified stable fast-forward repair, and confirm the local controller accepts it and resumes the same thread without another terminal command. Remove the fixture defect only through the repair path so the evidence is real.

- [ ] **Step 8: Record verification evidence and finalize metadata**

Write `docs/2026-08-13-remote-rescue-watch-review.md` with capsule hashes, branch commits, automation identifier, test counts, release SHA-256, forbidden-data scans, stable-parent evidence, and target-machine lineage. Regenerate root metadata, commit it separately, rebuild the ZIP, and byte-compare both metadata files.

- [ ] **Step 9: Commit review evidence**

```bash
git add README.md tests/unit/test_release_guardrails.py docs/2026-08-13-remote-rescue-watch-review.md MANIFEST.json SHA256SUMS.txt
git commit -m "release: verify remote rescue watch"
```
