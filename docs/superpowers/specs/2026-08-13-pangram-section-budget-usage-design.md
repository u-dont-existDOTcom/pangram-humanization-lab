# Per-section Pangram budget and call accounting design

## Goal

Make paid Pangram use measurable and bounded. Every tested boundary has a persistent budget of at most six new paid detector submissions per audit, while cache reuse and pending-task resume remain free for budget purposes. Record enough evidence to show whether future humanization work is becoming cheaper as lessons improve.

## Budget identity

The budget key is `(audit_id, section_id, detector_model, expected_version)`. The six-call cap resets only when a genuinely new `audit_id` begins. Re-running the same section in another batch or workflow inside the same audit continues the existing count.

A whole-article acceptance boundary is treated as another section with its own `section_id`, such as `FULL_ARTICLE`.

## Counted and uncounted operations

Count against the cap:

- every new paid Pangram POST attempt, including an ambiguous POST that may have reached the service;
- any corrective paid POST needed after a legacy wrong-version task.

Do not count against the cap:

- content-addressed cache hits;
- authentication probes;
- polling GET requests;
- resuming an already-paid pending task.

The call reservation is persisted and Git-synced before the POST so an interruption cannot reset the count.

## Call record

Persist one call ledger per audit under `state/pangram-call-ledgers/<audit_id>.json`. For each section record:

- paid API call count and cap;
- cache hits;
- pending-task resumes;
- submitted word count for each paid POST;
- estimated developer credits using `ceil(words / 1000)`;
- estimated cost using the published $0.05 per 1,000-word credit;
- measurement keys and text SHA-256 values.

Pangram's current AI-detection response does not expose a credit-consumption or remaining-balance field. Word-count-derived values are therefore labeled `estimated_credits`, not exact credits. If Pangram later returns authoritative usage metadata, store it separately as `reported_credits` and prefer it in summaries.

Each fixed-batch result JSON includes call accounting so editorial workers can report spend without opening the internal ledger.

## Exhaustion behavior

Before a seventh paid POST for the same budget key, fail closed without submitting. Write a handoff JSON under `state/handoffs/pangram/<audit_id>-<section_id>.json` with reason `section_call_cap_reached`, the section's call summary, and completed results already available in the batch.

The worker then asks Joel for help rather than raising the cap or manufacturing a new audit merely to reset it.

## Efficiency metric

For a section that reaches Pangram `Human`, the result records `paid_calls_to_human`, `estimated_credits_to_human`, and the first successful measurement key. Historical summaries can therefore trend paid calls per successful section. The intended direction is downward as promoted lessons improve.

## Compatibility

Legacy fixed-batch v1 specs without `audit_id` or `section_id` continue to run with legacy behavior. New humanization audits provide both identities. No existing historical cache key or detector result is rewritten.