# Somatic owner-source restoration — pending execution checkpoint

Date: 2026-09-15
Status: **REQUEST DURABLE / WORKFLOW QUEUED / NO DETECTOR RESERVATION OR RESULT YET**

Experiment: `somatic-owner-source-restoration-20260915-stage1`

Exact candidate:
`state/experiments/somatic-owner-source-restoration-20260915/inputs/F-owner-source-plus-current-tail.txt`

Candidate text SHA-256:
`209691a327a0afd4d9dd221358632ef67ad40b37d67a9ee7afed1810cb73bc43`

Public fixed-batch spec:
`experiments/somatic-owner-source-restoration-20260915-stage1.json` on `automation/pangram-fixed-batch`

Private immutable request:
`requests/somatic-owner-source-restoration-20260915-stage1.json`

Private executor request commit:
`299ec03d9cb210edd1ba7fff4f1ae98fe162d4c8`

GitHub Actions run:
`34913833963` / run number 109

Observed state at checkpoint:

- workflow status: `queued`;
- no in-progress private-executor workflow was reported at the same observation;
- no `state/pangram-call-ledgers/somatic-owner-source-restoration-20260915.json` exists yet;
- no result file exists yet;
- therefore no paid detector POST reservation is durably recorded for this candidate at this checkpoint.

Recovery rule:

1. Inspect run `34913833963` before taking any action.
2. If it later starts/completes, read the canonical ledger/result and continue from that exact evidence.
3. Do **not** create another request or rebuy the candidate merely because this conversation ended while the run was queued.
4. If the queued run is canceled/failed before the detector runner and there is still no ledger reservation/cache/result, then a deliberate retrigger may be considered under the ordinary recovery-before-repeat contract.

This queue state is an execution-availability condition, not detector evidence and not article authority.