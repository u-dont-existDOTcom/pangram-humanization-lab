# Romance final Pangram r3 — credit block — 2026-08-16

## Exact boundary

- article branch: `agent/romance-architecture-map-2026-08-16`
- source Markdown SHA-256: `dbbc02fde8330045a945a45d51b12d87ed386167958e7c9870852caf51c479ff`
- reader-visible SHA-256: `fd47cad5825ab8f3bafd810c4c0b7e0a817edff40bd802edf66dac7247b6412e`
- reader-visible words: `18,248`
- reader-visible bytes: `104,574`
- experiment: `romance-current-master-visible-final-r3-2026-08-16`
- request: `requests/pangram/romance-current-master-visible-final-r3-2026-08-16.json`
- trigger: `triggers/pangram/romance-current-master-visible-final-r3-2026-08-16.json`
- trigger branch: `automation/pangram-fixed-batch`
- workflow run: `31952964278`
- verify job: `95179183840` — success
- detector job: `95179214894` — failed before detector result

## Root cause

The full safety/verification gate passed, including the deterministic suite, repository-visible-controls audit, and hash-bound paid-request validation.

The detector runner then:

1. authenticated successfully enough for the non-billable task API probe;
2. found no cached equivalent for the exact boundary;
3. wrote and pushed a durable call reservation for measurement `romance-current-master-visible-final-r3-2026-08-16_current-reader-visible`;
4. attempted to submit the exact Pangram task;
5. received `HTTP 402` with `{'detail': 'Insufficient credits'}`;
6. wrote and pushed a durable submit-failure record;
7. exited without producing `state/experiments/romance-current-master-visible-final-r3-2026-08-16-results.json`.

This is an account-credit block, not an article, hash, request, trigger, authentication, validator, or workflow-architecture failure.

## Resume rule

Do **not** register a second experiment or create a duplicate paid request. After Pangram credits are replenished, re-run the failed detector job / failed jobs for workflow run `31952964278`. The existing immutable request and trigger remain the intended certification path. Before rerunning, confirm the r3 result file still does not exist.

## Editorial status while blocked

The exact r3 boundary already passed the two whole-article cold audits recorded in `state/ROMANCE-POST-PANGRAM-REPAIR-COLD-AUDIT-2026-08-16.md`.

No further prose edit is justified merely because final certification is credit-blocked. In particular:

- Gandarussa owner wording remains unchanged, with the owner-supplied *Diplomat* link on `Gandarussa`;
- the sexual-exclusivity paragraph remains unchanged after withdrawing the prior social-monogamy conflation;
- Talk/Casual, Primal, and Ending remain protected under the current architecture/provenance dispositions;
- Slow/Turtles and Two Pillars retain the graph-justified repairs already materialized.

## Next action

Replenish Pangram credits, confirm no r3 result exists, then re-run failed job `95179214894` (or failed jobs for run `31952964278`). Inspect the resulting exact-boundary detector evidence before any further editorial action.
