# Authorial Flow Graph v1 — Design Specification

**Date:** 2026-08-10  
**Status:** Owner-approved design; implementation in progress  
**Migration source:** `authorial-loop-supervisor-v3` and accumulated authorial-loop/Pangram evidence  
**Primary user environment:** French Zorin Linux; working directory under `~/Téléchargements`

## 1. Purpose

Build a durable, local, one-command writing-reconstruction system in which the human supplies only genuinely irreducible authorial judgments. Installation, model capability checks, state persistence, retries, regression execution, model orchestration, Pangram measurement, repair, evidence retention, and resumption are machine work.

The system exists to test and operationalize an **externalized recurrent authorial process**:

1. preserve **human authority**, not every proposition, source role, bridge, sequence, or stopping point in an AI-generated realization;
2. let one accepted semantic move alter the live state before the next move is generated;
3. separate flow judgment from semantic licensing;
4. block later clauses from retroactively rescuing a bad transition or invented relation;
5. use owner labels as sparse authoritative supervision;
6. treat Pangram as an external detector endpoint, never as a substitute for fidelity, quality, or owner judgment.

### 1.1 Approved authority, mode, research, detector, and learning amendments

A plain `humanize` request first classifies provenance. Owner-final/locked prose remains conservative by default. Natural owner drafts preserve owner-grounded meaning. An AI draft produced from owner inputs is **provisional realization evidence**: inherited AI-selected premises, citations, causal/evidentiary bridges, heading, order, and stopping point may be repaired under P3/P4 rather than preserved by inertia. Source pools may be reconstructed under P4.

Operation levels follow Joel Articles P0/P1/P2/P2S/P3/P4. Basic Thought-Flow remains a distinct experiment in advancing from the live thought. If semantic sanity fails, it temporarily escalates to the authorized P3/P4 or bounded-research branch, repairs the conceptual substrate, then rejoins Thought-Flow. P2S never silently performs substantive repair or automatic research.

Research is automatic only when a factual, doctrinal, historical, linguistic, scientific, or source-role uncertainty could materially change the thought. Research is bounded and question-driven; source support, system inference, and Joel's position remain separate. When evidence materially favors a different conclusion, the system preserves both the faithful Joel route and a separately labeled better-reasoned alternative. It never silently puts the latter in Joel's byline.

Candidate ranking is editorially blind to Pangram. The strongest coherent candidate is frozen before detector testing. Bounded meaning-preserving detector variants may be explored afterward; a weaker Pangram-passing variant never silently replaces the editorial winner. Normally one recommended candidate is shown; 2–3 are shown only for materially different thought routes or unresolved authorial choices.

Owner feedback is sparse supervision. A correction is immediate project authority. It becomes a reusable cross-project rule only after repeated analogous support, held-out success, or explicit owner confirmation. Personal facts, beliefs, memories, relationships, and article-specific positions are never generalized into style rules. Local edge/stop labels and whole-passage precomputed-shape labels are distinct learning targets. The system exhausts machine reasoning first and interrupts only for a surviving material authorial ambiguity.

## 2. Non-goals

Version 1 will not:

- provide a browser UI;
- make DSPy/GEPA a required runtime dependency;
- use OpenHands as a required repair backend;
- claim generalization from the current small owner-labeled corpus;
- infer that source order is automatically good flow;
- silently rewrite a candidate after final audit;
- ask the user to carry logs, scores, manifests, ZIPs, or version updates between runs;
- treat a Pangram-Human result as owner-final.

## 3. Architectural decision

### 3.1 LangGraph is the sole live runtime

The existing system has three overlapping orchestration layers: harness, inner autopilot, and outer supervisor. Version 1 replaces those live state machines with one LangGraph graph. The legacy implementation becomes a migration source and regression corpus, not a subprocess in the production path.

Verified dependency baseline on 2026-08-10:

- `langgraph==1.2.9`
- `langgraph-checkpoint-sqlite==3.1.0`
- Python `>=3.10`; primary local target and live-test interpreter Python 3.12.3

A SQLite checkpointer persists graph state. One content-addressed `thread_id` identifies each source + requirements + author-context + regression-version + graph-program-version combination. Reusing that thread resumes the exact checkpoint. A changed protected input creates a new thread rather than mutating the old run.

### 3.2 Current system becomes the regression corpus

The migration imports and protects:

- `INPUT.md`
- `REQUIREMENTS.md`
- `AUTHOR_CONTEXT.md`
- `HUMAN-FLOW-GOLD.json`
- `SEMANTIC-RELATION-GOLD.json`
- `SOURCE-FLOW-POSITIVE.json` as **diagnostic only**
- `PANGRAM-SOURCE-BASELINE.json`
- `PRIOR-PANGRAM-HUMAN-CANDIDATE.md`
- known failure traces and failure classifications
- protected-file and secret-isolation policies

Owner-labeled flow cases are hard authority. Objective semantic-relation regressions are hard fidelity gates. Model-derived source-order positive probes remain diagnostic and cannot force source order.

## 4. Repository layout

```text
authorial-flow-graph-v1/
├── INSTALL-AND-RUN.sh
├── RUN.sh
├── pyproject.toml
├── requirements.lock
├── README.md
├── src/authorial_flow/
│   ├── cli.py
│   ├── config.py
│   ├── state.py
│   ├── graph.py
│   ├── routing.py
│   ├── artifacts.py
│   ├── events.py
│   ├── process_runner.py
│   ├── secrets.py
│   ├── models/
│   │   ├── claude_cli.py
│   │   ├── codex_cli.py
│   │   └── pangram.py
│   ├── nodes/
│   │   ├── bootstrap.py
│   │   ├── regression.py
│   │   ├── atomize.py
│   │   ├── pressure.py
│   │   ├── generate.py
│   │   ├── flow.py
│   │   ├── fidelity.py
│   │   ├── stopping.py
│   │   ├── final_gates.py
│   │   ├── owner_interrupt.py
│   │   ├── repair.py
│   │   └── finalize.py
│   ├── prompts/
│   ├── repair/
│   └── optimizer/
├── project/
│   ├── INPUT.md
│   ├── REQUIREMENTS.md
│   ├── AUTHOR_CONTEXT.md
│   ├── HUMAN-FLOW-GOLD.json
│   ├── SEMANTIC-RELATION-GOLD.json
│   ├── SOURCE-FLOW-POSITIVE.json
│   └── PANGRAM-SOURCE-BASELINE.json
├── tests/
│   ├── unit/
│   ├── regression/
│   ├── integration/
│   └── fixtures/
├── docs/
└── .state/                 # runtime, ignored by git
    ├── checkpoints.sqlite
    ├── events.jsonl
    ├── artifacts/
    ├── worktrees/
    └── final/
```

Files are kept small and role-specific. Large raw model/Pangram responses live in the artifact store; LangGraph state stores content-addressed references rather than duplicating large payloads in SQLite checkpoints.

## 5. Graph state

The graph uses a typed state with append-only or explicitly reduced fields. The state contains compact control data, not full raw logs.

```text
Identity
- project_id
- thread_id
- source_hash
- protected_input_hashes
- graph_version
- regression_version

Inputs
- source_ref
- requirements_ref
- author_context_ref
- owner_gold_ref
- semantic_gold_ref
- diagnostic_positive_ref

Semantic representation
- section_job
- atom_refs
- exact_identity_strings
- atom_coverage

Generation
- accepted_moves[]
- accepted_prefix_hash
- move_index
- retry_count
- rollback_count
- branch_memory[]
- pressure_votes[]
- committed_pressure
- candidate_ref
- candidate_spans[]

Judgments
- entry_edge_result
- full_edge_result
- relation_result
- semantic_result
- stop_result
- final_local_gates
- Pangram_result_ref

Human supervision
- interrupt_payload
- owner_response
- newly_added_label_ref

Repair
- failure_class
- repair_attempt
- plan_ref
- patch_ref
- test_ref
- review_ref

Runtime
- phase
- status
- active_process
- heartbeat
- last_error_ref
- event_sequence
```

State transitions must be idempotent. Nodes that can be replayed after interruption write content-addressed artifacts and check for an existing successful result before making another billable/model call.

## 6. Main graph

```text
START
  → bootstrap
  → load_project
  → regression_subgraph
  → atomize_source
  → generation_subgraph
  → final_local_gates
  → Pangram_4
  → freeze_candidate
  → owner_interrupt
  → finalize
```

Any machine failure routes to `failure_classifier`. Repairable failures route to `repair_subgraph`; a real missing authorial judgment routes to `owner_interrupt`. Catastrophic bounded failure packages evidence automatically and stops without asking the user to collect anything.

## 7. Regression subgraph

### Hard startup gates

1. **Owner flow regression**
   - exact suite hash and ordered case IDs;
   - candidate-blind state precommitment and edge pipeline must reproduce owner labels;
   - regression examples are evaluator-only and never writer input.

2. **Semantic-relation regression**
   - rejects invented answer, causal, explanatory, support, contrast, timing, or evaluative relations;
   - accurate later facts cannot rescue an invented relation earlier in a candidate.

3. **Protected-input integrity**
   - source, requirements, author context, owner labels, and Pangram baseline hashes are verified.

4. **Runtime asset and schema preflight**
   - every required prompt, schema, script, and dependency is present and parseable before model calls.

### Diagnostic-only probes

`SOURCE-FLOW-POSITIVE.json` remains useful for detecting over-rejection, but it is explicitly model-derived from source adjacency. A failure is evidence for analysis, not a hard requirement to reproduce source order.

Every regression result is bound to:

- suite SHA-256;
- ordered case IDs;
- graph/prompt version;
- exact model ID and CLI version;
- child return code;
- stdout/stderr artifact refs;
- generated result hash.

No shared result path may be reused without exact provenance validation.

## 8. Generation subgraph

### 8.1 Atomization

Codex produces an authority-aware semantic representation. For owner-final/P2S material, must-preserve propositions remain lossless. For AI-generated or mixed developmental material, the representation preserves provenance and owner-grounded obligations while marking inherited AI propositions/relations as provisional rather than making them mandatory coverage. Ordinary full source sentences are not passed through as exact strings. Exact locks are limited to identity-bearing phrases, quotations, URLs, names, numerical/source identifiers, or owner-approved language whose exact form performs a necessary function.

The first representation pass does not silently fact-check or rewrite. When semantic sanity identifies a thought-level or source-role defect and the active mode authorizes substantive work, it emits an explicit P3/P4/research escalation artifact. The original source remains immutable; corrected conceptual units return to Thought-Flow with their provenance/disposition recorded.

### 8.2 Candidate-blind precommitment

Before a candidate exists, two independent readers inspect only accepted prose:

- Codex pressure reader;
- Claude pressure reader.

They vote `OPEN`, `NATURAL_STOP`, or `AMBIGUOUS`, and describe:

- live pressure;
- function of the previous move;
- settled material;
- backward-reopen risks;
- why stopping may be natural.

A credible `OPEN` vote vetoes premature stopping. A `NATURAL_STOP` action requires cross-model agreement or one very strong stop vote with no competing `OPEN` vote. Grammatical completeness is not thought-level completion.

### 8.3 One atomic move

Claude sees:

- unordered semantic atoms;
- accepted prose;
- committed pressure state;
- requirements and author context;
- bounded rejection challenges for the current position.

Claude does not see owner regression examples or an expected source order. It writes exactly one semantic advance or `<STOP>`.

A deterministic splitter rejects candidates that package multiple advances through multiple sentences, semicolons, em-dash turns, substantive colon joins, or clear propositional continuations such as `, which ...` when they function as a second move.

### 8.4 Flow gates

1. **Entry-edge judge** sees only the candidate's first committed discourse move. Later material cannot rescue a bad doorway.
2. **Full-edge judge** evaluates the whole atomic candidate against the precommitted state.
3. Both are source-blind and may not demand source order, unused facts, or an ideal essay structure.

A candidate must grow from the previous move's live pressure; topical relatedness alone is insufficient.

### 8.5 Fidelity gates

1. **Relation guard** sees source + accepted prose + one semantic span and rejects invented relations.
2. **Semantic guard** checks facts, actors, chronology, certainty, causality, attribution, autobiographical stance, and context.

These guards cannot choose what should come next. Flow and semantic licensing remain separate authority domains.

### 8.6 Stop and rollback

If precommitment says `NATURAL_STOP`:

- complete semantic coverage → stop before writer generation;
- incomplete coverage → roll back the prior accepted move and regenerate from the earlier state so remaining meaning is placed before the endpoint.

Rollback is bounded. Rejected branches are remembered by semantic/edge signature so the system does not regenerate equivalent dead ends.

## 9. Final local gates

Pangram is called only when all local hard gates pass:

- every must-preserve atom is represented;
- no invented or strengthened meaning;
- no unresolved fidelity issue;
- coherent move sequence;
- all accepted edges were passed by the production edge pipeline;
- copy-distance gate rejects near-verbatim source replay;
- candidate is complete and not blocked;
- protected files remain unchanged.

Generic model judgments such as `cold_humanization_pass` remain diagnostic only.

## 10. Pangram integration

The Pangram node:

- verifies `pangram-4` access through `/models`;
- submits through the asynchronous task API;
- checkpoints `task_id` before polling;
- resumes pending tasks instead of resubmitting;
- verifies returned version `4.0`;
- preserves the complete raw response and segment windows;
- strips `PANGRAM_API_KEY` from all Claude/Codex subprocess environments;
- never persists or logs the key;
- reuses the source baseline only when the exact source hash matches.

The operational detector gate is document-level Human with zero AI and zero AI-assisted fraction/windows. Detector failure is evidence for bounded search/optimization, not permission to alter meaning or degrade prose. The editorial winner is frozen before Pangram. Detector variants must independently pass meaning/fidelity/coherence gates; if a weaker equivalent variant passes while the editorial winner does not, both statuses are surfaced and the editorial winner remains recommended.

## 11. Owner interrupt

When a candidate passes local gates and Pangram, it is frozen before any further mutation. LangGraph calls a durable interrupt with:

- candidate text;
- numbered moves;
- concise machine-gate summary;
- no implementation logs unless requested.

Owner responses:

1. `ACCEPT`
2. `BAD_EDGE` — first move that does not follow
3. `STOP_BEFORE` — previous move should have ended the thought
4. `MEANING_ISSUE` — concise correction
5. `VOICE_ISSUE` — concise correction
6. `DEFER`

`BAD_EDGE` and `STOP_BEFORE` are written directly into owner flow ground truth and become evaluator regressions. Meaning/voice corrections are stored as protected owner issues. Execution resumes from the appropriate graph node; the user does not restart the program or move files.

## 12. Failure classification and repair subgraph

### 12.1 Classification

Failures are first classified as:

- deterministic/runtime;
- model-provider plumbing;
- regression/evaluator architecture;
- candidate-generation dead end;
- fidelity failure;
- Pangram-only failure;
- genuine owner judgment.

Only the final class may interrupt the user.

### 12.2 Repair workflow

1. Create an isolated git worktree from the current accepted implementation.
2. Codex produces one bounded causal repair plan.
3. Claude reviews the plan; schema-constrained Codex review is a recorded fallback if Claude review is unavailable.
4. Codex implements only in the worktree.
5. Run compile, unit, regression, integration, protected-hash, secret-isolation, and source-hardcoding tests.
6. Claude reviews the actual diff; Codex fallback remains available and recorded.
7. Promote only a reviewed, tested patch.
8. Resume the graph from the failed machine checkpoint.

Repair provider failure is machine work. All attempts retain model ID, CLI version, return code, stdout/stderr, parse errors, and output-file state.

A repair may never modify protected source/owner files or add current topic/source phrases to production code/prompts.

## 13. Process runner and observability

All Claude/Codex subprocess calls go through one nonblocking `ProcessRunner` using `Popen` and polling/select rather than blocking `readline()`.

Every 10 seconds the terminal prints a single updated status line containing:

```text
thread | graph node | provider/model | child PID | elapsed | retry | moves | last event
```

The runner records:

- start/end timestamps;
- PID and command with secrets redacted;
- model/provider;
- stdout/stderr streams;
- heartbeat events;
- timeout/termination reason;
- exit code.

A silent long model call remains visibly alive. Ctrl+C checkpoints current state and terminates or preserves child processes according to node policy. Re-running the same command resumes the thread.

Normal operation never prints an internal `UPLOAD THIS FILE` path. Evidence ZIPs are created only for final completion or bounded catastrophic failure.

### 13.1 Default budgets and concurrency

Budgets live in project configuration rather than prompts or code branches. Initial defaults:

- accepted moves: `30`;
- writer attempts at one position: `4`;
- total rollbacks per trajectory: `8`;
- provider retries per resolved model: `3`;
- Claude/Codex subprocess deadline: `30 minutes`;
- Pangram polling deadline: `15 minutes`;
- optimizer rounds: `6`;
- locally valid Pangram candidates per trajectory: `6`;
- executable repair rounds: `5`;
- repair-plan revisions: `2`.

The two pressure readers may run concurrently because they use different provider CLIs. All graph-state mutations, owner-label writes, worktree promotion, and Pangram submissions are serialized. V1 supports one local graph process per SQLite database; it does not claim multi-process writer safety.

Reaching a budget produces a durable bounded-stop checkpoint and complete machine evidence. It does not manufacture an owner question unless the missing information is genuinely authorial.

## 14. Artifact and event storage

`.state/events.jsonl` is append-only and records every node start/end, model call, retry, gate result, repair, interrupt, and owner response.

Raw payloads are written content-addressably:

```text
.state/artifacts/<sha256-prefix>/<sha256>.<ext>
```

Each artifact has a small metadata sidecar containing type, producer node, timestamp, input hashes, model/version, and secrecy classification.

Large artifacts are referenced from graph state. This keeps SQLite checkpoints compact and makes evidence packaging deterministic.

## 15. Optimizer

### 15.1 Built-in optimizer in v1

A separate optimizer subgraph can compare prompt/program variants against development regressions while enforcing hard fidelity and owner-authority constraints. It may optimize evaluator/program instructions, not article prose.

Promotion requires:

- no hard-regression failures;
- aggregate improvement across positive and negative development cases;
- no protected-data leakage;
- no source/topic hardcoding;
- validation partition success;
- locked-test success when a sufficiently large locked set exists.

The current corpus is too small to support a credible generalization claim. Initial cases are development data. The system records partition metadata now so future owner labels can populate validation and locked-test sets.

### 15.2 Optional DSPy/GEPA integration

DSPy/GEPA is installed only through an optional extra and is not in the normal execution path. Custom `BaseLM` adapters will invoke Claude/Codex CLI. GEPA activation requires a minimum configured label count and explicit optimizer command. Its outputs remain candidates that must pass the complete regression suite before promotion.

OpenHands remains a possible future repair backend, not a v1 dependency.

## 16. One-command workflow

Initial installation and first run:

```bash
cd ~/Téléchargements
unzip -q ~/Téléchargements/authorial-flow-graph-v1.zip -d ~/Téléchargements
cd ~/Téléchargements/authorial-flow-graph-v1
./INSTALL-AND-RUN.sh
```

`INSTALL-AND-RUN.sh` is idempotent and performs:

1. Python/version checks;
2. isolated `.venv` creation/update;
3. hash-pinned dependency installation;
4. Claude/Codex CLI presence and live minimal model verification;
5. Pangram model-access preflight when a key is available;
6. migration-corpus integrity checks;
7. full local test suite;
8. graph start or checkpoint resume;
9. evidence packaging only at final/bounded stop.

Subsequent runs:

```bash
./RUN.sh
```

A different source can be supplied without editing code:

```bash
./RUN.sh /absolute/path/to/section.md
```

The current project files are the default when no path is supplied.

## 17. Secret and authority isolation

### Visibility matrix

| Component | Source | Atoms | Accepted prose | Candidate | Owner gold | Pangram key |
|---|---:|---:|---:|---:|---:|---:|
| Writer | No | Yes | Yes | N/A | No | No |
| Pressure readers | No | No | Yes | No | No | No |
| Entry/full edge judges | No | No | Yes | Yes | No | No |
| Relation/semantic guards | Yes | Optional IDs | Yes | Yes | No | No |
| Regression runner | Case-specific | No | Case-specific | Case-specific | Yes | No |
| Pangram client | No | No | No | Yes | No | Controller only |
| Repair agents | Code/evidence only | No article authority | No writer exemplars | No production candidate unless diagnosing | Read-only policies | No |

Owner labels and protected source files are never writable by repair agents. Pangram credentials remain controller-only and are removed from child environments.

## 18. Testing strategy

### Unit tests

- typed state reducers and routing;
- content-addressed artifact store;
- secret redaction and environment stripping;
- structured-output parsing;
- atomic move splitter;
- copy-distance gate;
- regression provenance binding;
- owner-response validation;
- process heartbeat and timeout logic.

### Regression tests

- all owner flow labels;
- all semantic-relation labels;
- later-clause rescue failures;
- candidate-blind stop failures;
- near-copy false success;
- stale shared-result contamination;
- runtime files excluded from patch diffs;
- exact-string leakage;
- missing packaged schemas/assets;
- internal ZIP destruction/incorrect path reporting;
- reviewer-provider fallback behavior.

### Integration tests with mocks

- full graph through owner interrupt;
- crash during a model node, then resume;
- crash after Pangram task submission, then resume without resubmission;
- silent subprocess with visible heartbeat;
- rejected repair plan → revised plan;
- broken patch → bounded implementation repair;
- protected-file mutation rejection;
- owner bad-edge label → regression update → resume.

### Live smoke tests

- exact Claude and Codex models resolved by minimal calls;
- Pangram `/models` access;
- one small non-public test candidate only after local gates;
- complete clean-package installation on French Zorin paths.

## 19. Acceptance criteria

Version 1 is complete when all of the following are demonstrated:

1. one command installs or updates the environment and resumes the correct thread;
2. Ctrl+C and process death resume from the last successful checkpoint;
3. a silent child call produces a heartbeat at least every 10 seconds;
4. no stale regression evidence can cross-contaminate suites;
5. repair agents cannot mutate protected source/owner files;
6. owner regression examples are never visible to the writer;
7. source-order positive probes are diagnostic only;
8. Pangram is skipped when hard local gates fail;
9. Pangram task IDs are checkpointed before polling and not duplicated on resume;
10. the first Pangram-Human candidate is frozen;
11. machine failures invoke machine repair rather than user log collection;
12. the only routine human interrupt is an authorial decision or credential action;
13. a bad-edge owner label is persisted and execution resumes automatically;
14. internal artifacts are archived, not printed as nonexistent user upload paths;
15. final completion produces the accepted text plus one reproducible evidence package;
16. all migrated known failure cases have explicit passing regression coverage.

## 20. Migration and cutover

The legacy supervisor remains read-only reference evidence during implementation. Cutover occurs only after the LangGraph system passes the legacy regression suite and a complete mocked end-to-end run.

The first live run uses the existing free-will development passage and existing Pangram baseline. No legacy controller/harness process runs inside the new graph. Once the new system reaches a valid owner interrupt and resumes successfully from the owner's response, the legacy supervisor is retired from active development.

## 21. Deferred decisions

No unresolved design choice blocks implementation. The following are deliberately deferred beyond v1:

- browser dashboard;
- remote/cloud checkpoint store;
- OpenHands repair backend;
- automatic long-running GEPA optimization;
- multi-user support;
- a claim of generalization beyond the accumulated owner/regression corpus.

## 22. Reference basis

The design was checked against current primary documentation on 2026-08-10:

- LangGraph persistence, checkpoints, threads, recovery, and SQLite checkpointer guidance: <https://docs.langchain.com/oss/python/langgraph/persistence>
- LangGraph dynamic interrupts and resume via `Command`: <https://docs.langchain.com/oss/python/langgraph/interrupts>
- LangGraph streaming and custom events for arbitrary model clients: <https://docs.langchain.com/oss/python/langgraph/streaming>
- LangGraph subgraph persistence choices: <https://docs.langchain.com/oss/python/langgraph/use-subgraphs>
- `langgraph` release 1.2.9: <https://pypi.org/project/langgraph/>
- `langgraph-checkpoint-sqlite` release 3.1.0: <https://pypi.org/project/langgraph-checkpoint-sqlite/>
- DSPy/GEPA documentation: <https://dspy.ai/>
