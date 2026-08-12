# Bounded Failure Control Design

**Status:** Approved for implementation by Joel's 2026-08-12 instruction to fix the reproduced bounded failure.

**Baseline:** `install/authorial-flow-graph-v1-1.1.0-dev1` at remote commit `042b425cd5d2c2fadf4dbce84dc21650e0c89f0b` (tree `01c0822d4e42092f402c7976ba58f7f821516fd7`).

**Preservation mode:** P0 for article and policy material. This release changes runtime control, repair, provider failover, and observability only. It does not edit article prose, owner gold, semantic gold, policy, or promoted learning.

## Incident

The reproduced run reached a bounded generation dead end after accepting an epistemic-arrival move while six protected authority units remained uncovered. The next candidate was correctly classified `STOP_BEFORE_CANDIDATE`, but that verdict was treated as a normal writer rejection. Retry updates also retained an older `OPEN` pressure value, hiding that the current boundary's readers had reached `NATURAL_STOP`. The repair controller then approved essentially the same plan five times even though its prose-form test descriptions could not be executed by the safe test-command parser. Provider fallbacks additionally repeated attempts whose failure class made an equivalent retry futile.

An earlier semantic-sanity response also demonstrated a gate bypass: `status=FAIL`, a research trigger, and an owner question were paired with an unconstrained natural-language `recommended_escalation`. Because runtime routing recognized only four exact strings, the response fell through to ordinary generation.

## Safety invariants

1. A semantic-sanity failure cannot reach generation until every required owner and research action is resolved. Unknown or contradictory escalation data fails closed.
2. Pressure, edge verdicts, and rejection reasons govern only the exact accepted boundary on which they were computed.
3. `STOP_BEFORE_CANDIDATE` is a control decision, not a writer-quality retry.
4. An accepted arrival cannot strand required authority units. The runtime either rejects it before acceptance, rolls it back using a validated coverage ledger, or stops with `POLICY_CONTRADICTION` without another writer call.
5. Every returned `machine_failure`, not just an exception, has dereferenceable, redacted evidence and an originating node before repair routing.
6. The repair loop cannot review or execute the same plan against the same program and evidence twice. Each attempt has one explicit terminal outcome.
7. Provider failover happens only when the next profile is materially different and the failure is retriable there.
8. Decision traces contain hashes, counts, enums, and confidence values—never source prose, candidate prose, prompts, transcripts, or credentials.

## Boundary-scoped generation

`generation_boundary_id(...)` hashes a canonical payload containing the accepted-passage SHA-256, accepted-move count, aggregate coverage SHA-256, graph version, and program version. The runtime computes it before pressure reads. Stored pressure and edge results include that boundary ID. Retry updates always persist the current pressure, boundary ID, proposal hash, rejection class, and bounded counters.

Before accepting a candidate, the runtime applies the existing deterministic arrival detector to the candidate and considers fidelity-gate coverage. If the candidate would arrive while required units remain, it is rejected as `PREMATURE_ARRIVAL` without changing accepted prose.

When an edge gate returns `STOP_BEFORE_CANDIDATE` for the current boundary:

- with no required units uncovered, discard the proposed candidate and finish on the accepted passage;
- with required units uncovered, remove the latest accepted arrival through the validated per-move coverage ledger, recompute coverage from retained rows, and continue;
- if the latest move is not a provable arrival or the ledger cannot be validated safely, return `machine_failure/POLICY_CONTRADICTION` rather than retrying the writer.

Legacy checkpoint fields without a boundary ID are observations only and never control a new boundary.

## Semantic escalation

The structured schema limits `recommended_escalation` to `BASIC`, `P3`, `P4`, `RESEARCH`, or `OWNER`. Runtime normalization independently validates the result and derives a required action queue from all signals:

- a non-empty owner question requires owner resolution;
- `research_trigger=true` requires research;
- `P3`/`P4` requires the applicable developmental path;
- `FAIL+BASIC`, an unknown escalation, or a contradiction returns a fail-closed owner interrupt with a diagnostic reason.

When owner and research are both required, the owner is resolved first, then representation is rerun and research remains required. An owner answer clears only the owner requirement; it does not manufacture a semantic PASS or erase research.

## Failure evidence and decision trace

The guarded-node wrapper normalizes returned machine failures. It preserves a declared failure class, assigns the node origin, creates a `FailureRecord`, materializes a redacted evidence bundle, and stores its content-addressed reference in `failure_record_ref` and `last_error_ref`. If the node already returned a valid evidence reference, the wrapper does not duplicate it.

Evidence and supervisor snapshots include a versioned `decision_trace` with boundary ID, move count, uncovered-required count, pressure vote states/confidences, committed pressure, edge verdict/confidence, candidate hash, rejection class, and current budgets. Work-feed `decision.trace` events use the same allowlist.

## Repair idempotency

`RepairPlan.tests` must contain at least one exact safe local pytest command whenever `repairable=true`; invalid plans are rejected before review. A canonical repair signature hashes the normalized diagnosis, patch summary, target files, safe commands, evidence reference, and program version. Durable state stores bounded repair-history rows containing that signature, outcome, reason, and artifact references.

The cycle exposes four terminal outcomes:

- `APPLIED_VERIFIED` — promoted code passed all gates;
- `STAGED_FOR_OWNER` — only genuine authorial information is missing;
- `REJECTED_WITH_REASON` — plan/review/implementation/verification rejected with an actionable reason;
- `NON_APPLICABLE_STOP` — non-repairable, duplicate, unsafe, or exhausted work must stop.

A duplicate signature on unchanged evidence and program returns `NON_APPLICABLE_STOP` before another review. Rejection details and recent signatures are included in any permitted next planner prompt.

## Provider capability control

Model attempts record a failure kind and a capability signature. Local classification distinguishes authentication, unsupported model, invalid/unsupported schema, structured-output contract violation, timeout/transient process failure, and unknown failure. Authentication, unsupported-model, and invalid-schema failures are not retried with an equivalent profile. Parse/contract failures require a materially different provider/model capability before failover. The live smoke command validates the runtime schema inventory locally and performs one minimal structured-output probe per configured profile rather than discovering the same incompatibility inside a long run.

Runtime services initialize Pangram and research providers lazily, so unrelated tests and flows do not construct live clients merely because a host environment contains a key.

## Acceptance criteria

1. A malformed natural-language escalation cannot reach generation.
2. Owner-plus-research requirements remain pending sequentially; owner resolution alone cannot force PASS.
3. A stale pressure or edge result from boundary A cannot control boundary B.
4. Reproduced arrival-with-uncovered-units either rolls back or returns `POLICY_CONTRADICTION`; writer attempts do not increase indefinitely.
5. An arrival that would strand required units is never accepted.
6. Returned machine failures carry safe, dereferenceable evidence.
7. Duplicate repairs stop before a second plan review, and invalid prose test descriptions never reach the executor.
8. Deterministic provider failures do not trigger equivalent retries; transient failures still may.
9. Decision traces render the exact controller decision and pass secret/prose leak tests.
10. The full deterministic suite, clean install, state-preserving upgrade test, and exact remote-tree verification pass.

