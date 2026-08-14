# Lesson Closeout Gate

Every substantive editorial, detector, reconstruction, or experiment pass must close its learning loop before it is called complete.

## Start point

Always begin lesson retrieval with `state/LESSON-INDEX.md`. It defines the current read order, authority order, and branch routing. Do not rely on a memorized older lesson list.

## Completion invariant

Every new substantive finding must receive one disposition:

- `promoted` — transferable enough to enter the current lesson summary/index;
- `provisional` — potentially transferable but still experimental / needs replication;
- `article-specific` — useful only for the named article/span/context;
- `superseded` — retained as provenance but replaced by newer owner correction/evidence;
- `no-new-lesson` — the artifact was reviewed and adds no new transferable lesson.

`experimental` is accepted as an input alias and normalized to `provisional`.

A non-promoted finding requires a reason. A promoted finding must point to both `state/LESSON-INDEX.md` and at least one `state/WORKING-LESSONS*.md` file. During a changed-range check, those promoted targets must actually change in the same range.

## Machine-readable ledger

Canonical ledger: `state/LESSON-LEDGER.json`.

Each entry is bound to the **exact SHA-256 of the source artifact**. If the source artifact changes later, the old disposition no longer satisfies the gate; the changed finding must be reviewed again.

Example commands after installing the repo package:

```bash
pangram-lesson-closeout record \
  --source state/ROMANCE-EXAMPLE-INCIDENT-2026-08-13.md \
  --finding "Functional duplicate recaps should be routed to the live questions that need them." \
  --disposition promoted \
  --promoted-to state/LESSON-INDEX.md \
  --promoted-to state/WORKING-LESSONS-SUPPLEMENT-2026-08-13.md

pangram-lesson-closeout record \
  --source state/experiments/example-result.json \
  --finding "This detector interaction is local to the tested boundary." \
  --disposition provisional \
  --reason "Needs independent cross-case replication."
```

For evidence that exists only on another branch while the canonical ledger is updated on `main`:

```bash
pangram-lesson-closeout record \
  --source state/ROMANCE-EXAMPLE-INCIDENT.md \
  --source-ref automation/pangram-fixed-batch \
  --finding "..." \
  --disposition article-specific \
  --reason "Bound to this Romance section."
```

## Automatic review inbox

New fixed-batch detector results register themselves in `state/LESSON-INBOX.json` on the evidence branch. The inbox entry is metadata-only: exact source path/ref/SHA-256, experiment/audit/section identifiers, variant IDs, and detector triage fields. It does **not** copy the tested article passage.

Registration is idempotent for an exact path/ref/hash. A changed result hash creates a new review obligation. The weekly integrity audit reads the inbox on long-lived evidence refs and treats an item as resolved only when the canonical `main` ledger contains a disposition with the same source path, source ref, and SHA-256.

This is the durable fallback for interrupted sessions or connector safety blocks: even if semantic closeout cannot be written immediately, the experiment cannot silently disappear from review.

## Metadata-only closeout requests

When a direct ledger/index write from chat is blocked or would require resending sensitive article content, create a small request under:

`state/lesson-closeout-requests/<request-id>.json`

The request contains only source identity and semantic disposition metadata: `source_path`, `source_ref`, `source_sha256`, `finding`, `disposition`, `reason`, and `promoted_to`. A promoted request may additionally contain an explicit lesson block, index block, and summary target. It must never contain the source article or detector result body.

The existing trusted `.github/workflows/lesson-integrity.yml` Action processes these requests on `main`. It verifies the named source ref and SHA-256 before mutating canonical state, invokes the canonical closeout logic, applies explicitly supplied promoted blocks idempotently, records the processed request as a receipt, and commits the resulting ledger/index/summary state. The Action has no Pangram secret.

If even the small metadata request is blocked, leave the inbox item pending and report that durable unresolved state. Do not pretend the lesson was saved; do not discard the obligation.

## Gates

Audit the current ref:

```bash
pangram-lesson-closeout audit --ref HEAD
```

Check only a changed range (used by CI/PRs):

```bash
pangram-lesson-closeout check --base <base-sha> --head HEAD
```

The gate tracks new research artifacts after the configured enforcement timestamp. Older evidence is grandfathered, but any tracked artifact modified after enforcement must be dispositioned for its new exact hash. Pending review-inbox items also fail the relevant long-lived-ref audit until a matching canonical disposition exists.

## GitHub enforcement

`.github/workflows/lesson-integrity.yml` provides:

1. **Metadata request processor** — on eligible same-repository pull requests, tests and processes unprocessed closeout requests on the originating PR branch using a narrowly scoped contents-write job.
2. **Push / pull-request gate** — changed tracked research artifacts must be dispositioned. If a finding is promoted, the canonical index and summary target(s) must be updated in the same range.
3. **Weekly audit** — audits current `main` plus configured long-lived evidence refs. If orphaned research or pending review obligations are found, the workflow opens or updates one `Lesson integrity audit: unresolved findings` GitHub issue automatically.

The weekly audit is a backstop for interruptions and workers that skipped closeout. It is not a substitute for the completion gate.

## Work / subagent requirement

Before reporting a substantive pass complete:

1. identify each actual new finding;
2. ensure every new detector result is durably registered for review;
3. record its semantic disposition in the canonical ledger, directly or through a metadata-only closeout request;
4. promote durable findings into the current lesson summary/index;
5. run the lesson-closeout audit/check appropriate to the branch;
6. verify the gate passes;
7. only then claim the pass complete.

Do not ask Joel to remind you to do this.
