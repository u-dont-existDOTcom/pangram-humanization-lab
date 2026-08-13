# Authorial Flow Graph v1

A checkpointed LangGraph runtime for improving and humanizing prose by advancing from the live state of a thought rather than filling a predicted completed outline. It implements the Joel Articles P0–P4 preservation hierarchy, source-provenance authority, semantic-sanity escalation, bounded research, downstream detector use, scoped owner learning, and autonomous repair.

The current release is a **candidate** until the exact Git commit passes the live and owner acceptance planes on the target Zorin machine. Deterministic build-container success is reported separately from live Claude/Codex/Pangram/research plumbing and owner-confirmed thought-flow quality.

## One-command local workflow

On Joel's French Zorin system, install from the versioned Git branch:

```bash
git clone --branch install/authorial-flow-graph-v1-1.3.0-dev1 \
  https://github.com/u-dont-existDOTcom/pangram-humanization-lab.git \
  ~/authorial-flow-graph-v1
cd ~/authorial-flow-graph-v1
./INSTALL-AND-RUN.sh
```

`INSTALL-AND-RUN.sh` is idempotent. It creates or updates `.venv`, resolves the complete transitive dependency set without installing it, persists the exact artifact SHA-256 lock, installs under `--require-hashes`, reconciles the local Git repair baseline against an exact release overlay without touching `.state`, runs both deterministic pytest preflight and live Claude/Codex capability smoke through the autonomous Codex repair controller, then starts or resumes the content-addressed project thread. A failed live smoke prints the failing subcheck, attaches its redacted report to repair evidence, and must pass again inside the disposable repair worktree before a patch can be promoted; if Codex itself is unavailable, the installer packages the failure instead of silently returning. A clean existing Git head is left alone so a previously promoted self-repair is never reverted by rerunning the installer; a dirty update is accepted only when it matches the new release manifest and contains no unrelated changes. If the preserved SQLite thread was already terminally stopped by an older runtime after exhausting a machine-repair budget, the newer program image replays the latest pre-failure checkpoint on that same thread once for the new program version; a bounded stop produced by the current version is marked exhausted so manual reruns cannot loop providers indefinitely.

Subsequent runs:

```bash
./RUN.sh
```

A different source can be supplied directly:

```bash
./RUN.sh /absolute/path/to/section.md
```

Status without starting a model call:

```bash
./RUN.sh status
```

Ctrl+C is a checkpointed supervision request while machine work is running. If a cancellable Claude or Codex child call is active, the runtime terminates it and discards partial output; if Pangram, repair promotion, or another atomic operation is active, the pause waits until its safe update—including a Pangram task ID—is checkpointed. Supervision then opens in the same terminal on the same thread.

## Live work feed and interactive supervision

The normal live feed shows complete article proposals, guard verdicts and reasons, generation retries, accepted moves, the exact current passage, Pangram state, repair phases, and quiet-call heartbeats. It never publishes incomplete child output, raw prompts, provider transcripts, child environments, credentials, or hidden chain-of-thought.

At the `supervisor>` prompt, free-form questions are read-only: asking what is happening does not resume or mutate the graph. The supervisor may describe one proposed redirect, rollback, proposal rejection, meaning correction, or unchanged resume. The controller—not the model—then displays the exact scope, restart depth, fields to clear, moves to remove, and resume node. Nothing changes until the owner approves the confirmed action with `y`.

Type `leave paused` (or `leave`) to keep the durable interrupt pending. The next `./RUN.sh` reopens the same supervisor session and same thread. A rejected proposal is tied to its exact content hash; rollback uses per-move meaning coverage; a cancelled attempt is rerun from its prior checkpoint; and partial model text is always discarded.

## Operation levels

The runtime distinguishes P0, P1, P2, P2S, P3, and P4. A plain `humanize` request does not blindly preserve every proposition in an AI-generated draft. Owner-final prose is protected; AI-from-owner-inputs can escalate to developmental P3/P4 when semantic sanity or architecture requires it. Basic Thought-Flow remains the narrow generation experiment and temporarily escalates to developmental/research repair when the underlying thought itself is defective.

## Research

Research is automatic only when a factual, doctrinal, historical, linguistic, scientific, or source-selection uncertainty could materially change the thought. Research findings can create a separately labeled better-reasoned alternative but cannot silently become Joel's personal position.
 Existing direct URLs can be fetched without search credentials. When material research needs search discovery, `BRAVE_SEARCH_API_KEY` is requested lazily in the terminal (or read from the environment), kept controller-side, and removed from Claude/Codex child environments.

## Detector policy

Pangram is downstream of semantic sanity, curious-reader continuity, cold audits, fidelity, coherence, completeness, and copy gates. The editorial winner is frozen before detector optimization. Bounded detector variants may be tried, but a worse Pangram-passing passage never silently replaces stronger prose.

## Owner review

The normal path asks for one owner judgment only after machine reasoning is exhausted. A machine-valid candidate normally asks only whether it is accepted. If rejected for flow, the runtime can record the first bad edge and whether the previous move was already the natural stopping point. Local edge/stop labels and whole-passage precomputed-outline labels are separate learning targets.

Example owner response:

```bash
./RUN.sh answer '{"kind":"BAD_EDGE","move_index":3,"note":"This changes to a nearby issue instead of following the live question."}'
```

Owner judgments are immediate project authority. They become reusable hypotheses first and are promoted to general rules only after repeated analogous support, held-out success, or explicit owner confirmation. Personal facts and positions are never generalized into style rules.

## Autonomous machine repair

Machine-repairable runtime/provider/regression failures are handled inside the runtime rather than handed to the owner as a debugging chore. The controller first persists a secret-redacted, dereferenceable failure bundle containing the actual provider/model/role, expected schema, bounded stdout/stderr, thread/program/source state, and relevant runtime context. Codex then repairs an isolated git worktree and must demonstrate the regression failing before the patch and passing afterward. Repair Codex does not receive Pangram or Brave credentials and cannot mutate protected project inputs, policy, owner labels, learning records, or detector baselines.

Installer preflight uses the same machinery one stage earlier: if the full pytest gate fails before LangGraph can start, the controller persists the exact command/stdout/stderr evidence, invokes the isolated repair cycle, promotes only a verified patch, and reruns the exact pytest command. Bounded exhaustion creates the evidence ZIP automatically rather than making the owner relay terminal logs. Repair worktrees also place the installed project `.venv/bin` first on `PATH`, so Codex RED/GREEN commands test the candidate with the runtime's actual dependency environment rather than Zorin's system Python.

The controller—not Codex—runs the declared targeted tests plus integration and full-suite gates, protected-hash/source-hardcoding checks, and independent plan/diff review. Plans must name exact local pytest commands; prose test descriptions stop before review or write-capable execution. Each plan is signed against its failure evidence and program version, and the same plan cannot be reviewed twice on unchanged context. Every attempt ends explicitly as `APPLIED_VERIFIED`, `STAGED_FOR_OWNER`, `REJECTED_WITH_REASON`, or `NON_APPLICABLE_STOP`, with the reason available to any permitted next planner call.

One bounded Codex correction is allowed if controller verification fails; a second correction is not. Only the verified commit is promoted. Promotion checkpoints a machine-only restart interrupt, the stale process exits, and the new program image resumes the **same LangGraph thread/checkpoint** at the failed machine stage rather than reseeding the article. High-level repair phases remain visible while this happens. If the bounded repair budget is exhausted, the runtime automatically creates a secret-free evidence ZIP and stops with `bounded_machine_stop`; it does not ask the owner to collect or upload routine logs.

## Bounded-failure controls in 1.2

Semantic-sanity escalation is fail-closed: only `BASIC`, `P3`, `P4`, `RESEARCH`, and `OWNER` are valid, and a semantic FAIL cannot fall through to generation. An owner answer resolves only the owner question; pending research or developmental work remains required.

Generation pressure and edge judgments carry a SHA-256 identity for the exact accepted passage, move count, authority coverage, graph version, and program version. Stale decisions cannot govern a changed boundary. `STOP_BEFORE_CANDIDATE` now discards the extra candidate and either stops on the accepted passage or rolls back a validated arrival when protected meaning remains. If safe rollback cannot be proven, the controller stops as `POLICY_CONTRADICTION` without spending more writer attempts. A candidate that visibly arrives while protected units remain cannot enter accepted prose.

Returned machine failures receive the same redacted, dereferenceable evidence as exceptions. A content-free decision trace shows boundary hashes, counts, pressure/edge enums, confidences, rejection class, and budgets without source, accepted, candidate, prompt, transcript, or credential text. Provider attempts likewise record typed failure causes and capability signatures; deterministic auth/schema failures stop, while fallback can move only to a distinct configured profile.

## Evidence and packaging

`./RUN.sh package --reason bounded-failure` creates a secret-free evidence ZIP containing policy/project manifests, checkpoint/event data, content-addressed artifacts, regression evidence, detector output, and owner-response state. Internal artifacts stay internal; the runtime does not print transient `UPLOAD THIS FILE` paths that later disappear.

Version 1.3 also publishes a compact privacy-safe result record automatically after installer checks and significant runtime outcomes. It uses the separate orphan branch `diagnostics/authorial-flow-graph-v1` in the canonical private repository, without switching or dirtying the installed source branch. Records contain only typed outcomes, counts, hashes, provider capability status, and the content-free boundary trace; article text, prompts, transcripts, stdout/stderr bodies, exceptions, credentials, full local paths, and evidence ZIP bytes are permanently excluded. If Git authentication or the network is unavailable, the outcome is unchanged and the record remains in `.state/diagnostics/outbox/` for the next run. `./RUN.sh publish-results` creates a current snapshot and retries the queue manually.

## Validation status

- **Deterministic:** the current implementation passes the unit, regression, real LangGraph/SQLite, real local-Git diagnostics publication, integration-with-fakes, repair, optimizer, release, heartbeat, provenance, authority-isolation, detector-downstream, supervisor-security, and packaging suites in the build environment. Exact 1.2 control evidence is recorded in `docs/2026-08-12-bounded-failure-control-review.md`; 1.3 publication evidence is recorded in `docs/2026-08-12-automatic-diagnostics-publication-review.md`.
- **LangGraph checkpoint integration:** deterministic real-SQLite tests cover cancelled-node replay, Pangram task-ID checkpoint/poll resume, repair-promotion consistency, invalid-action reinterrupts, and durable same-thread supervisor resume. The exact candidate still requires the target Zorin run; deterministic signal tests do not prove terminal behavior on that machine.
- **Live Claude/Codex:** earlier releases supplied provider evidence, but the interactive-supervisor candidate requires fresh target-machine smoke and one real same-terminal supervisor conversation.
- **Live Pangram:** current async-API authentication is checked without creating a task; real candidate submission remains downstream of local gates, checkpoints the task ID before polling, and accepts only returned version `4.0` with Human/zero-AI status. Target-machine evidence required.
- **Live research plumbing:** opt-in provider smoke; research quality remains a separate editorial/evidence judgment.
- **Owner-confirmed:** a real bad-looking Thought-Flow run, Ctrl+C, one supervisor question, one confirmed redirect, and same-thread continuation or durable pause on the target Zorin machine remain required before approval.

See `docs/acceptance-matrix.md` for criterion-by-criterion evidence and `docs/migration-cutover.md` for the legacy cutover boundary.
