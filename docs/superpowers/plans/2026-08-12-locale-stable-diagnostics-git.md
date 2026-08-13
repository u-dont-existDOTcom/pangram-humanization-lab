# Locale-Stable Diagnostics Git Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make diagnostics Git transport classify first-publication, authentication, network, and race failures consistently on French Zorin without breaking UTF-8 paths such as `~/Téléchargements`.

**Architecture:** Keep locale control inside the existing `_git_result` subprocess boundary. Remove child `LC_ALL` only after deriving its effective character-type locale, restore that value as `LC_CTYPE`, and force `LC_MESSAGES=C` plus `LANGUAGE=C`; no parent environment, diagnostic record, queue, or source checkout is changed.

**Tech Stack:** Python 3.12, `subprocess`, pytest, Git CLI.

## Global Constraints

- Preserve P0 article, project, policy, owner-gold, semantic-gold, and promoted learning material byte-for-byte.
- Do not change the diagnostic schema, privacy allowlist, canonical repository, branch, queue, retry policy, or content-free status line.
- Never persist or print raw Git stderr, credentials, environment values, full paths, article text, prompts, transcripts, or evidence ZIP bytes.
- Preserve UTF-8 path handling and existing Git credential-helper inheritance.
- Keep the source checkout HEAD and status unchanged during diagnostic publication.

---

### Task 1: Stabilize diagnostics Git messages at the subprocess boundary

**Files:**
- Modify: `tests/integration/test_diagnostics_git.py`
- Modify: `src/authorial_flow/diagnostics.py`

**Interfaces:**
- Consumes: `_prepare_diagnostics_checkout(checkout: Path, *, remote_url: str, branch: str, timeout_seconds: float) -> str` and `_git_result(args: Sequence[str], *, cwd: Path, timeout_seconds: float, check: bool = True) -> subprocess.CompletedProcess[str]`.
- Produces: the same interfaces, with Git children receiving stable English messages and the caller's effective character-type locale.

- [ ] **Step 1: Write the failing French-locale/non-ASCII-path regression**

Add this test to `tests/integration/test_diagnostics_git.py`:

```python
def test_git_transport_stabilizes_messages_without_losing_utf8_paths(
    tmp_path: Path, monkeypatch,
) -> None:
    import authorial_flow.diagnostics as diagnostics

    checkout = tmp_path / "Téléchargements" / "diagnostics-checkout"
    checkout.mkdir(parents=True)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text(
        """#!/bin/sh
if [ "$1" = "fetch" ]; then
    if [ -z "${LC_ALL+x}" ] && [ "$LC_MESSAGES" = "C" ] && [ "$LANGUAGE" = "C" ] && [ "$LC_CTYPE" = "fr_FR.UTF-8" ]; then
        printf "%s\\n" "fatal: couldn't find remote ref refs/heads/diagnostics/authorial-flow-graph-v1" >&2
    else
        printf "%s\\n" "fatal: référence distante introuvable" >&2
    fi
    exit 128
fi
exit 0
""",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("LC_ALL", "fr_FR.UTF-8")
    monkeypatch.delenv("LC_CTYPE", raising=False)
    monkeypatch.setenv("LC_MESSAGES", "fr_FR.UTF-8")
    monkeypatch.setenv("LANGUAGE", "fr")

    mode = diagnostics._prepare_diagnostics_checkout(
        checkout,
        remote_url="https://github.com/u-dont-existDOTcom/pangram-humanization-lab.git",
        branch=DIAGNOSTICS_BRANCH,
        timeout_seconds=10,
    )

    assert mode == "orphan"
    assert os.environ["LC_ALL"] == "fr_FR.UTF-8"
```

- [ ] **Step 2: Run the regression and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_diagnostics_git.py::test_git_transport_stabilizes_messages_without_losing_utf8_paths -q
```

Expected: FAIL with `subprocess.CalledProcessError` because the existing child inherits the French `LC_ALL`, emits the localized missing-ref sentence, and does not enter the orphan path.

- [ ] **Step 3: Implement the minimal child-only locale normalization**

In `_git_result`, construct the child environment as follows before `subprocess.run`:

```python
    environment = {**os.environ}
    effective_ctype = (
        environment.get("LC_CTYPE")
        or environment.get("LC_ALL")
        or environment.get("LANG")
    )
    environment.pop("LC_ALL", None)
    if effective_ctype:
        environment["LC_CTYPE"] = effective_ctype
    environment.update(
        {
            "LC_MESSAGES": "C",
            "LANGUAGE": "C",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ASKPASS": "false",
            "SSH_ASKPASS": "false",
            "GIT_CONFIG_NOSYSTEM": "1",
        }
    )
```

Do not modify the parent `os.environ` and do not change command arguments, timeouts, output capture, or failure classification.

- [ ] **Step 4: Run the regression and diagnostics integration suite to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_diagnostics_git.py::test_git_transport_stabilizes_messages_without_losing_utf8_paths -q
.venv/bin/python -m pytest tests/integration/test_diagnostics_git.py tests/integration/test_diagnostics_end_to_end.py -q
```

Expected: the regression passes; all diagnostics integration tests pass.

- [ ] **Step 5: Run privacy and source-isolation regressions**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_diagnostics.py tests/integration/test_diagnostics_git.py tests/integration/test_diagnostics_end_to_end.py -q
git status --short
```

Expected: all selected tests pass; only the intended test, implementation, design, and plan files differ from the baseline.

- [ ] **Step 6: Commit the focused fix**

```bash
git add tests/integration/test_diagnostics_git.py src/authorial_flow/diagnostics.py
git commit -m "fix: stabilize diagnostics Git messages"
```

---

### Task 2: Verify the completed transport correction

**Files:**
- Modify: `docs/2026-08-12-automatic-diagnostics-publication-review.md`

**Interfaces:**
- Consumes: the unchanged diagnostics CLI and Git transport interfaces from Task 1.
- Produces: a durable verification record containing only commands, typed outcomes, counts, hashes, and commit identifiers.

- [ ] **Step 1: Run the complete deterministic suite**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: all tests pass with zero failures.

- [ ] **Step 2: Run the clean release build/compile gate**

Run:

```bash
release_zip="$(mktemp --suffix=.zip)"
.venv/bin/python scripts/build_release.py --repo . --out "$release_zip" --clean-zip-compile
sha256sum "$release_zip"
```

Expected: `verification=PASS`, the project-instruction character count remains below 8,000, and a release SHA-256 is printed. The temporary ZIP is not a user deliverable.

- [ ] **Step 3: Confirm protected trees and worktree hygiene**

Run:

```bash
git diff --quiet cc910f53525d2af7a24175bc28c4282d17732c14 -- project policy
git diff --check
git status --short
```

Expected: the protected-tree diff exits zero; no whitespace errors; only the intended review update remains uncommitted.

- [ ] **Step 4: Record exact verification evidence**

Append the exact test count/runtime, release verification fields, release SHA-256, protected-tree result, live corrected-probe outcome when available, and diagnostics-branch inspection result to `docs/2026-08-12-automatic-diagnostics-publication-review.md`. Do not include raw stderr, environment values, credentials, full local paths, or diagnostic record bodies.

- [ ] **Step 5: Commit the verification record**

```bash
git add docs/2026-08-12-automatic-diagnostics-publication-review.md
git commit -m "docs: verify locale-stable diagnostics transport"
```
