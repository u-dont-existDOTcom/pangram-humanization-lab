# Pangram section call budget

This is the cost-control contract for Pangram humanization audits and detector-rule research.

## Repair section guard

Each **genuine local repair section** has a maximum of **6 new paid Pangram API POSTs per stable audit/section key** unless Joel explicitly authorizes a different single-section design.

Budget key for section-scoped repair work:

`audit_id + section_id + detector model + expected result version`

A new fixed batch, workflow, branch, transport, or chat does not reset the count if the same natural repair section is being tested. Splitting or renaming the same section to evade the guard is prohibited.

The six-call guard is primarily a **local repair-work safety/cost limit**. It prevents one stubborn passage or section from turning into open-ended detector optimization.

## Aggregate certification boundaries are not sections

Joel corrected the prior rule on 2026-08-21: a whole article, article half, or other aggregate certification boundary is **not** a section merely because it is submitted to Pangram as one request. Capping a long document or arbitrary 10k-word half at six total measurements does not match the purpose of a section-level guard.

Fixed-batch variants therefore distinguish:

- `budget_scope: "section"` — default; six-call hard cap applies;
- `budget_scope: "aggregate"` — whole-document, half-document, or other multi-section certification/accounting boundary; calls remain fully accounted but the six-call section cap does not apply.

Aggregate scope is **not unlimited permission to waste calls**. Every aggregate call must still satisfy the normal paid-work invariants:

- exact content-addressed cache check first;
- resume/recover pending or ambiguous work before any new POST;
- no duplicate completed exact measurement;
- explicit model/version gate;
- durable reservation/checkpoint/result accounting;
- a fresh aggregate call should be decision-changing or required because accepted edits made the prior aggregate result stale.

If the requested deliverable genuinely consists of one natural section only, that natural section is still section-scoped and remains subject to the six-call guard.

Historical ledgers that grouped an article half or whole document under a `section_id` remain valid accounting evidence, but reaching six calls on that aggregate historical key is **not** a current section-cap blocker.

## Rule-learning research budget

Joel clarified on 2026-08-16 that controlled research into **why successful repairs work** may use a larger budget when there is real expected information value.

Current owner authorization is recorded in `state/PANGRAM-RULE-LEARNING-BUDGET-2026-08-16.md`:

- up to **20 new paid calls** may be used without renewed approval for preregistered rule-learning work;
- this is a program-level allowance beginning after the completed Vows r1/r2 isolation work;
- ask Joel before exceeding 20 new calls;
- stop earlier when the useful rule is already discriminated, a hypothesis fails, or remaining work becomes phrase/token hunting.

The six-call key remains a useful local guard for each genuine section inside a research program. Multiple section IDs are legitimate only for genuinely distinct sections, factor families, replications, or holdouts. Never invent a new section/audit identity merely to reset a cap.

If one genuinely single section needs more than six calls for a preregistered factorial or replication design, change the governance/harness transparently with owner authorization rather than disguising the continuation as another boundary.

## What counts

Counts as a paid call:

- a new detector POST;
- an ambiguous POST attempt that may have reached Pangram;
- a corrective paid POST after a preserved legacy wrong-version task.

Does not count:

- exact content-addressed cache hits;
- authentication probes;
- polling GETs;
- resuming an already-paid pending task.

The ledger reservation must be written and Git-synced before the POST.

## Usage evidence

New audited specs use a top-level `audit_id`, and every accounted variant has a `section_id` plus a `budget_scope` (`section` by default).

The runner persists call state in:

`state/pangram-call-ledgers/<audit_id>.json`

Result JSON reports, per accounting boundary:

- `budget_scope`
- `hard_cap_applies`
- `cap` (`6` for section scope; `null` for aggregate scope)
- `paid_api_calls`
- `cache_hits`
- `pending_resumes`
- `estimated_credits`
- `estimated_cost_usd`
- `paid_calls_to_human`
- `estimated_credits_to_human`
- `first_human_measurement_key`

For rule-learning programs, also maintain a program-level counter in the relevant state note so calls across distinct section IDs cannot silently exceed the owner-authorized total.

Pangram's current public developer pricing is $0.05 for a credit covering up to 1,000 words. The lab therefore estimates each paid submission as `ceil(word_count / 1000)` credits. These values remain explicitly estimated unless the API itself supplies authoritative usage metadata.

## Local section cap reached

Before a seventh paid POST under one unchanged **section-scoped** audit/section key, the current runner stops without submitting and writes:

`state/handoffs/pangram/<audit_id>-<section_id>.json`

Reason: `section_call_cap_reached`.

For repair work, report the attempts and ask Joel unless an existing owner authorization clearly covers a different next step. For rule-learning work, do not evade the local guard by relabeling the same section; either move to a genuinely distinct replication/holdout section or obtain/record authorization for a larger single-section design.

Aggregate certification boundaries never use `section_call_cap_reached`; they remain governed by cache, recovery, decision-value, and exact-boundary certification rules.

## Optimization objective

Repair work should minimize calls-to-Human and estimated credits-to-Human while preserving prose quality.

Rule-learning work has a different objective: maximize **information gained per paid call** about transferable realization/architecture effects. Prefer factorial discrimination, cross-boundary replication, exact repeats of surprising results, counterexamples, and frozen holdouts over lexical subdivision. A detector effect is not promotion-ready merely because it is statistically or numerically large in one passage.
