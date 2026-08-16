# Pangram section call budget

This is the cost-control contract for Pangram humanization audits and detector-rule research.

## Repair boundary guard

Each tested repair boundary has a maximum of **6 new paid Pangram API POSTs per audit/section key** unless Joel explicitly authorizes a different design.

Budget key:

`audit_id + section_id + detector model + expected result version`

A new fixed batch, workflow, or chat does not reset the count if the `audit_id` and `section_id` are unchanged. A whole-article acceptance test is another boundary with its own section ID.

The six-call guard is primarily a **repair-work safety/cost limit**. It prevents an apparently stubborn passage from turning into open-ended detector optimization.

## Rule-learning research budget

Joel clarified on 2026-08-16 that controlled research into **why successful repairs work** may use a larger budget when there is real expected information value.

Current owner authorization is recorded in `state/PANGRAM-RULE-LEARNING-BUDGET-2026-08-16.md`:

- up to **20 new paid calls** may be used without renewed approval for preregistered rule-learning work;
- this is a program-level allowance beginning after the completed Vows r1/r2 isolation work;
- ask Joel before exceeding 20 new calls;
- stop earlier when the useful rule is already discriminated, a hypothesis fails, or remaining work becomes phrase/token hunting.

The existing six-call key remains a useful local safety guard inside a research program. Multiple section IDs are legitimate only for genuinely distinct boundaries, factor families, replications, or holdouts. Never invent a new section/audit identity merely to reset a cap.

If one genuinely single boundary needs more than six calls for a preregistered factorial or replication design, change the governance/harness transparently with owner authorization rather than disguising the continuation as another boundary.

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

New audited specs use a top-level `audit_id`, and every variant has a `section_id`. The runner persists section call state in:

`state/pangram-call-ledgers/<audit_id>.json`

Result JSON reports, per section:

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

## Local cap reached

Before a seventh paid POST under one unchanged audit/section key, the current runner stops without submitting and writes:

`state/handoffs/pangram/<audit_id>-<section_id>.json`

Reason: `section_call_cap_reached`.

For repair work, report the attempts and ask Joel unless an existing owner authorization clearly covers a different next step. For rule-learning work, do not evade the local guard by relabeling the same boundary; either move to a genuinely distinct replication/holdout boundary or obtain/record authorization for a larger single-boundary design.

## Optimization objective

Repair work should minimize calls-to-Human and estimated credits-to-Human while preserving prose quality.

Rule-learning work has a different objective: maximize **information gained per paid call** about transferable realization/architecture effects. Prefer factorial discrimination, cross-boundary replication, exact repeats of surprising results, counterexamples, and frozen holdouts over lexical subdivision. A detector effect is not promotion-ready merely because it is statistically or numerically large in one passage.
