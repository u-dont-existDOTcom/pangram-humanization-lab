# Owner correction — six-call cap applies to sections only — 2026-08-21

Status: **direct Joel owner correction; active protocol authority.**

Joel clarified that the hard six-paid-call Pangram repair cap is **per genuine local repair section**, not per whole article, article half, or other aggregate certification boundary. Treating a long article or arbitrary half as one capped section does not match the purpose of the guard.

Correct rule:

- A genuine local repair section has a hard maximum of **6 new paid Pangram POSTs per stable audit + section + model/version** unless Joel explicitly authorizes a different single-section design.
- Splitting, renaming, changing transport, changing chat, or changing workflow does not reset the same local section's cap.
- A whole article, article half, or other multi-section aggregate certification boundary is **not** a section merely because Pangram receives it in one request.
- Aggregate certification calls remain content-addressed, checkpointed, recovered-before-repeat, version-gated, and durably accounted, but the six-call section cap does not apply to them.
- Aggregate calls should still be decision-changing or required because accepted edits made the previous aggregate result stale; this correction is not permission for gratuitous repeats.
- If a requested deliverable genuinely consists of one natural section, that natural section remains subject to the six-call cap.

Implementation is on `automation/pangram-fixed-batch`: fixed-batch variants use `budget_scope: "section"` (default, capped) or `budget_scope: "aggregate"` (accounted, not section-capped). The repository safety gate passed after this change.

Romance consequence: the historical `part2` ledger remains valid accounting, but its 6/6 count is **not a current blocker** because Part 2 is a multi-section article half, not one repair section.
