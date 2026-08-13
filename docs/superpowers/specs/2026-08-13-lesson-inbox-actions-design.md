# Durable lesson inbox + trusted closeout Action design

## Problem

Detector/result evidence is already durable in GitHub, but a chat-side GitHub write can be blocked by the connector safety classifier when the surrounding article concerns sensitive material. A completion process that depends on one final large connector write can therefore leave an experiment without a semantic disposition even though the experiment itself succeeded.

## Goal

Make it impossible for a completed detector experiment to disappear from the lesson-review queue, and make final disposition require only a small metadata request rather than resending article text or detector output through the connector.

## Layer 1: automatic pending inbox

After a fixed-batch result is written, deterministically register its exact path + SHA-256 in `state/LESSON-INBOX.json` on the evidence branch. The entry contains only metadata:

- source path and source ref;
- source SHA-256;
- experiment ID and audit ID when present;
- section IDs and variant IDs;
- detector prediction labels/scores needed for triage, but no copied article body;
- status `pending`;
- creation/update timestamps.

Registration is idempotent. Re-running the same exact artifact does not duplicate the inbox item. A changed artifact hash creates a new review obligation.

This inbox does not claim a lesson exists. It means the artifact must receive a semantic disposition before the editorial/detector task can be called durably closed.

## Layer 2: metadata-only closeout request

Install one trusted main-branch workflow and request processor. Chat-side workers create a small JSON request under `state/lesson-closeout-requests/` containing:

- source path/ref/SHA-256;
- finding text;
- disposition;
- reason when non-promoted;
- promoted destinations when promoted;
- optional Markdown lesson block + target summary path for deterministic append.

The request never contains the source article or detector result body.

The trusted Action verifies the source hash against the named ref, invokes the canonical lesson-closeout logic, updates `state/LESSON-LEDGER.json`, appends a promoted lesson block only when explicitly requested, updates the lesson index when required, resolves the matching inbox entry, runs the lesson-integrity audit, and commits the result. Requests are immutable receipts; processing records outcome rather than silently deleting evidence.

## Completion behavior

A detector task is not durably closed while any result artifact from that audit remains `pending` in the inbox. The weekly lesson-integrity job should surface stale pending inbox items alongside orphaned tracked artifacts.

If a connector blocks the metadata request itself, the pending inbox still preserves the unresolved obligation and exact evidence path for the next worker. This is a degraded-but-durable state, not silent lesson loss.

## Safety and authority

- The Action contains no Pangram key and has no reason to read article bodies except exact source-hash verification through Git.
- It never invents a lesson or promotion; semantic disposition still comes from the editorial/research worker.
- Existing authority rules remain unchanged: promoted summaries are derived views; exact evidence and owner corrections retain provenance.
- No request may mark a changed source hash as reviewed.
