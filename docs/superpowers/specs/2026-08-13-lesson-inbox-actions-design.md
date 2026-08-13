# Durable lesson inbox + trusted closeout Action design

## Problem

Detector/result evidence is already durable in GitHub, but a chat-side GitHub write can be blocked by the connector safety classifier when the surrounding article concerns sensitive material. A completion process that depends on one final large connector write can therefore leave an experiment without a semantic disposition even though the experiment itself succeeded.

## Goal

Make it impossible for a completed detector experiment to disappear from the lesson-review queue, and make final disposition require only a small metadata request rather than resending article text or detector output through the connector.

## Layer 1: automatic pending inbox

After a fixed-batch result is written, deterministically register its exact path + SHA-256 in `state/LESSON-INBOX.json` on the evidence branch. The entry contains only metadata: source path/ref/SHA-256, experiment/audit/section identifiers, variant IDs, detector triage fields, status, and timestamps. It does not copy the tested passage.

Registration is idempotent. Re-running the same exact artifact does not duplicate the inbox item. A changed artifact hash creates a new review obligation. The inbox does not claim a lesson exists; it records that the artifact needs a semantic disposition before durable closeout.

## Layer 2: metadata-only closeout request

Chat-side workers may create a small JSON request under `state/lesson-closeout-requests/` containing source identity plus finding/disposition metadata. The request never contains the source article or detector result body.

The existing trusted `lesson-integrity.yml` Action verifies source ref/hash, invokes canonical closeout logic, updates `state/LESSON-LEDGER.json`, applies explicitly supplied promoted blocks idempotently, and records the processed request as a receipt. The workflow has no Pangram secret.

## Completion behavior

A detector result remains unresolved while its evidence-ref inbox item lacks a canonical ledger entry matching source path, source ref, and exact SHA-256. The weekly lesson-integrity audit surfaces these pending obligations alongside ordinary orphaned research.

If even the metadata request is blocked, the inbox still preserves the unresolved obligation and evidence identity for the next worker. This is a degraded-but-durable state, not silent lesson loss.

## Safety and authority

- The request path never needs the source prose.
- The Action never invents a lesson or promotion; semantic disposition still comes from the editorial/research worker.
- Existing authority rules remain unchanged: owner correction and exact evidence outrank summaries.
- No request can review a changed source hash.
