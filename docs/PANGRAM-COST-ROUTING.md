# Pangram cost-routing policy

Status: **ACTIVE owner policy**

Updated: 2026-08-24

## Rule

Use the authenticated Pangram GUI for large production boundaries. Use the Pangram API for short/local sections.

Operationally:

- full articles, half-article certification boundaries, and other large aggregate production inputs default to `pangram-local run` through the authenticated GUI;
- short natural sections, narrow localization tests, and controlled detector experiments may use the API when the exact cache/reservation/call-ledger gates pass;
- do not send an aggregate/full-boundary production measurement through the API merely because the API route is easier to automate;
- an API call for a large/aggregate boundary requires an explicit owner override for that specific run;
- exact cache hits and read-only History recovery remain non-submission operations and are not affected by this routing rule.

## Reason

Joel reported on 2026-08-24 that approximately $170 had been consumed across roughly 90 Pangram API calls while about $31 in API credit still remained. The working lesson is not to spend API credit on long documents when the authenticated GUI can perform the same large-boundary certification with the existing exact-hash, pre-click reservation, History-binding, and ambiguity protections.

This also corrects an earlier inference from a self-hosted HTTP 402 on a roughly 10k-word request. With the owner reporting substantial API credit still present, that 402 must not be treated as evidence that the account was globally exhausted. Record the transport response exactly, but do not infer account balance from it.

## Classification

The existing fixed-batch `budget_scope` terminology is the first routing signal:

- `section` → API-eligible by default, subject to normal cost/call caps;
- `aggregate` → GUI by default; API blocked unless the owner explicitly overrides the route.

This avoids inventing an arbitrary universal word-count cutoff. If later evidence shows a useful hard word ceiling for API sections, calibrate it from actual Pangram cost data and promote it separately.

## Safety invariants

Changing transport never resets paid-call accounting. Across API and GUI routes:

1. freeze exact reader-visible bytes and SHA-256;
2. inspect completed cache, pending task IDs, ambiguous submissions, GUI reservations, and History before another paid action;
3. never repeat an exact paid measurement merely because the transport changed;
4. require Pangram 4 / version 4.0 evidence;
5. persist reservation/checkpoint/result state before the next paid submission;
6. preserve the six-new-paid-calls per stable audit/section cap unless Joel explicitly changes it.

GUI is a cost-routing choice, not permission to weaken duplicate protection or detector evidence standards.
