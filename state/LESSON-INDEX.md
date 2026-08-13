# Pangram / humanization lesson index

Use this file as the starting point for current lesson retrieval.

## Required read order

1. `state/WORKING-LESSONS.md` — consolidated lessons through 2026-08-12.
2. `state/WORKING-LESSONS-SUPPLEMENT-2026-08-13.md` — newer Romance detector, semantic-sanity, architecture, routing, provenance, and large-reconstruction lessons. Newer owner correction / controlled evidence here supersedes older conflicting guidance.
3. `state/WORKING-LESSONS-SUPPLEMENT-2026-08-13-HUMANIZATION-GATE.md` — protected rhetorical function, hard detector-acceptance gating when Pangram is explicitly required, trauma-informed language testing, and measured choice-diff rules.
4. For exact evidence behind a lesson, inspect the cited incident note and experiment/result JSON rather than generalizing from the summary.

## Pangram execution/access gate

For every task that requires a measured Pangram result, read `docs/PANGRAM-ACTIONS-RUNBOOK.md` before deciding whether detector access exists. Missing local environment credentials and a signed-out browser session do not establish unavailability. The canonical fallback uses the repository Actions secret through the proven fixed-batch path on `automation/pangram-fixed-batch`.

A worker may use the label `pre-Pangram candidate` only after the runbook's local and GitHub routes have both failed with a recorded blocker. The repository secret remains inside Actions; never retrieve, reveal, print, commit, or ask Joel to paste it.

Joel's standing completion target for requested Pangram humanization is 100% Human on the exact intended delivery boundary: `fraction_human == 1.0`, `fraction_ai == 0.0`, and `fraction_ai_assisted == 0.0` from a successful Pangram 4 result. A Human headline or a partial score such as 93% is not a pass. Continue faithful repair until 100%, or make an explicit unresolved authorial handoff describing the exact span and narrow help needed; never silently stop at the best partial score.

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
- `state/experiments/spiritual-bypassing-invitation-batch-2026-08-13-results.json`
- `state/experiments/spiritual-bypassing-r12-2026-08-13-results.json`
- `state/experiments/spiritual-bypassing-r13-interaction-2026-08-13-results.json`
- `state/experiments/spiritual-bypassing-r14-minimal-alternatives-2026-08-13-results.json`
- exact result JSON under `state/experiments/`

## Authority order

For lesson application:

1. current Joel owner correction / owner-final prose
2. current project edit contract and authoritative article baseline
3. newer controlled experiment with exact boundary/provenance
4. promoted current lesson summaries
5. older incident notes / historical detector outcomes
6. synthetic probes

Detector status is never authorship provenance. Pangram green does not certify natural owner authorship, and Pangram red does not override coherent faithful prose. When Pangram success is an explicit delivery requirement, however, the exact intended delivery boundary must actually pass before the humanization task is called complete.

## Scope

Do not load every historical experiment indiscriminately. Start with the current lesson summaries, then open exact evidence only where the current task needs it.
