# Pangram async API vs web History recovery boundary — 2026-08-22

## Incident

A Somatic Therapies Pangram 4 measurement had a durable paid-submission reservation but no durable task-id or result checkpoint. Automatic repeat submission was correctly blocked.

A read-only recovery path then opened the authenticated Pangram web History and searched stored records for the exact Shaking Qigong text. Authentication succeeded, 10 History candidates were inspected, no exact record matched, and the recovery itself made no detector submission.

That absence was not enough to decide whether the earlier async API POST had happened, so a zero-cost positive control was run through the same read-only History path.

## Positive control

The control used a Somatic introduction variant with a known successful async API Pangram result (`somatic-therapies-intro-r08-human-anchor-20260822-a`). The authenticated web History recovery again inspected 10 candidates and found no exact match.

Therefore, under the current self-hosted async API route/configuration, absence from the authenticated web History surface is **not evidence that an async API submission never occurred**. A known-success API task can be absent from that History surface.

## Durable operational rule

- Never clear an ambiguous async API paid reservation, reset its budget, or authorize a repeat POST merely because exact text is absent from web History.
- Before using web History absence as negative evidence for any transport, first demonstrate with a known-success positive control from that same transport/configuration that successful submissions are recoverable through the same History surface.
- For the current async API route, web History is non-adjudicative. Resolve ambiguity from durable task-id/cache/ledger evidence or another transport-appropriate exact record.
- Read-only web History recovery remains useful for GUI/history-backed scans where exact stored-record identity is actually established.
- A recovery read is not a detector submission and must remain mechanically unable to POST.

## Exact evidence

- Ambiguous Shaking recovery branch: `evidence/pangram-history-recovery/somatic-shaking-r01-20260822-b`
  - exact text SHA-256: `0f21beb5d6c95c471a13d8b3ff2d373a4541cca61151043203c702286614a181`
  - authenticated History candidates inspected: 10
  - exact match: none
  - recovery detector submission attempted: false
- Known-success async API control recovery branch: `evidence/pangram-history-recovery/somatic-intro-r08-api-control-20260822`
  - exact text SHA-256: `bfd409547d4f680a85fa106ca8c4fb9e7b76f766d6d348d1d6fe4186e590c190`
  - authenticated History candidates inspected: 10
  - exact match: none
  - recovery detector submission attempted: false

## Scope

This finding does not claim that Pangram web History never contains API-originated scans in every product configuration. It establishes the narrower operational fact required for this workflow: **the current async API route cannot be cleared by web-History absence.**
