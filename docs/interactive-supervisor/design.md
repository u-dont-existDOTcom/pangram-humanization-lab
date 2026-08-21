# Interactive Same-Terminal Supervisor Pause Design

**Status:** Approved by Joel on 2026-08-12 for test-first implementation planning.

**Selected interface:** Pressing Ctrl+C during a run pauses the active work and opens the supervisor conversation in the same terminal. This release does not add an attachable `supervise` command.

**Authoritative code baseline:** source commit `9683918db65c9907a081d177d22ccd6953f12415`, packaged as `authorial-flow-graph-v1-9683918-pangram-async-auth-fix-release.zip`, SHA-256 `7bbdcefc354e1ff5ef45b57aa76b8cf55800a26b7796f3501e82452c0a84d140`.

**Preservation mode:** P0 for article and policy material. The feature changes runtime control and observability only. It does not edit project inputs, article prose, owner gold, policy files, learning records, or the detector contract except through an explicit, confirmed owner action described below.

## Goal

Joel can watch the actual operational work, press Ctrl+C when it appears to be going wrong, ask a supervisor what the runtime is doing, and give a confirmed instruction that changes the remaining work without corrupting the active checkpoint or silently weakening any gate.

## User-visible contract

The normal run prints meaningful events as they occur: phase, provider/model/role, proposed prose, explicit guard verdicts and reasons, retries, accepted moves, the current accepted passage, repair state, and Pangram state. Hidden reasoning, raw prompts, provider transcripts, and credentials remain private.

When Joel presses Ctrl+C during active work:

1. A running Claude or Codex child process is terminated using the existing graceful-then-forceful child cleanup.
2. Any incomplete model response is discarded and cannot become a proposal or accepted move.
3. The graph commits a supervisor-pause checkpoint on the existing thread.
4. The terminal displays the current accepted passage, any complete unaccepted proposal, explicit guard results already returned, the interrupted operation, retry/repair/detector state, and the operation that would run next.
5. The terminal opens a free-form supervisor conversation.

Joel may ask questions without changing state. A proposed change shows its exact effect and requires confirmation before the graph resumes. Leaving the supervisor conversation keeps the graph paused; the next `./RUN.sh` reopens the same supervisor session on the same thread.

## Approaches considered

### 1. Checkpointed graph pause with an in-terminal supervisor loop — selected

The runtime converts a pause request into a first-class graph interrupt, then holds a conversational loop in the CLI while that interrupt remains unresolved. Confirmed actions return to the graph as typed commands.

This preserves the checkpoint and lets the action, invalidation, and resumed destination remain auditable in graph state.

### 2. Catch Ctrl+C outside LangGraph and patch a sidecar file

This would require less graph wiring, but a sidecar instruction could diverge from the checkpoint that it claims to modify. Reopening the graph after an aborted node would also make it harder to distinguish a discarded proposal from an accepted result.

### 3. Exit on Ctrl+C and attach through another command or process

This preserves the current safe-exit behavior but adds friction at the exact moment Joel wants to understand a bad-looking run. Joel selected immediate same-terminal supervision.

## Architecture

### Pause controller and signal handling

A per-run `PauseController` owns the pause request. While the graph is executing, the CLI installs a temporary SIGINT handler that sets the controller's requested flag. The handler itself does not mutate checkpoints or raise through an atomic in-process operation.

`ProcessRunner` receives the controller. Its existing polling loop notices the request, terminates the current child process, and raises a dedicated `OwnerPauseRequested` exception. The guarded graph node catches that exception and returns a supervisor-pause update instead of a machine failure.

For short in-process atomic operations, including Pangram submit/poll and repair promotion, SIGINT records a pending pause. The operation finishes to its normal safe boundary, its result is included in the node update, and the wrapper routes to supervision before another operation starts. The terminal prints that the pause is pending while an atomic operation finishes. This prevents a successful Pangram submission from losing its task ID and being submitted again after resume.

The temporary SIGINT handler is removed when graph execution returns. Inside the supervisor loop, Ctrl+C cancels only the current supervisor answer or offers to leave the run paused; it never resumes the graph implicitly.

### Graph pause boundary

Every machine node uses the same pause-aware guard. A pause update contains:

- `status: supervisor_pause_requested`;
- the interrupted node and operation;
- whether that operation was cancelled or completed atomically;
- the natural next node and pre-pause status;
- a durable supervisor snapshot reference;
- the latest complete proposed-candidate reference, when one exists;
- the existing thread ID and event sequence.

All machine-node routers recognize this status and route to one `supervisor_pause` node. That node calls LangGraph `interrupt(...)`. Its resume payload is a validated `SupervisorAction`, and its conditional router returns to the stored destination. The pause node never changes content on its own.

### Live work feed

The existing `EventJournal` remains the durable source. Events receive a versioned, allowlisted payload schema and chronological read support. The normal terminal renderer prints the event at append time; graph state and the event journal do not maintain competing reconstructions of the current passage.

Required event kinds are:

- `flow.phase` — node, phase, and plain-English job;
- `model.start` — provider, configured model, and role;
- `model.heartbeat` — the same context plus PID and elapsed time while silent;
- `proposal.complete` — a complete candidate and its artifact reference;
- `guard.result` — gate, PASS/FAIL/REVISE, and the explicit operational reason returned by that gate;
- `generation.retry` — rejected stage and explicit reason;
- `move.accepted` — accepted move and move index;
- `passage.current` — the passage rebuilt from checkpoint-bound `accepted_moves`;
- `detector.state` — submit, task-ID checkpoint, poll, returned version, and result state;
- `repair.state` — existing repair phases and verification state;
- `supervisor.paused` and `supervisor.action` — pause boundary and confirmed action.

Only complete model results may produce `proposal.complete`. Pipe fragments and raw stdout never enter the work feed. `passage.current` is created from the exact accepted-move update being checkpointed rather than a separate text accumulator.

Substantive events reset the heartbeat timer. Heartbeats reappear only after the configured silent interval.

### Supervisor snapshot

The snapshot is built from the merged checkpoint state at the safe pause boundary plus recent allowlisted work events. It contains only information useful for supervision:

- source/project identity and exact thread ID;
- interrupted node, provider/model/role, and intended next node;
- section job, task mode, and provenance;
- accepted moves and current accepted passage;
- latest complete unaccepted proposal, if any;
- explicit guard verdicts and reason fields;
- retry, rollback, repair, and Pangram status;
- current owner directives and their scopes;
- relevant artifact and event references.

It excludes model prompts, hidden reasoning, child environments, raw provider transcripts, credential values, and unrelated source material.

### Supervisor conversation

The conversational supervisor uses the configured Codex adapter under the separate role `owner_supervisor`. It receives the safe snapshot and the visible supervisor-session transcript. Its structured response distinguishes:

- an answer grounded in snapshot facts;
- stated inferences or uncertainty;
- an optional proposed action;
- the exact checkpoint fields and downstream stages that action would invalidate.

The model cannot write graph state. The CLI renders its answer and, when it proposes an action, asks Joel to confirm the exact normalized action and scope. Malformed output, model failure, or another Ctrl+C leaves the graph paused and changes nothing.

## Confirmed action model

The CLI sends one of the following actions to the paused graph only after confirmation.

### Resume unchanged

Continue from the stored destination. A cancelled model call is rerun from the last valid input checkpoint. An atomic operation completed before the pause is not repeated.

### Reject the visible proposal

Available only when the snapshot identifies a complete, unaccepted proposal. The action records its exact artifact/hash and Joel's reason in branch memory, clears proposal-local results, and returns to generation. It never removes an accepted move. The writer receives the rejected proposal and owner reason for this article so it does not blindly repeat it.

### Roll back accepted moves

Joel selects an integer count and sees the exact moves that will be removed before confirming. The runtime truncates `accepted_moves` and a parallel per-move coverage ledger, recomputes aggregate atom coverage from the retained entries, clears every downstream candidate/audit/detector field, and resumes generation from the retained prefix.

Newly accepted moves record the `covered_unit_ids` returned by the fidelity gate. For a legacy checkpoint that has accepted moves but no per-move coverage ledger, rollback first runs a bounded coverage reconciliation against the existing authority units. A second strict check must validate that mapping. If reconciliation cannot be validated, rollback is blocked and the supervisor offers a full representation restart; the runtime never guesses which removed move carried a required unit.

### Redirect the remaining work

The action stores Joel's exact instruction and one explicit scope:

- `NEXT_ATTEMPT` — consumed after the next applicable generation attempt;
- `CURRENT_ARTICLE` — persists on this thread and is included in applicable representation, generation, audit, and guard inputs;
- `GENERAL_RULE_CANDIDATE` — applies to the current article and creates an unpromoted learning hypothesis. Existing evidence/holdout or explicit-owner-confirmation requirements still control promotion.

The confirmed action also names its restart depth:

- `CURRENT_STAGE` — retry the interrupted stage;
- `GENERATION_FROM_PREFIX` — preserve accepted moves and regenerate from that prefix;
- `REPRESENTATION_FROM_SOURCE` — rebuild the semantic representation and discard downstream prose.

The supervisor must show that restart depth before confirmation. A direction cannot weaken semantic, fidelity, cold-audit, regression, repair, or Pangram gates.

### Correct the meaning or owner position

The exact correction is recorded as owner-grounded authority, the semantic representation is rebuilt from the unchanged source plus that correction, and all accepted prose and downstream detector state are invalidated. The confirmation screen states that consequence. This action cannot edit the source file, policy snapshot, or owner-gold fixtures.

### Leave paused

Exit the supervisor loop without resolving the LangGraph interrupt. No graph action is sent. Running `./RUN.sh` again detects the pending supervisor interrupt and reopens the same snapshot and conversation state.

## State additions and invalidation

New durable state includes the supervisor resume destination, snapshot reference, pause mode, pre-pause status, current and consumed directives, complete rejected-proposal references, per-move coverage, and supervisor-session reference.

Any action that changes prose direction clears stale fields according to its restart depth. At minimum, changing or truncating the accepted prefix clears candidate records, candidate text/spans, entry/full/relation/semantic results that depend on removed prose, cold-audit results, freeze/recommendation references, detector variants/results/task ownership, and owner-review payloads. Regression evidence and immutable source/policy refs remain. A meaning correction additionally rebuilds authority units and their coverage.

If a Pangram task belongs to an invalidated candidate, its local ownership fields are cleared only after the action is checkpointed. The remote task may finish unused; its result cannot be applied to another candidate.

## Privacy and integrity boundaries

- Event payloads use allowlists; arbitrary state dictionaries, prompts, and environments are never printed.
- Existing secret redaction remains a second defense for strings that enter explicit reason fields unexpectedly.
- Candidate text and owner instructions are treated as article content, not as credentials.
- The supervisor receives explicit artifacts and state, never hidden model reasoning.
- Supervisor answers are advisory until Joel confirms a typed action.
- No instruction becomes a global rule silently.
- No supervisor action modifies project inputs, policy files, gold fixtures, or the current thread ID.
- The existing Pangram v4 Human/zero-AI contract remains unchanged.

## Failure behavior

- Supervisor model failure: report the bounded failure and remain paused; do not invoke autonomous code repair merely because a conversational answer failed.
- Malformed proposed action: reject it and remain paused.
- Invalid rollback count or stale proposal reference: reject it and refresh the snapshot.
- Coverage-reconciliation failure on a legacy thread: block partial rollback and offer a representation restart.
- Process termination failure: preserve the existing terminate-then-kill behavior; do not checkpoint partial output.
- Journal read corruption: stop at the last valid complete JSON line, report the damaged tail, and keep the graph checkpoint authoritative.
- Terminal closure while paused: the graph interrupt and supervisor session are durable and reopen on the next run.

## Test-first acceptance criteria

### Pause and checkpoint behavior

1. A SIGINT during a silent child model process terminates the child, discards partial stdout, and reaches a checkpointed `SUPERVISOR` interrupt on the same thread.
2. Resuming unchanged reruns the cancelled node from its last valid input checkpoint without duplicating an accepted move.
3. A pause requested during Pangram submission occurs only after the task ID is checkpointed; resume polls that ID without resubmission.
4. A pause requested during repair promotion reaches supervision only after the promotion boundary is consistent.
5. A second Ctrl+C during a supervisor answer cancels that answer while the graph remains paused.

### Work-feed behavior

6. A fake flow displays proposal → failed guard → retry → proposal → passed guard → accepted move → current passage in exact chronological order.
7. The displayed current passage equals checkpoint-bound `accepted_moves` byte for byte.
8. Heartbeats carry provider/model/role context, stop after substantive events, and resume only after a silent interval.
9. Incomplete subprocess output and raw prompts never become visible events.
10. Repair and Pangram events expose operational state without changing their routes or gates.

### Conversation and action behavior

11. Free-form supervisor questions make no checkpoint mutation.
12. A model-proposed action makes no mutation until Joel confirms it.
13. Resume, proposal rejection, rollback, redirect, meaning correction, and leave-paused each preserve the exact documented state/invalidation contract.
14. Rollback recomputes aggregate coverage from retained per-move entries; a legacy rollback cannot proceed on an unvalidated reconciliation.
15. `GENERAL_RULE_CANDIDATE` remains unpromoted without the existing promotion evidence or explicit confirmation.
16. Stale candidate/event references and malformed actions fail closed.
17. Reopening after leave-paused restores the same thread, snapshot, and visible supervisor conversation.

### Security and regression behavior

18. API keys, credential-bearing environments, raw prompts, and secret fixture values are absent from terminal output, events, snapshots, and supervisor prompts.
19. Existing owner-interrupt, machine-repair, same-thread resume, Pangram-version, and release-package tests remain green.
20. The exact packaged release passes the full deterministic suite and clean-extraction verification.
21. Target Zorin acceptance demonstrates a real bad-looking Thought-Flow run, Ctrl+C during work, supervisor questioning, one confirmed redirect, and same-thread completion or continued pause.

## Expected code boundaries

- `src/authorial_flow/pause.py` — pause controller, dedicated exception, temporary signal context.
- `src/authorial_flow/supervisor.py` — safe snapshot, action schema/validation, state invalidation, and conversation response schema.
- `src/authorial_flow/work_feed.py` — allowlisted event schema, redaction, rendering, and heartbeat quieting.
- `src/authorial_flow/events.py` — chronological reads and corrupt-tail handling while preserving existing append behavior.
- `src/authorial_flow/process_runner.py` — pause-aware child cancellation and contextual heartbeats.
- `src/authorial_flow/models/claude_cli.py` and `codex_cli.py` — model-start context passed to the runner; no transcript streaming.
- `src/authorial_flow/runtime.py` — explicit proposal/guard/accepted/detector events, per-move coverage, pause-aware node wrapper, and owner directives in applicable model inputs.
- `src/authorial_flow/graph.py`, `routing.py`, and `nodes/owner_interrupt.py` — checkpointed supervisor node and resume routing.
- `src/authorial_flow/state.py` — durable supervisor/directive/coverage fields.
- `src/authorial_flow/cli.py` — temporary SIGINT handler, immediate same-terminal session, confirmation, and pending-session reopen.
- Unit, integration, graph-resume, detector, repair, release, and target-smoke tests — one failing regression before each production behavior.
- `README.md`, acceptance matrix, migration/cutover notes, and release checklist — exact user behavior and remaining target-machine validation.

## Non-goals for this release

- Browser dashboard.
- An attachable write-capable supervisor command.
- Automatic supervisor edits or automatic direction changes.
- Hidden chain-of-thought display.
- Streaming raw model stdout as draft prose.
- Automatic global-rule promotion.
- Unbounded rollback, repair, or conversation loops.
- Any weakening of article, fidelity, cold-audit, repair, or detector gates.

## Release boundary

The release remains a candidate after deterministic verification. It becomes target-machine approved only after the exact ZIP passes the existing live Claude/Codex/Pangram checks and the new real Ctrl+C → supervisor conversation → confirmed steering → same-thread continuation acceptance run on Joel's Zorin machine.
