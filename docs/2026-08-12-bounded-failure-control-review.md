# Bounded Failure Control Review — 2026-08-12

## Scope

This review covers runtime version `1.2.0-dev1`, implemented from the captured bounded-failure checkpoint, event journal, and content-addressed artifacts. Article, owner-gold, semantic-gold, project input, policy, and promoted learning files were not changed.

## Confirmed causes and repairs

1. **Semantic gate bypass:** `recommended_escalation` accepted arbitrary prose and the runtime recognized only exact tokens, allowing a FAIL to fall through. The schema is now enumerated and independent runtime normalization fails closed. Owner resolution no longer manufactures PASS or clears research.
2. **Stale boundary state:** retry updates retained pressure from an earlier accepted prefix. A canonical boundary ID now binds passage hash, move count, coverage hash, graph version, and program version. Every current decision is tagged and every retry persists the current pressure.
3. **Impossible stop retry:** `STOP_BEFORE_CANDIDATE` was treated as ordinary writer rejection after an arrival. It now stops when protected coverage is complete, rolls back a ledger-validated arrival when required meaning remains, or returns `POLICY_CONTRADICTION` without another writer attempt.
4. **Premature accepted arrival:** an arrival could be accepted before required meaning was placed. The post-fidelity coverage check now rejects that candidate before acceptance.
5. **Blind returned failures:** evidence was generated for exceptions but not node-returned machine failures. Both paths now use one redacted evidence normalizer and preserve declared failure class/origin.
6. **Equivalent provider retries:** attempts lacked causal classification. Auth, model support, schema, structured contract, transient, and unknown failures now carry typed evidence and a capability signature; duplicate profiles are removed and deterministic provider-wide failures stop.
7. **Repeated non-executable repair:** prose-form tests passed plan review but failed the safe executor check, causing the same plan to be regenerated. Exact pytest commands are validated before review, signatures bind plan/evidence/program, prior feedback reaches the next planner prompt, and unchanged duplicates stop before another review.
8. **Missing-origin terminal replay:** the live 1.3 resume returned an unchanged legacy `GENERATION_DEAD_END` because that terminal predates returned-failure normalization and contains no `failure_origin_node`. The recovery bridge now derives `generation` from the newest `machine_failure` checkpoint's allowlisted phase, searches only the current terminal lineage for the replay checkpoint, and refuses to cross an older terminal boundary.

## Deterministic verification

- Baseline before repair: `302 passed` with live service keys removed from the test environment.
- Exact release-candidate source run: `329 passed in 8.76s`.
- Focused slices cover semantic escalation, stale boundaries, stop/rollback/contradiction, premature arrival, failure evidence, trace redaction, provider classification, lazy clients, schema inventory, repair signature/history/outcomes, supervisor resume, and security.
- Deterministic release build/verification passed for graph version `1.2.0-dev1`, source checkpoint `063f129a0ef4d157d74b27975abb919f6d032a30`, with project instructions at 3,175 characters and clean-extraction compilation passing.
- A copy of the actual failed thread `f51ae3b6a22e44371ee58c4abbcf49a4e2302fe5cf1a3ec71365d77d3e0daac0` opened under 1.2, returned the legacy terminal checkpoint (`bounded_machine_stop`, three accepted moves), and read ten history records. Its SQLite SHA-256 remained byte-identical before and after the compatibility read: `b88267c0e5611e0e9a7b6ca586f366af3d9e9cba9ba23e7e7a88c90decf297cc`.
- The exact uploaded 29-checkpoint history reproduces the missing-origin case. The corrected selector infers `generation` and chooses checkpoint `1f195df1-418e-682c-800b-ccd4299a3d21`, the newest checkpoint whose `next` is `generation` in the current terminal lineage; it does not select the exhausted `repair` checkpoints or the older terminal lineage.
- Remote-tree verification is recorded after Git publication; live Claude/Codex/Pangram and owner-terminal acceptance remain target-machine planes.

## Remaining live boundary

No build-container result is represented as a live provider, Pangram, terminal-signal, or owner-quality pass. The exact published Git commit still requires the target Zorin install, provider profile smoke, Pangram version-4 downstream result, and one real Ctrl+C supervisor conversation/confirmed action or durable leave-paused continuation.
