# Per-section Pangram budget and usage accounting design

## Goal

Make paid Pangram use measurable and bounded. Every audit boundary has a persistent budget of at most six new paid detector submissions, while cache reuse and pending-task resume remain free for budget purposes. Record enough usage data to show whether future humanization work is becoming cheaper as lessons improve.

## Budget identity

The budget key is `(audit_id, section_id, detector_model, expected_version)`. The six-call cap resets only when a genuinely new `audit_id` begins. Re-running the same section in another batch or workflow inside the same audit must continue the existing count.

A whole-article acceptance boundary is treated as a boundary with its own `section_id` (for example `FULL_ARTICLE`).

## Counted and uncounted operations

Count against the cap:

- every new paid Pangram POST attempt, including an ambiguous POST that may have reached the service;
- any corrective paid POST needed after a legacy wrong-version task.

Do not count against the cap:

- content-addressed cache hits;
- authentication probes;
- polling GET requests;
- resuming an already-paid pending task.

The budget reservation is persisted and Git-synced before the POST so an interruption cannot reset the count.

## Usage record

Persist one usage state file per audit under `state/usage/pangram/<audit_id>.json`. For each section record:

- paid submission count and cap;
- cache hits;
- pending-task resumes;
- submitted word count for each paid POST;
- estimated whole developer credits using `ceil(words / 1000)`;
- estimated cost using the published $0.05 per 1,000-word credit;
- measurement keys and text SHA-256 values.

The detector API response currently does not expose a credit-consumption or remaining-balance field. Therefore usage derived from word counts must be labeled `estimated_credits`, not exact credits. If Pangram later returns authoritative usage metadata, store it separately as `reported_credits` and prefer it in summaries.

Each fixed-batch result JSON must include an audit usage summary so editorial workers do not need to inspect internal state files to report spend.

## Exhaustion behavior

Before a seventh paid POST for the same budget key, fail closed without submitting. Write a handoff JSON under `state/handoffs/pangram/<audit_id>-<section_id>.json` containing the six measured attempts, best measured result available, remaining detector-red windows when available, and the explicit reason `paid_section_budget_exhausted`.

The worker must then ask Joel for help rather than silently raising the cap or starting a new audit merely to reset it.

## Efficiency metric

Record `paid_calls_to_human` and `estimated_credits_to_human` for sections that reach Pangram `Human`. Historical summaries should make it possible to trend median paid calls per successful section over time. The intended direction is downward as promoted lessons improve.

## Compatibility

Legacy fixed-batch v1 specs without `audit_id` or `section_id` continue to run with legacy behavior. New humanization audits must provide them; the operating guide/runbook will require them. No existing historical cache key or detector result is rewritten.