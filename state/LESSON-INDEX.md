# Pangram / humanization lesson index

Use this file as the starting point for current lesson retrieval.

## Required read order

1. `state/WORKING-LESSONS.md` — consolidated lessons through 2026-08-12.
2. `state/WORKING-LESSONS-SUPPLEMENT-2026-08-13.md` — newer Romance detector, semantic-sanity, architecture, routing, provenance, and large-reconstruction lessons. Newer owner correction / controlled evidence here supersedes older conflicting guidance.
3. For exact evidence behind a lesson, inspect the cited incident note and experiment/result JSON rather than generalizing from the summary.

## Completion gate

Before reporting any substantive editorial, detector, reconstruction, or experiment pass complete, use `docs/LESSON-CLOSEOUT.md` and the canonical `state/LESSON-LEDGER.json`.

Every substantive finding must be dispositioned as `promoted`, `provisional`, `article-specific`, `superseded`, or `no-new-lesson`. Promoted findings must update this index plus the current lesson summary. Run the repository lesson-closeout gate before claiming completion. Do not ask Joel to remind you.

## Important branch note

The default `main` branch contains the canonical lesson summaries above, but many of the newest exact incident notes and Pangram-4 experiment/result files currently live on branch:

`automation/pangram-fixed-batch`

A worker that reads only the default branch will therefore have the current promoted lessons but not all exact experimental evidence. For detector work or disputed findings, explicitly inspect that branch.

Key current evidence on `automation/pangram-fixed-batch` includes:

- `state/HISTORICAL-WHITESPACE-AUDIT-2026-08-12.md`
- `state/PANGRAM-WHITESPACE-SENSITIVITY-2026-08-12.md`
- `state/ROMANCE-OXYTOCIN-LOGIC-REPAIR-2026-08-12.md`
- `state/ROMANCE-IDEALIZATION-INCIDENT-2026-08-12.md`
- `state/ROMANCE-PROGRESS-SIGNALS-INCIDENT-2026-08-13.md`
- `state/ROMANCE-DOCTOR-PATIENT-REPAIR-2026-08-13.md`
- `state/ROMANCE-MONOGAMY-POLYAMORY-INCIDENT-2026-08-13.md`
- `state/ROMANCE-ARTIFICIAL-CHECKLIST-INCIDENT-2026-08-13.md`
- `notes/romance-recap-removal-routing-2026-08-13.md`
- exact result JSON under `state/experiments/`

## Authority order

For lesson application:

1. current Joel owner correction / owner-final prose
2. current project edit contract and authoritative article baseline
3. newer controlled experiment with exact boundary/provenance
4. promoted current lesson summaries
5. older incident notes / historical detector outcomes
6. synthetic probes

Detector status is never authorship provenance. Pangram green does not certify natural owner authorship, and Pangram red does not override coherent faithful prose.

## Scope

Do not load every historical experiment indiscriminately. Start with the two lesson summaries, then open exact evidence only where the current task needs it.
