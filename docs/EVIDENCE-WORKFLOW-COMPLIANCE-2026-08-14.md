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
- Keep one workflow in `.github/workflows`.
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

## Exceptions

Hosted evidence-branch protection, secret scanning, push protection, Actions defaults, and vulnerability alerts remain unverified; code scanning is recorded disabled. Main issue #17 owns those settings/plan limits.

## Lesson disposition

- Project detector/editorial ledger: `no-new-lesson`. This is a GitHub workflow-governance repair, not a passage, detector, or humanization finding.
- Cross-project: promote the paid-workflow lifecycle rule and the multi-form privileged-trigger audit regression to `u-dont-existDOTcom/universal-dev-architecture` with this repository, immutable commit/path/blob evidence, tests, and limits.
