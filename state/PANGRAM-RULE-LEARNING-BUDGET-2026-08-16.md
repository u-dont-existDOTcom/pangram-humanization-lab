# Pangram rule-learning budget — owner authorization

**Date:** 2026-08-16  
**Scope:** detector/humanization research only; not article authority

Joel clarified that the existing six-call boundary limit was intended primarily as a repair-work cost/safety guard, not as a ceiling on controlled research into why successful owner repairs work.

## First authorization — completed

Joel authorized up to **20 new paid Pangram API calls** without renewed approval for rule-learning work when there was a concrete unresolved causal/generalization question and the work remained controlled rather than phrase hunting.

Required conditions:

- preregister controlled contrasts, factorials, replications, or holdouts;
- preserve exact source/provenance and full detector boundaries;
- preserve meaning as far as the hypothesis permits and label unavoidable confounds;
- keep editorial quality, fidelity, and owner preference independent of detector outcome;
- check cache/results first;
- stop when marginal information value collapses.

The 20-call Vows program is documented in `state/ROMANCE-VOWS-RULE-LEARNING-R1-R4-2026-08-16.md` and ledgered in `state/pangram-call-ledgers/romance-vows-rule-learning-2026-08-16.json`.

Calls used: **20 / 20**. Pending resumes: 0.

## Second authorization — cross-boundary follow-up

After reviewing the Vows findings, Joel explicitly approved **8 additional paid calls** for cross-boundary holdouts/generalization tests.

The follow-up is documented in `state/ROMANCE-CROSS-BOUNDARY-RULE-LEARNING-2026-08-16.md` and ledgered in `state/pangram-call-ledgers/romance-cross-boundary-rule-learning-2026-08-16.json`.

Actual paid calls recorded by the ledger: **9**.

Allocation:

- Talk cumulative-overcompletion holdout: 3;
- Primal source-reporting holdout: 2;
- Primal idiolect factorial: 4.

This is a **1-call authorization overrun**. The Primal idiolect factorial reused an exact text that had just been measured in the source-reporting experiment, but it was submitted under a new measurement key and the runner reserved a fresh paid POST rather than reusing the existing same-text cache record. The pre-run cache audit failed to catch that operational detail. Preserve this as an error in the record; do not retroactively relabel the duplicate as authorized or free.

Pending resumes: 0.

## Relationship to the six-call repair guard

The harness's six-paid-call key (`audit_id + section_id + detector model + version`) remains a useful local boundary safety guard, especially for repair work. It is not the total research-session budget.

Multiple section IDs are legitimate for genuinely distinct boundaries, factor families, replications, or holdouts. Never invent a new identity simply to reset a cap.

## Current stop rule

**No further paid Pangram calls are authorized.** Ask Joel before any additional paid rule-learning or repair call unless a separate explicit authorization is given later.

The cross-boundary tranche materially reduced the value of further immediate calls:

- cumulative overcompletion was detector-causal in Vows but null in the Talk holdout;
- formal source-certification sensitivity in Vows did not reproduce as a classification effect in Primal;
- genericizing two conspicuous owner-idiolect clusters in a 2×2 Primal factorial left every cell Human.

The strongest surviving interpretation of the dramatic Vows lexical flip is a near-threshold boundary/segmentation interaction, not a reusable magic-word or idiolect-seeding rule.

## Tooling follow-up

Before another rule-learning program, inspect/fix cache reuse so identical detector/model/version/text hashes can reuse a completed measurement across experiment-local measurement keys when provenance permits. A same-text baseline should not silently consume another paid POST merely because the experiment gives it a new local ID.
