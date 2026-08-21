# Section-only call-cap implementation receipt — 2026-08-21

This branch exists to exercise the repository PR/CI gates against the current `automation/pangram-fixed-batch` implementation after Joel's owner correction that the six-paid-call hard cap applies only to genuine local repair sections.

Expected behavior under test:

- `budget_scope: section` remains capped at six new paid POSTs per stable audit/section/model/version key;
- `budget_scope: aggregate` remains fully accounted but is not stopped at six because an article, article half, or other multi-section certification boundary is not one section;
- cache hits and pending resumes remain non-paid for accounting;
- ambiguous POST reservations remain accounted;
- aggregate and section scope cannot be silently mixed under one accounting key;
- section-cap handoffs are emitted only for section-scoped boundaries;
- no detector call is made by this CI receipt.
