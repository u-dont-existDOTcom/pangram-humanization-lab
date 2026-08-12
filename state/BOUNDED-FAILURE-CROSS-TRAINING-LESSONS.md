# Bounded-failure cross-training lessons — 2026-08-12

Status: incident analysis and provisional runtime design guidance. This is not article copy, a detector phrase rule, or proof that the current interactive supervisor works.

## Evidence boundary

- Evidence package: `authorial-flow-evidence-v1`, reason `bounded-failure`.
- Archive SHA-256: `e63303103cbf799d264773b80d7946676c53c9b9db396b654ab6a6c242022faa`.
- Package integrity: 292 of 292 manifest entries verified.
- Recorded release source: `9683918db65c9907a081d177d22ccd6953f12415`.
- Recorded local baseline: `a304ae377631056b4e96687b0e80fdd25bc1568c`.
- Thread: `f51ae3b6a22e44371ee58c4abbcf49a4e2302fe5cf1a3ec71365d77d3e0daac0`.
- The replay lasted about 15 minutes 44 seconds: about 7 minutes 32 seconds in generation and 8 minutes 12 seconds in repair planning.
- The package records 22 Claude calls with a combined CLI-reported cost estimate of `$1.9484035`: 8 writer calls, 9 pressure-reader calls, and 5 repair-plan reviews. Codex calls are not included in that estimate.

The uploaded thread predates the interactive-supervisor release. Its final resume returned an already terminal `bounded_machine_stop`; it therefore does not validate Ctrl+C attach, live event rendering, or operator actions.

## What failed

The run did not principally fail because the writer could not produce a good next sentence. It entered an internally impossible state.

1. Representation marked semantic sanity `FAIL`, raised unresolved owner questions, and set a research trigger.
2. Generation nevertheless began without an owner answer or research resolution.
3. Three moves were accepted. The third occupied the natural stopping position while six required authority units remained uncovered.
4. At the resulting boundary, the committed pressure state said `OPEN` with confidence `0.99`, while the entry-edge guard said `STOP_BEFORE_CANDIDATE` with confidence `0.96` because the passage had arrived.
5. The runtime treated an `OPEN` vote as a stop veto, so it kept asking the writer for continuations. The edge guard then rejected those continuations as reopening after arrival.
6. Four retries could not succeed because the governing invariants contradicted one another.
7. The repair loop generated and approved substantially the same plan five times, but did not apply it and did not stop after learning that it had no new plan.

The initial attempt also repeated deterministic provider failures: one provider returned plain text where structured output was required; Codex fallbacks repeatedly encountered an invalid JSON schema or an unsupported model. Equivalent retries could not change those facts.

## Confirmed incident lessons

### 1. A failed gate must alter control flow

Semantic sanity, unresolved authorial information, and required research cannot be advisory annotations. A blocking result must route to exactly one of:

- owner clarification;
- bounded research;
- an explicitly labeled provisional branch; or
- a bounded stop.

Generation must be unreachable until the gate has a recorded resolution. This is the executable form of the Romance lesson “touch base with reality before humanization.”

### 2. Local sentence acceptance requires global sequence feasibility

A locally faithful sentence can still make the article impossible to finish. Before accepting a move, the graph must ask whether the remaining required units can still be placed before the declared stopping point.

Required invariant:

> A terminal or arrival move cannot be accepted while required units remain uncovered unless each remaining unit has an authorized `bank`, `defer`, or `omit` disposition with a reason.

This operationalizes two existing editorial lessons: architecture before sentences, and optimize for the next necessary move rather than merely for a plausible local move.

### 3. Stop/continue state must be boundary-scoped

Pressure votes and edge judgments must name the exact boundary they evaluate: accepted-passage hash, accepted-move count, coverage-state hash, and state version. A pressure result from an earlier boundary must not veto stopping at a later boundary.

If the current pressure adjudicator says `OPEN` while the current entry edge says the passage has arrived and any continuation would reopen it, the runtime should emit `POLICY_CONTRADICTION`. It should not spend another writer attempt trying to satisfy both.

### 4. Provider failures need capability-aware retry policy

Authentication failures, unsupported models, invalid schemas, and structured-output contract violations are deterministic for the same provider/model/request contract. They should be classified as non-retriable until at least one relevant capability changes.

Before a live run:

- validate every structured schema against each configured provider;
- verify the requested model is available to the current account;
- run a minimal structured-output contract probe; and
- fail over only to a provider/model pair whose capability profile differs materially.

### 5. Repair needs an effect stage and idempotence

An approved repair plan must lead to one of four explicit outcomes:

- applied and verified;
- staged for human approval;
- rejected with a new reason; or
- declared non-applicable and stopped.

Hash the normalized diagnosis and plan. If the same approved plan recurs against the same program version and failure evidence, do not pay for another review. Stop or escalate.

### 6. Repair evidence must preserve decision causality

Counters alone are insufficient. The true failure was a contradiction between current decisions, not merely “too many retries.” Content-safe repair evidence should include:

- boundary hash and state version;
- accepted-move count and uncovered-required-unit count;
- whether the latest accepted unit is marked terminal/arrival;
- current pressure votes, adjudicated state, and confidence;
- current edge verdict and confidence;
- candidate hash and rejection class; and
- retry and budget counters.

Raw source or candidate prose is not needed to diagnose this class of failure.

### 7. Supervisor visibility should expose the contradiction

The operator view should show, for the current boundary:

- accepted-move count;
- uncovered required units;
- pressure votes and the committed pressure state;
- edge verdict;
- candidate disposition;
- retry reason; and
- whether the graph is blocked on owner judgment, research, or a policy contradiction.

Heartbeats that show only a PID and elapsed time prove liveness, not progress. The interactive supervisor is aimed at this visibility problem, but needs a fresh nonterminal run to validate it.

## Cross-training synthesis

The Romance training and this bounded failure point to the same upstream principle from different directions:

- Romance: polished prose cannot rescue a defective or incomplete thought.
- This run: a sophisticated graph cannot rescue advisory gates and contradictory state.

The shared rule is:

> Do not ask the downstream system to compensate for an unresolved upstream decision.

That yields four reusable practices:

1. Perform an ordinary-reality check before abstract architecture.
2. Turn important editorial principles into route-changing invariants, not prompt reminders.
3. Evaluate the next sentence by what it makes possible for the remaining argument.
4. Separate publication optimization from capability training: reuse good owner prose for publication, but require fresh syntax when the experiment is meant to test generation ability.

## Recommended repair order

1. Enforce the semantic-sanity/owner-information/research gate.
2. Add boundary identity and detect pressure/edge policy contradictions.
3. Add ordered coverage feasibility before accepting arrival moves.
4. Preflight provider/model/schema capabilities and classify deterministic failures.
5. Add repair-plan deduplication plus an explicit apply/stage/stop outcome.
6. Extend structural evidence and supervisor rendering with the current decision trace.

## Not established by this package

- It does not prove a universal detector phrase rule.
- It does not show that Claude or Codex is intrinsically better at pressure reading.
- It does not validate the newly published interactive supervisor.
- It does not justify modifying the article or merging the Romance candidate.
- It does not establish that every single `OPEN` vote should be ignored; it establishes that vote scope, freshness, and conflict precedence must be explicit.
