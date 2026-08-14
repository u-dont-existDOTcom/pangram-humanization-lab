# Evidence-workflow compliance record — 2026-08-14

## Baseline and concurrency check

- Repository: `u-dont-existDOTcom/pangram-humanization-lab`
- Evidence branch baseline: `a413d6d872d31a7f39c2c0ec5b13f270c105cef2`
- Baseline tree: `cd4ecf734f50180ee772b2f41b3b771a14e58c00`
- Active, queued, or pending evidence-branch Actions at branch time: none
- Paid Pangram calls authorized or made by this migration: `0`

The baseline had advanced beyond the earlier audit to include an independently completed r29 sequence. The migration branched from the newer idle head and preserves those commits.

## Finding

Fourteen workflow files were executable on the long-lived branch. Historic task-specific workflows used floating Action tags, broad or missing lifecycle controls, and paid detector jobs reachable from push-path changes. The general runner also retained push/commit-message routing. This made ordinary code/workflow maintenance capable of intersecting credential-bearing paid automation.

## Remediation

- Preserve every baseline workflow using its exact Git blob SHA under a non-executable archive directory.
- Keep one evidence implementation at `.github/workflows/pangram-paid-dispatch.yml`; default branch `main` registers the same path with a snapshot-locked fail-closed stub.
- Run full tests and the repository audit on pushes and pull requests with read-only permissions.
- Permit the detector job only on `workflow_dispatch`.
- Require the exact `RUN_PAID_PANGRAM_FIXED_BATCH` choice.
- Validate the spec under `experiments/`, canonical result identity, non-empty `audit_id`, and every `section_id` before the secret-bearing job exists.
- Serialize runs, bound both jobs with timeouts, and pin checkout/setup-python to full SHAs.
- Scope `contents: write` and `PANGRAM_API_KEY` only to the manual detector job/step.
- Leave the runner, cache, task checkpoints, Git synchronization, result registration, and six-call ledger unchanged.

## Verification contract

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python scripts/audit_codex_github.py --root . --fail-on error
python scripts/validate_paid_dispatch.py --spec <experiments/file.json> --out <canonical-result-or-empty> --confirmation RUN_PAID_PANGRAM_FIXED_BATCH
```

The branch-push workflow must show the `verify` job successful and the `detector` job skipped. No manual dispatch is part of compliance verification.

## Exact verification receipts

- Test-first commit: `0972f557c0b6ec8a14f42989dd2e541d8c33ec8f`.
- Expected RED run: `31776789465`; failure was exactly the missing `scripts.validate_paid_dispatch` module.
- First integrated run: `31777229767`; 73 tests passed and one rejection-message assertion failed, while the detector job was skipped.
- Code-bearing remediation head: `41411b1ec4eb7fb0b2c8fa1c2db416162df30905`.
- Green code-bearing run: `31777325504`; `verify` succeeded, `detector` was skipped, 74 tests passed, and the repository audit reported 0 errors and 5 warnings.
- Security-review RED head/run: `abd78f87850a7a62ff368d0045a7b1ba23217bd2` / `31777929822`; four regressions failed exactly for CR/LF identifiers, surplus untrusted outputs, the missing registered workflow path, and the absent evidence-ref/credential-delay policy while 74 unrelated tests passed.
- Security-remediation head/run: `e140e164828cf3128e1d8f6139fd5d1cd393d487` / `31778048629`; 78 tests passed, the audit reported 0 errors and 5 warnings, paid preflight was skipped, and the detector was skipped.
- Default registration: reviewed PR #22 head `092367b72a819b524575fadd6118513cc7bf7c3c` passed runs `31778554058` and `31778554047`, then merged to `main` as `81b5cd017e3be088c0638e527ce25f5df6a2f4e8`.
- Output boundary: only validated `spec_path` and `result_path` are written to `$GITHUB_OUTPUT`; audit and section identities reject control characters and are not emitted as job outputs.
- Credential boundary: read-only checkouts do not persist credentials; write credentials are enabled only immediately before the final runner step; `PANGRAM_API_KEY` exists only in that step.
- Workflow lifecycle check: 0 of the 14 audited historic workflow paths remain executable; one new registered path is executable, and all 14 archived copies match their documented source Git blob SHAs.
- Manual dispatches made by this migration: `0`.
- Paid Pangram calls made by this migration: `0`.

The report/current-state binding descendants modify documentation only. Before merge, the latest PR head must also have a successful verification run with the detector skipped. Recording that latest run in PR metadata and the post-merge branch receipt avoids an infinite chain in which editing this report creates a new head that itself needs to be written back into the report.

## Exceptions

Hosted evidence-branch protection, secret scanning, push protection, Actions defaults, and vulnerability alerts remain unverified; code scanning is recorded disabled. Main issue #17 owns those settings/plan limits.

## Lesson disposition

- Project detector/editorial ledger: `no-new-lesson`. This is a GitHub workflow-governance repair, not a passage, detector, or humanization finding.
- Cross-project: promote the paid-workflow lifecycle rule and the multi-form privileged-trigger audit regression to `u-dont-existDOTcom/universal-dev-architecture` with this repository, immutable commit/path/blob evidence, tests, and limits.
