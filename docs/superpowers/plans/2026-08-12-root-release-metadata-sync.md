# Root Release Metadata Synchronization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make committed root release metadata reproducibly match the exact content-bearing Git commit and generated release ZIP.

**Architecture:** Add one `write_root_release_metadata()` operation that reuses the deterministic ZIP builder and atomically installs its two generated metadata files. Teach the source-commit resolver to step across metadata-only finalization commits so a clean rebuild after committing those excluded files remains identical.

**Tech Stack:** Python 3.12, Git CLI, `zipfile`, pytest.

## Global Constraints

- Preserve P0 article, project, policy, owner-gold, semantic-gold, and promoted learning material byte-for-byte.
- Root `MANIFEST.json` and `SHA256SUMS.txt` remain excluded from their own release member list.
- Existing `scripts/build_release.py --out <zip>` behavior remains compatible.
- Metadata writes use same-directory temporary files and `os.replace`; no direct truncation of either destination.
- The final metadata-only commit must rebuild to metadata that identifies the preceding content-bearing commit.

---

### Task 1: Add a reproducible root-metadata finalization command

**Files:**
- Modify: `tests/release/test_release_package.py`
- Modify: `src/authorial_flow/release.py`
- Modify: `scripts/build_release.py`

**Interfaces:**
- Consumes: `build_release(repo_root: Path, out_zip: Path) -> ReleaseManifest`.
- Produces: `write_root_release_metadata(repo_root: Path) -> ReleaseManifest` and CLI flag `--write-root-metadata`.

- [ ] **Step 1: Write the failing executable regression**

Add `from authorial_flow.version import GRAPH_VERSION` to `tests/release/test_release_package.py`, then add:

```python
def test_root_metadata_sync_is_rebuild_stable_after_metadata_only_commit(tmp_path):
    root = tmp_path / "Téléchargements" / "authorial-flow-graph-v1"
    root.mkdir(parents=True)
    for name, data in {
        "INSTALL-AND-RUN.sh": "#!/bin/sh\\nexit 0\\n",
        "RUN.sh": "#!/bin/sh\\nexit 0\\n",
        "requirements.lock": "# locked\\n",
        "pyproject.toml": "[project]\\nname='synthetic-release'\\nversion='1'\\n",
        "README.md": "# Synthetic release\\n",
        "PASTE_INTO_PROJECT_INSTRUCTIONS.txt": "instructions\\n",
        "source.txt": "release member\\n",
        "MANIFEST.json": '{"graph_version":"stale"}\\n',
        "SHA256SUMS.txt": "stale\\n",
    }.items():
        (root / name).write_text(data, encoding="utf-8")
    (root / "INSTALL-AND-RUN.sh").chmod(0o755)
    (root / "RUN.sh").chmod(0o755)
    policy = root / "policy" / "test-policy"
    policy.mkdir(parents=True)
    (policy / "MASTER.md").write_text("policy\\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "content release"], cwd=root, check=True)
    content_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "build_release.py"), "--repo", str(root), "--write-root-metadata"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    assert proc.returncode == 0, proc.stderr
    assert "root_metadata=PASS" in proc.stdout
    payload = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    assert payload["graph_version"] == GRAPH_VERSION
    assert payload["source_commit_sha"] == content_commit
    rows = {row["path"]: row for row in payload["members"]}
    assert "MANIFEST.json" not in rows
    assert "SHA256SUMS.txt" not in rows
    for rel, row in rows.items():
        source = root / rel
        assert row["size_bytes"] == len(source.read_bytes())
        assert row["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
        assert row["executable"] == bool(source.stat().st_mode & stat.S_IXUSR)
    sums = {}
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        sums[rel] = digest
    assert sums == {rel: row["sha256"] for rel, row in rows.items()}

    subprocess.run(["git", "add", "MANIFEST.json", "SHA256SUMS.txt"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "finalize release metadata"], cwd=root, check=True)
    rebuilt = tmp_path / "rebuilt.zip"
    manifest = build_release(root, rebuilt)
    assert manifest.source_commit_sha == content_commit
    with zipfile.ZipFile(rebuilt) as archive:
        prefix = manifest.archive_root + "/"
        assert archive.read(prefix + "MANIFEST.json") == (root / "MANIFEST.json").read_bytes()
        assert archive.read(prefix + "SHA256SUMS.txt") == (root / "SHA256SUMS.txt").read_bytes()
```

- [ ] **Step 2: Run the regression and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/release/test_release_package.py::test_root_metadata_sync_is_rebuild_stable_after_metadata_only_commit -q
```

Expected: FAIL because `scripts/build_release.py` requires `--out` and does not recognize `--write-root-metadata`.

- [ ] **Step 3: Make metadata-only commit resolution explicit**

In `src/authorial_flow/release.py`, add:

```python
ROOT_RELEASE_METADATA = {"MANIFEST.json", "SHA256SUMS.txt"}
```

Replace `_source_commit` with:

```python
def _git_text(repo_root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=repo_root, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _source_commit(repo_root: Path) -> str:
    candidate = _git_text(repo_root, "rev-parse", "HEAD")
    if not candidate:
        return "unversioned"
    while True:
        changed = _git_text(
            repo_root, "diff-tree", "--root", "--no-commit-id",
            "--name-only", "-r", candidate,
        )
        paths = {line.strip() for line in changed.splitlines() if line.strip()}
        if not paths or not paths.issubset(ROOT_RELEASE_METADATA):
            return candidate
        parent = _git_text(repo_root, "rev-parse", f"{candidate}^")
        if not parent:
            return candidate
        candidate = parent
```

Use `ROOT_RELEASE_METADATA` in `_include_file` instead of the duplicated root filename literal.

- [ ] **Step 4: Implement atomic root metadata writing**

Add to `src/authorial_flow/release.py`:

```python
def write_root_release_metadata(repo_root: Path) -> ReleaseManifest:
    repo_root = Path(repo_root).resolve()
    with tempfile.TemporaryDirectory(prefix="authorial-flow-root-metadata-") as td:
        release_zip = Path(td) / "release.zip"
        manifest = build_release(repo_root, release_zip)
        prefix = manifest.archive_root + "/"
        with zipfile.ZipFile(release_zip) as archive:
            payloads = {
                name: archive.read(prefix + name)
                for name in sorted(ROOT_RELEASE_METADATA)
            }
    staged: dict[str, Path] = {}
    try:
        for name, data in payloads.items():
            temporary = repo_root / f".{name}.{os.getpid()}.tmp"
            temporary.write_bytes(data)
            os.chmod(temporary, 0o644)
            staged[name] = temporary
        for name, temporary in staged.items():
            os.replace(temporary, repo_root / name)
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
    return manifest
```

- [ ] **Step 5: Expose the finalization command**

In `scripts/build_release.py`, import `write_root_release_metadata`, make `--out` optional, add `--write-root-metadata`, and reject invocation when neither operation is requested. When sync is requested, call the new function and print:

```text
root_metadata=PASS
source_commit=<sha>
graph_version=<version>
policy_version=<version>
```

When `--out` is also present, continue through the existing build and verification path.

- [ ] **Step 6: Run the regression and release suite to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/release/test_release_package.py::test_root_metadata_sync_is_rebuild_stable_after_metadata_only_commit -q
.venv/bin/python -m pytest tests/release/test_release_package.py -q
```

Expected: the new regression passes; all release tests pass.

- [ ] **Step 7: Commit the focused tooling fix**

```bash
git add tests/release/test_release_package.py src/authorial_flow/release.py scripts/build_release.py
git commit -m "fix: synchronize root release metadata"
```

---

### Task 2: Finalize and verify the real 1.3 metadata

**Files:**
- Modify: `docs/2026-08-12-automatic-diagnostics-publication-review.md`
- Modify: `MANIFEST.json`
- Modify: `SHA256SUMS.txt`

**Interfaces:**
- Consumes: `scripts/build_release.py --write-root-metadata` from Task 1.
- Produces: committed root metadata matching the exact content-bearing commit and every release member.

- [ ] **Step 1: Run the full suite and clean release gate before finalization**

Run:

```bash
.venv/bin/python -m pytest -q
```

Then build one temporary ZIP with `--clean-zip-compile` and require `verification=PASS`.

- [ ] **Step 2: Record the root-cause correction and exact verification evidence**

Append the stale 1.2 metadata finding, the missing finalization-command root cause, the executable regression result, full-suite result, clean-build result, and protected-tree comparison to `docs/2026-08-12-automatic-diagnostics-publication-review.md`, without raw errors, credentials, environment values, or full local paths. Commit the review update so it becomes a release member.

- [ ] **Step 3: Synchronize and commit only root metadata**

Run:

```bash
.venv/bin/python scripts/build_release.py --repo . --write-root-metadata
git status --short
```

Require that only `MANIFEST.json` and `SHA256SUMS.txt` changed, then commit:

```bash
git add MANIFEST.json SHA256SUMS.txt
git commit -m "release: finalize 1.3 root metadata"
```

- [ ] **Step 4: Rebuild from the clean final commit and compare exact metadata**

Build a new temporary ZIP with `--clean-zip-compile`. Require:

- `verification=PASS`;
- embedded and root `MANIFEST.json` SHA-256 values are equal;
- embedded and root `SHA256SUMS.txt` SHA-256 values are equal;
- embedded `source_commit_sha` equals the parent of the final metadata-only commit;
- `graph_version=1.3.0-dev1`;
- `project/` and `policy/` still match `cc910f53525d2af7a24175bc28c4282d17732c14`;
- `git diff --check` passes and `git status --short` is empty.

- [ ] **Step 5: Run the full suite once more on the final clean tree**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: all tests pass with zero failures.
