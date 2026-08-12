# Core Runtime Verification

## Implemented in Plan 1

- Content-addressed artifacts and append-only event journal.
- Secret-isolated nonblocking subprocess runner with independent heartbeat emission.
- Structured Claude/Codex CLI adapters and resumable Pangram task handling.
- Policy/project manifest hashing and exact regression-suite provenance.
- Authority-aware atomic semantic representation.
- Candidate-blind pressure aggregation, owner-labeled local-flow regressions, relational-fidelity regressions, and stop/rollback decisions.
- Completed-output cold-audit data contract and defect-bounded revision boundary.
- Editorial winner freeze before detector testing; detector scores cannot change editorial ranking.
- Downstream Pangram gate, semantic-delta rejection, and first-Human lineage freeze.
- LangGraph assembly targeting `StateGraph`, durable `interrupt`/`Command(resume=...)`, and SQLite checkpoint saver.
- CLI commands for run/resume/status/answer/package and deterministic evidence ZIPs.
- Legacy failure corpus and deterministic mocked end-to-end Basic Thought-Flow test.

## Verification performed in the build environment

The deterministic test suite runs without network/model calls. The real LangGraph SQLite
interrupt/resume integration test is present but is skipped when `langgraph` is unavailable. The
build container cannot install packages from PyPI, so Plan 1 does **not** claim a live LangGraph
checkpoint-resume result in this environment. `INSTALL-AND-RUN.sh` installs the pinned runtime on
the target machine, runs the full test suite, and blocks startup if that integration test fails there.

This limitation is dependency access, not a substituted home-grown runtime: production graph code
imports LangGraph and fails closed when the dependency is absent.

## Later-plan implementation status

Plan 2 behavior is implemented: provenance/mode inference, semantic-sanity escalation, P0–P4 operation levels, P3/P4 developmental repair, bounded research, candidate-role presentation, scoped owner learning, and narrow owner-question capture.

Plan 3 behavior is implemented at the deterministic/runtime level: autonomous executable repair, partition-safe optimization, release construction, live-provider smoke tooling, and legacy-supervisor cutover. Autonomous repair now uses dereferenceable failure evidence, isolated regression-first Codex patches, controller verification with one bounded correction, verified promotion, and same-thread checkpoint continuation after program-image restart. Live target-machine validation remains a separate plane.

## Authority boundary

Only owner-labeled flow cases are hard human flow authority. Model-derived source-order positives
remain diagnostic. Pangram is downstream of semantic, coherence, fidelity, and editorial gates.
