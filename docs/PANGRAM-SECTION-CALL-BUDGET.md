# Pangram section call budget

This is the cost-control contract for new Pangram humanization audits.

## Hard cap

Each tested boundary has a maximum of **6 new paid Pangram API POSTs per audit**.

Budget key:

`audit_id + section_id + detector model + expected result version`

A new fixed batch, workflow, or chat does not reset the count if the `audit_id` and `section_id` are unchanged. A whole-article acceptance test is another boundary with its own section ID.

## What counts

Counts against the six-call cap:

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

Pangram's current public developer pricing is $0.05 for a credit covering up to 1,000 words. The lab therefore estimates each paid submission as `ceil(word_count / 1000)` credits. These values remain explicitly estimated unless the API itself supplies authoritative usage metadata.

## Cap reached

Before a seventh paid POST, the runner stops without submitting and writes:

`state/handoffs/pangram/<audit_id>-<section_id>.json`

Reason: `section_call_cap_reached`.

The worker reports the attempts already made and asks Joel for help. Do not silently raise the cap or invent a fresh audit ID solely to buy more attempts.

## Optimization objective

The target is not merely to stay under six. Track calls-to-Human and estimated credits-to-Human so the median paid calls required per successful section can be compared over time. Promoted humanization lessons should drive that number downward.