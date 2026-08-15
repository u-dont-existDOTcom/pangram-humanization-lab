# Romance Current-Master Assembly Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministically assemble the exact current Romance working master from the immutable Aug. 13 baseline plus only the later authoritative owner/editorial replacements, with fail-closed anchors, provenance hashes, a diff, and preservation checks.

**Architecture:** Keep the Aug. 13 article bytes as an immutable private baseline and describe the accepted changes in a small JSON assembly spec. A stdlib-only Python assembler applies exact `replace_between`, `replace_section`, `replace_exact`, and `delete_exact` operations; every operation must match exactly once or the run fails. The assembler emits the current Markdown master, an operation/hash manifest, and a unified diff, while tests enforce native-object, heading, name, and owner-lock preservation.

**Tech Stack:** Python 3.10+ standard library, pytest, Git/GitHub Actions already present in `pangram-humanization-lab`.

## Global Constraints

- Work only on `agent/romance-current-master-assembly-2026-08-15`; do not edit `main` directly.
- The repository is private; do not move Romance prose into public `joel-articles` until a fresh metadata check reports `visibility: private`.
- Baseline source is the exact existing Git blob `b6a6d73b3a7e7e93efc31bc7e755f04b9d57df97` from `task/romance-full-human-2026-08-13-r1:inputs/romance-reconstructed-2026-08-13-sha18ed9fa.md`.
- No fuzzy matching, no prose cleanup, no detector-driven rewriting during assembly.
- Current explicit owner wording outranks historical detector labels and assistant candidates.
- Preserve links, headings, native-object placeholders, severe-claim agency, `H.`/`H.D.` identity, chronology, and untouched baseline bytes.
- Casual Sex/Situationship remains the locked baseline section; the later assistant structural rearrangement is evidence only and must not be imported.
- Tough Love upstream prose remains baseline owner-final; only the closing is replaced.
- Talk uses the current richer owner-preferred/editorially preferred realization despite the unresolved current Pangram result; no additional Talk detector calls in this audit.

---

### Task 1: Specify fail-closed assembly behavior with tests

**Files:**
- Create: `tests/test_romance_current_assembly.py`
- Later create: `scripts/assemble_romance_current.py`

**Interfaces:**
- Consumes: `apply_operations(text: str, operations: list[dict], root: pathlib.Path) -> tuple[str, list[dict]]`
- Produces: exact-match operations and provenance records used by the CLI in Task 2.

- [ ] **Step 1: Write failing unit tests**

Create tests that import `scripts.assemble_romance_current` and require:

```python
def test_replace_exact_requires_one_match(tmp_path): ...
def test_delete_exact_requires_one_match(tmp_path): ...
def test_replace_between_preserves_anchors(tmp_path): ...
def test_replace_section_replaces_start_through_before_next_heading(tmp_path): ...
def test_operation_manifest_records_old_and_new_sha256(tmp_path): ...
```

Each test uses tiny real strings and asserts that zero matches or multiple matches raise `AssemblyError` rather than guessing.

- [ ] **Step 2: Run the targeted tests and verify RED**

Run:

```bash
python -m pytest tests/test_romance_current_assembly.py -q
```

Expected: collection/import failure because `scripts/assemble_romance_current.py` does not exist yet. This is the intended RED state.

- [ ] **Step 3: Commit only the plan and failing tests**

```bash
git add docs/superpowers/plans/2026-08-15-romance-current-master-assembly.md tests/test_romance_current_assembly.py
git commit -m "test: specify Romance master assembly"
```

### Task 2: Implement the minimal deterministic assembler

**Files:**
- Create: `scripts/assemble_romance_current.py`
- Test: `tests/test_romance_current_assembly.py`

**Interfaces:**
- `class AssemblyError(RuntimeError)`
- `sha256_text(text: str) -> str`
- `apply_operations(text: str, operations: list[dict], root: pathlib.Path) -> tuple[str, list[dict]]`
- CLI arguments: `--baseline`, `--spec`, `--output`, `--manifest`, `--diff`

Supported operation schemas:

```json
{"id":"...","type":"replace_exact","old":"...","replacement_file":"..."}
{"id":"...","type":"delete_exact","old":"..."}
{"id":"...","type":"replace_between","start_anchor":"...","end_anchor":"...","replacement_file":"..."}
{"id":"...","type":"replace_section","start_anchor":"# Heading","end_anchor":"# Next heading","replacement_file":"..."}
```

`replace_between` preserves both anchors and replaces only the interior. `replace_section` replaces from the start anchor through the byte before the unique end anchor; the replacement file therefore contains the complete replacement section including its heading. All anchors/old spans must occur exactly once.

- [ ] **Step 1: Implement only enough code to satisfy Task 1 tests**

Use `pathlib`, `hashlib`, `json`, `argparse`, and `difflib`; no dependencies. Each operation record must include `id`, `type`, `old_sha256`, `new_sha256`, and byte counts.

- [ ] **Step 2: Run targeted tests and verify GREEN**

```bash
python -m pytest tests/test_romance_current_assembly.py -q
```

Expected: all Task 1 tests pass.

- [ ] **Step 3: Commit**

```bash
git add scripts/assemble_romance_current.py tests/test_romance_current_assembly.py
git commit -m "feat: add deterministic Romance assembler"
```

### Task 3: Add the exact private baseline, authoritative replacements, and assembly spec

**Files:**
- Create by reusing existing blob: `work/romance-current-assembly/baseline.md`
- Create: `work/romance-current-assembly/replacements/opening.md`
- Create: `work/romance-current-assembly/replacements/talk.md`
- Create: `work/romance-current-assembly/replacements/should.md`
- Create: `work/romance-current-assembly/replacements/flaws.md`
- Create: `work/romance-current-assembly/replacements/closing.md`
- Create: `work/romance-current-assembly/assembly-spec.json`
- Test: `tests/test_romance_current_assembly.py`

**Interfaces:**
- Baseline bytes are exactly the Aug. 13 source blob.
- Replacement files are verbatim authoritative/current text, not regenerated prose.
- Spec applies, in order: opening replacement; Love-tail deletion; Talk section replacement; Should section replacement; Flaws section replacement; five minimal Crucible edits/deletions; Tough Love closing replacement.

- [ ] **Step 1: Add failing integration tests before adding assembly data**

Add tests requiring these files and asserting:

```python
def test_full_assembly_preserves_all_native_markers(): ...
def test_full_assembly_preserves_hd_and_does_not_substitute_hale(): ...
def test_full_assembly_contains_exact_owner_opening_and_closing(): ...
def test_full_assembly_removes_superseded_aftercare(): ...
def test_locked_casual_section_is_byte_identical_to_baseline(): ...
def test_untouched_prefix_before_share_and_native_button_survive(): ...
```

For the Casual lock test, extract the bytes from `## Can Casual Sex or a Situationship Actually Be Honest?` through immediately before `---\n\n# Should you be in a relationship at all?` in baseline and output and require exact equality.

- [ ] **Step 2: Run tests and verify RED**

```bash
python -m pytest tests/test_romance_current_assembly.py -q
```

Expected: failures because baseline/spec/replacement files are absent.

- [ ] **Step 3: Add baseline blob, exact replacement files, and spec**

Crucible operations must preserve baseline Markdown links/native preview and `H.D.` while applying only these approved textual changes:

1. delete the explanatory `I didn’t know what a crucible was...` paragraph;
2. replace the entitlement/mind-reading paragraph with the passing local-function realization;
3. replace the peer-counseling consequence paragraph while preserving its link;
4. replace `The body has to be included too.` with `I also have to deal with what happens in my body.`;
5. delete the final `A relationship can grow somebody...` summary paragraph.

Do not replace the entire Crucible section from detector plaintext.

- [ ] **Step 4: Run targeted tests and verify GREEN**

```bash
python -m pytest tests/test_romance_current_assembly.py -q
```

Expected: all assembly tests pass.

- [ ] **Step 5: Commit**

```bash
git add work/romance-current-assembly tests/test_romance_current_assembly.py
git commit -m "data: bind current Romance assembly authority"
```

### Task 4: Generate and verify the exact current master

**Files:**
- Generate: `work/romance-current-assembly/current-master.md`
- Generate: `work/romance-current-assembly/assembly-manifest.json`
- Generate: `work/romance-current-assembly/current-master.diff`
- Modify: `tests/test_romance_current_assembly.py` only if an assembly invariant exposed by the real baseline needs a regression test first.

**Interfaces:**
- `current-master.md` is the exact assembled Markdown candidate.
- `assembly-manifest.json` records baseline SHA-256, final SHA-256, spec SHA-256, operation records, and output byte count.
- `current-master.diff` is the complete unified diff against the Aug. 13 baseline.

- [ ] **Step 1: Run assembler**

```bash
python scripts/assemble_romance_current.py \
  --baseline work/romance-current-assembly/baseline.md \
  --spec work/romance-current-assembly/assembly-spec.json \
  --output work/romance-current-assembly/current-master.md \
  --manifest work/romance-current-assembly/assembly-manifest.json \
  --diff work/romance-current-assembly/current-master.diff
```

Expected: exit 0 and deterministic hashes printed.

- [ ] **Step 2: Re-run and prove determinism**

Run the same command twice and verify `git diff --exit-code` for the three generated outputs on the second run.

- [ ] **Step 3: Run focused and full repository tests**

```bash
python -m pytest tests/test_romance_current_assembly.py -q
python -m pytest -q
python scripts/audit_repository_controls.py
```

Expected: all pass with no assembly/provenance failure.

- [ ] **Step 4: Cold-audit the literal generated master twice**

Audit 1: semantic sanity, actor/action/object, chronology, claims/certainty, headings, native objects, links, names, owner locks, and source fidelity.

Audit 2: curious-reader chain, duplicate conclusions, explanatory aftercare, local repetition, real stopping points, and whether any downstream prose is compensating for an upstream defect.

If a legitimate weakness appears, fix the authoritative replacement/spec only after classifying whether it is an owner-authorial issue, fidelity bug, or assembler bug; assembler bugs require a failing regression test first.

- [ ] **Step 5: Commit generated exact artifacts**

```bash
git add work/romance-current-assembly/current-master.md \
        work/romance-current-assembly/assembly-manifest.json \
        work/romance-current-assembly/current-master.diff
git commit -m "state: materialize current Romance master"
```

### Task 5: Review, merge, and prepare final detector boundary

**Files:**
- No new production files unless review finds a tested defect.

**Interfaces:**
- Pull request into private `pangram-humanization-lab:main` contains only private assembly tooling/state.
- Final whole-article detector input must be derived from the exact generated master, not reconstructed from chat or stale files.

- [ ] **Step 1: Open PR and verify hosted checks**

Confirm repository workflow policy, lesson integrity where applicable, and complete test suite succeed on the exact PR head.

- [ ] **Step 2: Review diff for authority/losslessness**

Confirm only intended sections changed; the locked Casual section and untouched owner-final sections remain byte-identical to baseline; native-object inventory is unchanged; `H.D.` remains in Crucible.

- [ ] **Step 3: Merge only after checks pass**

Use squash merge with expected-head SHA.

- [ ] **Step 4: Use the merged exact master for the final reader-visible Pangram certification**

Do not spend another Talk section call; the six-call Talk cap remains a recorded suspension. A whole-article call is a distinct final-deliverable boundary and should use the exact reader-visible assembled master after the two cold audits.
