# Fixed Pangram Batch via GitHub Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a generic, resumable fixed-batch Pangram runner and use it to execute the three oxytocin minimal-pair variants from GitHub Actions with the repository secret.

**Architecture:** A JSON spec holds exact texts. A small `pangram_lab.fixed_batch` module validates and executes them through the existing PangramClient/PangramCache/GitSync checkpoint path. A path-filtered branch workflow runs tests first, then the live batch, and result/cache commits do not retrigger the workflow.

**Tech Stack:** Python 3.11, pytest, existing `pangram_lab` package, GitHub Actions.

## Global Constraints

- Pangram model must be explicit `pangram-4`; terminal version must be `4.0`.
- Do not retry ambiguous POSTs.
- Reuse exact-text cache records.
- Push task-id/result checkpoints before another paid call.
- Never print or commit `PANGRAM_API_KEY`.
- Current live batch has exactly R1S0, R0S1, R1S1; second batch waits for first-batch interpretation.

---

### Task 1: Exact fixed-batch spec parser

**Files:**
- Create: `tests/test_fixed_batch.py`
- Create: `src/pangram_lab/fixed_batch.py`

**Interfaces:**
- Produces: `load_spec(path: Path, max_variants: int = 8) -> dict`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
import json
import pytest
from pangram_lab.fixed_batch import load_spec


def test_load_spec_preserves_exact_order_and_text(tmp_path: Path):
    p = tmp_path / "batch.json"
    p.write_text(json.dumps({
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "x",
        "variants": [
            {"id": "A", "text": "first  text"},
            {"id": "B", "text": "second"},
        ],
    }), encoding="utf-8")
    spec = load_spec(p)
    assert [v["id"] for v in spec["variants"]] == ["A", "B"]
    assert spec["variants"][0]["text"] == "first  text"


def test_load_spec_rejects_duplicate_ids(tmp_path: Path):
    p = tmp_path / "batch.json"
    p.write_text(json.dumps({
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "x",
        "variants": [{"id": "A", "text": "one"}, {"id": "A", "text": "two"}],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_spec(p)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fixed_batch.py -v`
Expected: FAIL during import because `pangram_lab.fixed_batch` does not exist.

- [ ] **Step 3: Write minimal implementation**

Implement JSON validation preserving text bytes-as-decoded, original order, unique non-empty ids, non-empty text, supported format, experiment id, and max variant count.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_fixed_batch.py -v`
Expected: PASS.

- [ ] **Step 5: Run full suite**

Run: `pytest -q`
Expected: all existing and new tests PASS.

### Task 2: Resumable batch execution

**Files:**
- Modify: `src/pangram_lab/fixed_batch.py`
- Create: `scripts/run_fixed_batch.py`
- Extend: `tests/test_fixed_batch.py`

**Interfaces:**
- Produces: `run_batch(spec, *, client, cache, sync, output_path) -> dict`

- [ ] **Step 1: Write failing test**

Use a fake client whose `detect_cached` records `(text, measurement_key)` calls and returns fixed Pangram-like result dicts. Assert variant order, measurement keys `<experiment_id>_<variant_id>`, SHA-256 output, and aggregate output JSON.

- [ ] **Step 2: Verify RED**

Run the new test and confirm failure because `run_batch` is missing.

- [ ] **Step 3: Implement minimal runner**

Sequentially call `client.detect_cached`, calculate exact-text SHA-256, write aggregate JSON after every successful variant, and return the aggregate.

- [ ] **Step 4: Verify GREEN and full suite**

Run targeted test, then `pytest -q`.

### Task 3: Oxytocin experiment spec and Actions workflow

**Files:**
- Create: `experiments/romance-oxytocin-r1-2026-08-12.json`
- Create: `.github/workflows/pangram-fixed-batch.yml`

**Interfaces:**
- Consumes: `PANGRAM_API_KEY` repository Actions secret.
- Produces: `state/experiments/romance-oxytocin-r1-2026-08-12-results.json` plus cache records.

- [ ] **Step 1: Add exact three-variant JSON spec**

Include R1S0, R0S1, R1S1 exactly as recorded in the state incident file, no normalization.

- [ ] **Step 2: Add workflow**

Workflow checks out with persisted credentials, grants `contents: write`, installs `.[test]`, runs `pytest -q`, then runs the batch script with `PANGRAM_API_KEY`. Configure git identity before the detector step so `GitSync.sync` can checkpoint and push.

- [ ] **Step 3: Trigger on dedicated branch/path only**

Use push branch `automation/pangram-fixed-batch` and paths covering the workflow, spec, fixed-batch module/script, and its test. Do not include `cache/**` or `state/experiments/**` so evidence pushes cannot recursively spend calls.

- [ ] **Step 4: Observe live run**

Verify unit/full tests pass, auth probe reaches Pangram task API, three variants are submitted/resumed/cache-hit as appropriate, every terminal result is version 4.0, and the result file is committed.

### Task 4: Interpret and preserve learning

**Files:**
- Update: `state/ROMANCE-OXYTOCIN-MINIMAL-PAIR-BATCH-2026-08-12.md`
- Update: `state/WORKING-LESSONS.md` only if replicated evidence justifies a portable lesson.

- [ ] **Step 1: Read exact R1S0/R0S1/R1S1 results**
- [ ] **Step 2: Apply the predeclared interpretation matrix**
- [ ] **Step 3: Repeat the smallest changed Human cell once if a first-batch flip occurs**
- [ ] **Step 4: Run C1/C2/C3 only if first batch fails to isolate the effect**
- [ ] **Step 5: Commit the exact evidence and bounded conclusion**
