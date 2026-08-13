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

## Gates

Audit the current ref:

```bash
pangram-lesson-closeout audit --ref HEAD
```

Check only a changed range (used by CI/PRs):

```bash
pangram-lesson-closeout check --base <base-sha> --head HEAD
```

The gate tracks new research artifacts after the configured enforcement timestamp. Older evidence is grandfathered, but any tracked artifact modified after enforcement must be dispositioned for its new exact hash.

## GitHub enforcement

`.github/workflows/lesson-integrity.yml` provides:

1. **Push / pull-request gate** — changed tracked research artifacts must be dispositioned. If a finding is promoted, the canonical index and summary target(s) must be updated in the same range.
2. **Weekly audit** — audits current `main` plus configured long-lived evidence refs. If orphaned research is found, the workflow opens or updates one `Lesson integrity audit: unresolved findings` GitHub issue automatically.

The weekly audit is a backstop for interruptions and workers that skipped closeout. It is not a substitute for the completion gate.

## Work / subagent requirement

Before reporting a substantive pass complete:

1. identify each actual new finding;
2. record its disposition in the ledger (or one `no-new-lesson` record when appropriate);
3. promote durable findings into the current lesson summary/index;
4. run the lesson-closeout audit/check appropriate to the branch;
5. verify the gate passes;
6. only then claim the pass complete.

Do not ask Joel to remind you to do this.
