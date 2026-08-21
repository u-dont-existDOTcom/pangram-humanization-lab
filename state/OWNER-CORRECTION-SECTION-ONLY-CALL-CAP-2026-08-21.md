# Owner correction — six-call cap applies to sections only — 2026-08-21

Status: **direct Joel owner correction; active immediately.**

Joel clarified that the hard six-paid-call Pangram repair cap is **per actual repair section**, not per article, article half, whole-document certification boundary, or other aggregate boundary. Capping a long article or arbitrary half as though it were one section defeats the purpose of the guard.

## Correct rule

- A genuine local repair section has a hard maximum of **6 new paid Pangram POSTs per stable audit + section + model/version** unless Joel explicitly authorizes a different single-section design.
- Splitting or renaming the same local section does not reset its cap.
- A whole article, article half, or other aggregate certification boundary is **not** a section merely because it is submitted as one detector request.
- Aggregate certification calls must still be content-addressed, checkpointed, recovered before repeat, and durably accounted. They are not subject to the six-call **section** cap.
- Do not spend aggregate certification calls gratuitously: rerun them when an accepted substantive change makes the previous aggregate result stale or when a decision genuinely requires a fresh exact-boundary result.
- If the requested deliverable genuinely consists of one natural section only, that natural section remains subject to the six-call section cap.

## Romance implication

The historical Romance `part2` call ledger grouped a roughly 10k-word article half under one `section_id`. Its six-call count remains valid historical accounting, but **6/6 is not a current blocker** under this owner correction because `part2` is an aggregate half-document boundary, not one natural repair section.

Local residual sections still retain their own six-call limits. The owner-integrated Part 2 can therefore receive a fresh aggregate measurement when editorially warranted without asking Joel to override a nonexistent article-half cap.

## Tooling implication

The fixed-batch harness must distinguish `section` budget scope from `aggregate` certification scope. Both remain accounted; only `section` scope enforces the six-call hard stop.
