# Pangram exact-text repeat recovery incident — 2026-08-21

Status: **tooling incident + repaired generic paid-work invariant**.

## Incident

During Romance Part 1 recovery, a multi-variant fixed batch had already written durable paid reservations for later variants while the result artifact was only partially visible to the worker. The worker incorrectly inferred that missing result visibility meant those variants had not been submitted and created isolated recovery requests using new measurement keys.

At least two exact texts were consequently submitted twice. The duplicate cache records have the same text SHA but different Pangram task IDs. These are real paid duplicate tasks and remain counted; the incident is not reconciled away as bookkeeping noise.

## Root cause

The Pangram cache is content-hashed at the directory level but measurement-key-specific at the record filename. `detect_cached()` therefore looked up only the current measurement key. Before this repair, the tracked client did not check whether the same audit + natural section + model/version already contained a paid or reserved event with the exact same text SHA under another measurement key.

Thus:

- result-file visibility was weaker than the durable call ledger;
- changing the measurement key could bypass an existing pending exact-text reservation;
- the six-call section ledger still counted the duplicate correctly, but it did not prevent the duplicate before submission.

## Repair

On `automation/pangram-fixed-batch`:

- `TrackedPangramClient` now checks same-audit/same-section/model/version call-ledger history for the exact text SHA before reserving a new paid call;
- a second measurement key for the same exact text raises `ExactTextRepeatBlocked` before POST;
- deliberate preregistered exact replication requires explicit `allow_exact_repeat: true` in the fixed-batch variant;
- the fixed-batch parser validates that override as boolean and exposes it in result provenance;
- regression coverage lives in `tests/test_tracked_pangram_repeat_guard.py`;
- `state/tooling-receipts/exact-repeat-guard-20260821.txt` records a green test run covering repeat guard + fixed batch + call budget.

## Transferable invariant

**Result visibility is not paid-call state authority.** Before any recovery POST, inspect the durable reservation ledger and exact text SHA across measurement keys. A missing or delayed result artifact does not authorize a new submission.

**Measurement-key changes do not create new detector work.** Exact same text in the same audit/natural section/model/version is a duplicate by default. Require explicit replication intent to buy it again.

This invariant complements, rather than replaces, content-addressed cache, pending-task resume, ambiguous-submit preservation, and section call budgets.
