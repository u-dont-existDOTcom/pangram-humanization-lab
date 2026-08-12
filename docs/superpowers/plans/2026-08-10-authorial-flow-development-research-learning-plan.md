# Authorial Flow Graph v1 — Development, Research, and Learning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the working Core Runtime so `humanize` can diagnose provenance/mode, repair bad thought through P3/P4 or bounded research, separate faithful owner position from better-reasoned alternatives, learn from sparse owner judgments with scoped promotion, and surface only the smallest necessary owner decision.

**Architecture:** Keep Basic Thought-Flow as a distinct generation subgraph. A semantic-sanity router may temporarily leave it for developmental/research work, then return with a revised authority representation. Learning is an append-only owner-authority subsystem separate from model-generated hypotheses; research is evidence/provenance infrastructure, never silent belief substitution.

**Tech Stack:** Core Runtime stack plus `httpx`; optional search-provider credentials/adapters. No browser UI and no required DSPy/GEPA dependency.

## Global Constraints

- Joel Articles task modes P0/P1/P2/P2S/P3/P4 are the authority model; do not invent a conflicting public taxonomy.
- Plain `humanize` defaults to automatic diagnosis and may explore conservative + developmental + research-informed candidates.
- Exploration authority does not equal publication authority; changed owner position remains a candidate until owner adoption.
- P2S never auto-researches or changes propositions/source choices.
- Research runs only when resolving the uncertainty could materially change the thought.
- Source support, system inference, and owner position are separate fields.
- Machine reasoning/research is exhausted before owner interrupt; questions are narrow and materially authorial.
- Every owner judgment controls the current project immediately, but cross-project promotion is conservative.
- Model-generated positive examples cannot validate model-generated rules.
- Local edge/stop labels and whole-passage precomputed-shape labels are separate learning targets.
- Normally present one recommended candidate; present multiple only for materially different thought routes/authorial choices.
- Better-reasoned alternatives never enter Joel's byline without adoption.

---

## File Map

- `src/authorial_flow/modes.py` — task-mode enum, request parsing, permission matrix.
- `src/authorial_flow/source_provenance.py` — owner/AI/mixed/source-pool provenance classification.
- `src/authorial_flow/nodes/classify_source.py` — source provenance node.
- `src/authorial_flow/nodes/choose_mode.py` — least-invasive mode inference.
- `src/authorial_flow/nodes/semantic_sanity.py` — thought validity and escalation reasons.
- `src/authorial_flow/nodes/developmental.py` — P3/P4 architecture repair/reconstruction.
- `src/authorial_flow/research/base.py` — provider-neutral research interfaces.
- `src/authorial_flow/research/discovery.py` — search provider orchestration.
- `src/authorial_flow/research/fetch.py` — direct fetch + content provenance.
- `src/authorial_flow/research/evidence.py` — claim/source/access-role records.
- `src/authorial_flow/nodes/research.py` — bounded research loop.
- `src/authorial_flow/candidates.py` — candidate roles/ranking/presentation extensions.
- `src/authorial_flow/learning.py` — append-only owner learning store + scope ladder.
- `src/authorial_flow/nodes/owner_interrupt.py` — narrow authorial question expansion.
- `src/authorial_flow/routing.py`, `graph.py` — escalation/rejoin branches.
- `tests/unit/`, `tests/integration/`, `tests/regression/` — mode, research, learning, interruption tests.

---

### Task 1: Task Modes, Permission Matrix, and Source Provenance Classification

**Files:**
- Create: `src/authorial_flow/modes.py`
- Create: `src/authorial_flow/source_provenance.py`
- Create: `src/authorial_flow/nodes/classify_source.py`
- Create: `src/authorial_flow/nodes/choose_mode.py`
- Create: `src/authorial_flow/prompts/source_provenance.md`
- Test: `tests/unit/test_modes_provenance.py`

**Interfaces:**
- Produces: `TaskMode(StrEnum)` with P0/P1/P2/P2S/P3/P4.
- Produces: `SourceProvenance(StrEnum)` = OWNER_FINAL, OWNER_DRAFT, AI_FROM_OWNER_INPUTS, MIXED, SOURCE_POOL, RESEARCH_PROVISIONAL.
- Produces: `ModeDecision(mode, reason, substantive_permission, research_permission)`.

- [ ] **Step 1: Write failing mode tests**

```python
# tests/unit/test_modes_provenance.py
from authorial_flow.modes import TaskMode, choose_mode
from authorial_flow.source_provenance import SourceProvenance


def test_explicit_p2s_disables_research_and_substantive_change():
    d = choose_mode("P2S", SourceProvenance.AI_FROM_OWNER_INPUTS, semantic_sanity=True)
    assert d.mode is TaskMode.P2S
    assert d.research_permission is False
    assert d.substantive_permission is False


def test_plain_humanize_ai_draft_can_choose_p3():
    d = choose_mode("humanize", SourceProvenance.AI_FROM_OWNER_INPUTS, semantic_sanity=True)
    assert d.mode in {TaskMode.P2S, TaskMode.P3}
    assert d.reason


def test_owner_final_does_not_auto_escalate_without_defect():
    d = choose_mode("humanize", SourceProvenance.OWNER_FINAL, semantic_sanity=True)
    assert d.mode in {TaskMode.P1, TaskMode.P2, TaskMode.P2S}
```

- [ ] **Step 2: Implement enums and explicit-mode parsing**

Explicit P0–P4/P2S always wins unless a higher-priority lock makes the requested change illegal; that conflict must return `requires_owner_authority=True` rather than silently escalating.

- [ ] **Step 3: Implement provenance classifier schema/prompt**

The model sees source metadata + provenance clues, not detector output. It must distinguish “AI-generated from owner inputs” from “natural owner prose” and return evidence spans/reasons. A deterministic override file may pin provenance for known project fixtures.

- [ ] **Step 4: Implement default `humanize` decision rules**

Use conservative deterministic bounds around model classification: owner-final → no substantive escalation by default; source pool → P4; AI-from-owner-inputs → P3 if thought repair warranted, otherwise P2S; mixed → P3 when substantive architecture is implicated.

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_modes_provenance.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/authorial_flow/{modes.py,source_provenance.py,nodes/classify_source.py,nodes/choose_mode.py,prompts/source_provenance.md} tests/unit/test_modes_provenance.py
git commit -m "feat: classify provenance and choose article modes"
```

---

### Task 2: Semantic Sanity Node and Escalation Contract

**Files:**
- Create: `src/authorial_flow/nodes/semantic_sanity.py`
- Create: `src/authorial_flow/prompts/semantic_sanity.md`
- Modify: `src/authorial_flow/routing.py`
- Modify: `src/authorial_flow/state.py`
- Test: `tests/unit/test_semantic_sanity_routing.py`

**Interfaces:**
- Produces: `SemanticSanityResult(status, defect_types, material_questions, research_trigger, owner_question, recommended_escalation)`.
- `recommended_escalation` ∈ BASIC, P3, P4, RESEARCH, OWNER.

- [ ] **Step 1: Write routing tests**

```python
# tests/unit/test_semantic_sanity_routing.py
from authorial_flow.nodes.semantic_sanity import SemanticSanityResult
from authorial_flow.routing import route_after_semantic_sanity


def test_bad_ai_architecture_routes_to_p4_not_writer():
    result = SemanticSanityResult(status="FAIL", defect_types=["wrong_thought"], recommended_escalation="P4")
    assert route_after_semantic_sanity(result) == "developmental"


def test_source_choice_uncertainty_routes_to_research():
    result = SemanticSanityResult(status="FAIL", defect_types=["source_role"], research_trigger=True, recommended_escalation="RESEARCH")
    assert route_after_semantic_sanity(result) == "research"
```

- [ ] **Step 2: Implement semantic sanity prompt**

Require explicit checks for claim/question, hidden premise already answering question, actor→action→object, chronology, causality, certainty, attribution, heading function, source-role fit, and whether passage should survive. It may not draft replacement prose.

- [ ] **Step 3: Implement routing rules**

If explicit P2S and sanity failure is substantive, do not repair silently: return `OWNER`/report boundary. Under default `humanize`, route P3/P4/research automatically according to defect class.

- [ ] **Step 4: Store escalation evidence in state**

Add `semantic_sanity_ref`, `escalation_reason`, `escalation_count`, and `resolved_concept_ref`; keep original source immutable.

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_semantic_sanity_routing.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/authorial_flow/{state.py,routing.py,nodes/semantic_sanity.py,prompts/semantic_sanity.md} tests/unit/test_semantic_sanity_routing.py
git commit -m "feat: route semantic sanity failures explicitly"
```

---

### Task 3: Mode-Specific P0/P1/P2/P2S Execution Paths

**Files:**
- Create: `src/authorial_flow/nodes/conservative.py`
- Create: `src/authorial_flow/prompts/p0_report.md`
- Create: `src/authorial_flow/prompts/p1_copyedit.md`
- Create: `src/authorial_flow/prompts/p2_lineedit.md`
- Create: `src/authorial_flow/prompts/p2s_reconstruct.md`
- Modify: `src/authorial_flow/routing.py`
- Modify: `src/authorial_flow/graph.py`
- Test: `tests/integration/test_mode_execution.py`

**Interfaces:**
- Produces: `ConservativeResult(candidate_ref, change_ledger_ref, hard_violations, mode)`.
- P0 returns analysis/report artifact only and cannot enter writer/detector publication-candidate path.
- P1/P2/P2S produce candidates whose allowed-delta validator is mode-specific.

- [ ] **Step 1: Write mode-boundary integration tests**

```python
# tests/integration/test_mode_execution.py

def test_p0_never_rewrites(fake_graph):
    result = fake_graph.run(requested_operation="P0")
    assert result.report_ref
    assert result.candidate_ref is None
    assert result.writer_call_count == 0


def test_p2s_rejects_substantive_delta(fake_graph):
    result = fake_graph.run(
        requested_operation="P2S",
        fake_candidate_change={"claim_deleted": "c1"},
    )
    assert result.status == "MODE_VIOLATION"
    assert result.research_call_count == 0


def test_p1_rejects_paragraph_rearchitecture(fake_graph):
    result = fake_graph.run(requested_operation="P1", fake_candidate_change={"paragraph_order_changed": True})
    assert result.status == "MODE_VIOLATION"
```

- [ ] **Step 2: Implement P0 report-only path**

P0 can call audit/fingerprint/research components only when the request permits them, but it never creates publication prose or enters Pangram candidate search unless the explicit task itself is detector analysis of supplied text. Record findings as artifacts and route END/owner review appropriately.

- [ ] **Step 3: Implement P1 allowed-delta validator**

Allow spelling, grammar, punctuation, spacing, literal agreement, broken-link correction, and obvious ambiguity repair only. Reject claim/certainty/order/paragraph architecture/emoji/link-anchor changes unless explicitly authorized by the request.

- [ ] **Step 4: Implement P2 allowed-delta validator**

Allow clarity/rhythm/repetition/local voice changes with smallest effective edits; preserve argument, examples, order, emotional temperature, memorable/locked lines, links/media, and substantive relations.

- [ ] **Step 5: Implement P2S reconstruction path**

Reuse semantic sanity + architecture card + Thought-Flow realization, but every proposition/factual assignment/allegation/certainty/recommendation/link/media/coined term/catchphrase/personal-history unit is `must_preserve`. Research permission is false. If semantic sanity identifies a substantive contradiction that cannot be resolved without changing meaning, emit the narrow report/owner-authority boundary instead of silently switching to P3.

- [ ] **Step 6: Add exact change-ledger output**

For every candidate, write mode, source hash, candidate hash, claim/certainty/actor/causal delta summary, and whether each delta is allowed. Mode violation blocks cold-audit/Pangram progression.

- [ ] **Step 7: Run tests**

Run: `pytest tests/integration/test_mode_execution.py -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/authorial_flow/{graph.py,routing.py,nodes/conservative.py,prompts/p0_report.md,prompts/p1_copyedit.md,prompts/p2_lineedit.md,prompts/p2s_reconstruct.md} tests/integration/test_mode_execution.py
git commit -m "feat: enforce Joel Articles operation levels"
```

---

### Task 4: Developmental P3/P4 Reconstruction Node

**Files:**
- Create: `src/authorial_flow/nodes/developmental.py`
- Create: `src/authorial_flow/prompts/developmental_architecture.md`
- Create: `src/authorial_flow/prompts/p4_reconstruction.md`
- Test: `tests/unit/test_developmental_authority.py`

**Interfaces:**
- Produces: `DevelopmentalResult(corrected_units, architecture_card_ref, faithful_position_ref, alternative_ref, unresolved_authorial)`.
- Consumes authority units and source pool; never overwrites original unit provenance.

- [ ] **Step 1: Write authority-preservation tests**

```python
# tests/unit/test_developmental_authority.py
from authorial_flow.authority import Authority, AuthorityUnit
from authorial_flow.nodes.developmental import validate_developmental_result


def test_owner_locked_unit_cannot_be_dropped():
    locked = [AuthorityUnit(id="u1", text="owner fact", authority=Authority.OWNER_LOCKED)]
    proposed = []
    errors = validate_developmental_result(locked, proposed)
    assert any("u1" in e for e in errors)


def test_ai_provisional_unit_may_be_omitted_with_reason():
    units = [AuthorityUnit(id="u2", text="AI bridge", authority=Authority.AI_PROVISIONAL)]
    proposed = [{"id": "u2", "disposition": "omit", "reason": "unsupported bridge"}]
    assert validate_developmental_result(units, proposed) == []
```

- [ ] **Step 2: Implement architecture-card schema**

Fields mirror Joel Articles: heading promise, real pressure, reader stake, controlling claim/certainty, intellectual/lived route, actor/action/object, causality/chronology, source landscape/unequal roles, strongest complication, governing movement, paragraph jobs, stopping point, exact-language reasons.

- [ ] **Step 3: Implement P3 repair behavior**

P3 may reorder, expand, compress, replace AI-provisional evidence roles, and propose new material. Every substantive delta gets an explicit origin/disposition record. Owner position changes remain `candidate_only=True` until adopted.

- [ ] **Step 4: Implement P4 reconstruction behavior**

P4 reconstructs from source pool + owner authority units, not inherited sentence sequence. It returns a corrected conceptual substrate/architecture for Thought-Flow, not a final paragraph that bypasses the Thought-Flow experiment.

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_developmental_authority.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/authorial_flow/nodes/developmental.py src/authorial_flow/prompts/{developmental_architecture.md,p4_reconstruction.md} tests/unit/test_developmental_authority.py
git commit -m "feat: add developmental and reconstruction escalation"
```

---

### Task 5: Provider-Neutral Bounded Research and Evidence Provenance

**Files:**
- Create: `src/authorial_flow/research/__init__.py`
- Create: `src/authorial_flow/research/base.py`
- Create: `src/authorial_flow/research/discovery.py`
- Create: `src/authorial_flow/research/fetch.py`
- Create: `src/authorial_flow/research/evidence.py`
- Create: `src/authorial_flow/nodes/research.py`
- Create: `tests/unit/test_research_provenance.py`
- Create: `tests/integration/test_research_node.py`

**Interfaces:**
- `ResearchProvider.search(query: str, limit: int) -> list[SearchHit]`
- `Fetcher.fetch(url: str) -> RetrievedSource`
- `EvidenceRecord(source_ref, access_level, primary_status, supports, resists, system_inference)`
- `research_node` returns resolved concept/ref or provider/missing-author ambiguity.

- [ ] **Step 1: Write provenance tests**

```python
# tests/unit/test_research_provenance.py
from authorial_flow.research.evidence import EvidenceRecord


def test_evidence_separates_source_support_from_inference():
    r = EvidenceRecord(
        source_ref="sha:1", access_level="full_text", primary_status="primary",
        supports=["AN 6.63 states X"], resists=[], system_inference=["This may bear on free will"]
    )
    assert r.supports != r.system_inference
```

- [ ] **Step 2: Implement provider-neutral models**

Use Pydantic models for `SearchHit`, `RetrievedSource`, `EvidenceRecord`, `ResearchQuestion`, and `ResearchSummary`. Access level enum: FULL_TEXT, ABSTRACT, SNIPPET, SECONDHAND.

- [ ] **Step 3: Implement two v1 discovery paths**

1. `DirectURLProvider` for URLs already present in source/research question.
2. `BraveSearchProvider` enabled only when `BRAVE_SEARCH_API_KEY` exists; provider key stays controller-side and is never passed to Claude/Codex.

If no discovery provider is available and research is materially required, classify `provider_unavailable` as machine/credential boundary, not an authorial question. Direct URL fetching remains available without search credentials.

- [ ] **Step 4: Implement fetcher with content limits and canonical provenance**

Use `httpx.Client(follow_redirects=True, timeout=30)`. Store final URL, response headers, retrieval time, body hash, MIME type, and access classification. Do not parse JS-rendered pages in v1; mark access limitation.

- [ ] **Step 5: Implement bounded research node**

Research plan first states exact uncertainty + material consequence. Cap discovery queries and fetched sources from config. Prefer primary/direct hits in model ranking. Stop when the specific question is stable; do not broaden into a literature review.

- [ ] **Step 6: Test that research cannot become owner belief**

Integration fake returns evidence favoring a different conclusion. Assert node outputs `better_reasoned_alternative_ref` and leaves `faithful_position_ref`/owner authority unchanged.

- [ ] **Step 7: Run tests**

Run: `pytest tests/unit/test_research_provenance.py tests/integration/test_research_node.py -q`

Expected: PASS without external network via mock transport.

- [ ] **Step 8: Commit**

```bash
git add src/authorial_flow/research src/authorial_flow/nodes/research.py tests/unit/test_research_provenance.py tests/integration/test_research_node.py
git commit -m "feat: add bounded provenance-aware research"
```

---

### Task 6: Candidate Roles, Blind Editorial Ranking, and Minimal Presentation

**Files:**
- Modify: `src/authorial_flow/candidates.py`
- Create: `src/authorial_flow/nodes/rank_candidates.py`
- Create: `src/authorial_flow/prompts/editorial_rank.md`
- Test: `tests/unit/test_candidate_presentation.py`

**Interfaces:**
- Candidate roles: CONSERVATIVE, DEVELOPMENTAL, RESEARCH_INFORMED, BETTER_REASONED_ALTERNATIVE.
- Produces: `EditorialRanking(order, winner_id, material_differences)` generated before Pangram visibility.
- Produces: `PresentationSet(recommended_id, alternatives[])`.

- [ ] **Step 1: Write presentation tests**

```python
# tests/unit/test_candidate_presentation.py
from authorial_flow.candidates import CandidateRecord, select_presentation


def test_cosmetic_variants_do_not_create_multiple_visible_options():
    a = CandidateRecord(id="a", text="A", role="CONSERVATIVE", material_route="route-1", editorial_score=9)
    b = CandidateRecord(id="b", text="B", role="CONSERVATIVE", material_route="route-1", editorial_score=8)
    shown = select_presentation([a, b])
    assert shown.recommended_id == "a"
    assert shown.alternatives == []


def test_materially_different_better_reasoned_route_can_be_shown():
    a = CandidateRecord(id="a", text="faithful", role="DEVELOPMENTAL", material_route="owner-position", editorial_score=9)
    b = CandidateRecord(id="b", text="alternative", role="BETTER_REASONED_ALTERNATIVE", material_route="evidence-diverges", editorial_score=9.2)
    shown = select_presentation([a, b])
    assert {shown.recommended_id, *shown.alternatives} == {"a", "b"}
```

- [ ] **Step 2: Extend candidate record with substantive-difference ledger**

Record claims added/removed, certainty changes, causal/evidence-role changes, source replacements, owner-position divergence, and route identity.

- [ ] **Step 3: Implement detector-blind editorial rank node**

Do not pass Pangram fields/artifact refs into rank prompt/input. Rank coherence, fidelity/authority, curious-reader/global shape, article function, stopping point, and owner preference when known.

- [ ] **Step 4: Implement minimal presentation selector**

One recommendation by default. Alternatives only when `material_route` or owner-position/source-role meaning differs. Limit total visible candidates to 3.

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_candidate_presentation.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/authorial_flow/candidates.py src/authorial_flow/nodes/rank_candidates.py src/authorial_flow/prompts/editorial_rank.md tests/unit/test_candidate_presentation.py
git commit -m "feat: rank thought routes before detector results"
```

---

### Task 7: Owner Learning Store and Conservative Scope Promotion

**Files:**
- Create: `src/authorial_flow/learning.py`
- Create: `tests/unit/test_learning_scope.py`
- Create: `tests/regression/test_learning_isolation.py`

**Interfaces:**
- Produces: `LearningKind` = LOCAL_EDGE, STOP_BEFORE, GLOBAL_PRECOMPUTED_SHAPE, MEANING_CORRECTION, VOICE_CORRECTION, SOURCE_ROLE_CORRECTION, RESEARCH_DIRECTION.
- Produces: `LearningScope` = PROJECT_AUTHORITY, REUSABLE_HYPOTHESIS, GENERAL_RULE, RETIRED.
- `LearningStore.append_owner_judgment(...) -> LearningRecord`
- `LearningStore.promote(record_id, evidence_refs, explicit_owner_confirmation=False)`.

- [ ] **Step 1: Write scope tests**

```python
# tests/unit/test_learning_scope.py
from authorial_flow.learning import LearningScope, LearningStore


def test_new_owner_label_is_project_authority_not_global(tmp_path):
    store = LearningStore(tmp_path)
    rec = store.append_owner_judgment(kind="LOCAL_EDGE", project_id="p", payload={"verdict": "FAIL"})
    assert rec.scope is LearningScope.PROJECT_AUTHORITY


def test_personal_fact_cannot_promote_to_style_rule(tmp_path):
    store = LearningStore(tmp_path)
    rec = store.append_owner_judgment(kind="MEANING_CORRECTION", project_id="p", payload={"personal_fact": True})
    result = store.promote(rec.id, evidence_refs=["case-2"])
    assert result.promoted is False
```

- [ ] **Step 2: Implement append-only JSONL + content-addressed record body**

`.state/learning/records.jsonl` is append-only. Updates/promotions create new events referencing prior record ID rather than rewriting history. Current view is derived by reducer.

- [ ] **Step 3: Implement promotion requirements**

To GENERAL_RULE require either explicit owner confirmation or repeated analogous owner-supported evidence including a held-out/validation record not used to invent the hypothesis. Model-generated synthetic positives cannot satisfy promotion.

- [ ] **Step 4: Implement dev/validation/locked-test partitions**

Store partition in each case. No automatic locked-test allocation until configured minimum counts; tests verify optimizer cannot read locked-test case bodies while generating hypotheses.

- [ ] **Step 5: Write writer-isolation regression**

Inject a learning store containing exact owner bad-edge candidate; assert writer input builder excludes all owner-gold/learning example text and includes only promoted abstract rule IDs/text when permitted.

- [ ] **Step 6: Run tests**

Run: `pytest tests/unit/test_learning_scope.py tests/regression/test_learning_isolation.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/authorial_flow/learning.py tests/unit/test_learning_scope.py tests/regression/test_learning_isolation.py
git commit -m "feat: persist scoped owner learning safely"
```

---

### Task 8: Narrow Owner Interrupts, Direct Label Capture, and Resume Routing

**Files:**
- Modify: `src/authorial_flow/nodes/owner_interrupt.py`
- Modify: `src/authorial_flow/routing.py`
- Modify: `src/authorial_flow/graph.py`
- Modify: `src/authorial_flow/cli.py`
- Test: `tests/integration/test_owner_learning_resume.py`

**Interfaces:**
- Owner interrupt payload types: FINAL_REVIEW, AUTHORIAL_AMBIGUITY, RESEARCH_ADOPTION.
- FINAL_REVIEW response kinds include ACCEPT, BAD_EDGE, STOP_BEFORE, GLOBAL_PRECOMPUTED_SHAPE, MEANING_ISSUE, VOICE_ISSUE, DEFER.

- [ ] **Step 1: Write bad-edge direct-learning integration test**

Run fake graph to final interrupt, resume with:

```json
{"kind":"BAD_EDGE","move_index":4,"note":"This does not follow."}
```

Assert learning store has PROJECT_AUTHORITY LOCAL_EDGE record, regression version increments, and graph routes back to regression/generation without requiring process restart.

- [ ] **Step 2: Write global-shape test**

Resume with `GLOBAL_PRECOMPUTED_SHAPE` when all local edges had passed. Assert separate learning kind; do not synthesize fake bad edge.

- [ ] **Step 3: Implement minimal-question generator for pre-final ambiguity**

If machine analysis cannot resolve an `OPEN_AUTHORIAL` unit, construct one question containing the exact competing interpretations and why choice changes the thought. Do not include logs/model debates.

- [ ] **Step 4: Implement faithful-vs-better-reasoned adoption interrupt**

Response `ADOPT_ALTERNATIVE` changes project authority by adding owner decision record; `KEEP_POSITION` preserves faithful candidate and keeps alternative as analysis. Neither becomes a general rule automatically.

- [ ] **Step 5: Run tests**

Run: `pytest tests/integration/test_owner_learning_resume.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/authorial_flow/{graph.py,routing.py,cli.py,nodes/owner_interrupt.py} tests/integration/test_owner_learning_resume.py
git commit -m "feat: turn owner judgments into scoped resumable learning"
```

---

### Task 9: End-to-End Default `humanize` with Semantic Escalation and Research Mock

**Files:**
- Create: `tests/integration/test_default_humanize_e2e.py`
- Create: `tests/fixtures/research/`
- Create: `docs/development-research-learning-verification.md`

**Interfaces:**
- Validates full default workflow across provenance → mode → sanity → optional P3/P4/research → Thought-Flow → cold audit → ranking → detector → minimal owner review → learning/resume.

- [ ] **Step 1: Write AI-draft semantic-repair scenario**

Fixture marks source as AI_FROM_OWNER_INPUTS and contains an inherited bridge that sanity rejects. Fake developmental node returns corrected substrate. Assert writer never receives inherited raw source and final candidate resolves owner-grounded obligations without requiring AI-provisional bridge coverage.

- [ ] **Step 2: Write research-trigger scenario**

Mock research indicates inherited citation does not directly answer the live question. Assert system generates separate research-informed route; owner position remains unchanged; editorial rank input excludes Pangram; one recommendation shown unless research route materially diverges.

- [ ] **Step 3: Write irreducible-authorial question scenario**

After machine branches/research exhausted, emit one `AUTHORIAL_AMBIGUITY` interrupt. Resume answer and assert it becomes project authority + learning record, then Thought-Flow restarts from corrected concept.

- [ ] **Step 4: Run all Plan 1 + Plan 2 tests**

Run: `pytest tests/unit tests/regression tests/integration -q`

Expected: PASS.

- [ ] **Step 5: Document verification boundaries**

State that autonomous executable code repair/optimizer promotion/live cutover remain Plan 3; research tests are mocked unless explicit live smoke test is run later.

- [ ] **Step 6: Commit**

```bash
git add tests/integration/test_default_humanize_e2e.py tests/fixtures/research docs/development-research-learning-verification.md
git commit -m "test: verify developmental humanize workflow"
```

---

## Development/Research/Learning Verification Gate

Run:

```bash
export LANGGRAPH_STRICT_MSGPACK=true
.venv/bin/python -m pytest tests/unit tests/regression tests/integration -q
```

Then inspect the deterministic e2e artifacts and verify:

- AI-provisional material can be dispositioned rather than forced into coverage;
- P2S never routes to automatic research;
- P3/P4/research can return a corrected concept to Basic Thought-Flow;
- research support vs system inference vs owner belief stay distinct;
- better-reasoned alternatives remain separate;
- editorial ranking occurs before Pangram visibility;
- owner bad-edge/global/meaning/voice labels become immediate project authority and scoped learning;
- only genuine authorial ambiguity interrupts before final preference.

## Plan Self-Review

- Spec coverage: provenance/modes, automatic `humanize`, semantic-sanity escalation, P3/P4 repair, bounded research, candidate roles/presentation, better-reasoned separation, learning scope ladder, local/global labels, narrow interrupts.
- No task makes model-derived source-order positives authoritative.
- No task silently adopts research/system conclusions into Joel's byline.
- No task generalizes personal facts/positions into style rules.
- Research and learning interfaces are isolated from writer-owner-gold leakage.
- Placeholder scan: no implementation placeholders remain.
