# Codex + GitHub compliance record — 2026-08-14

## Scope

Repository: `u-dont-existDOTcom/pangram-humanization-lab`  
Canonical baseline: `main@4eb9e3f76c2d7007682bc92cf0586fe742c61009`  
Evidence baseline: `automation/pangram-fixed-batch@88d225f36d6da8de9b8cbff8fa11b999d01d749a`  
Classification: private, active, long-running, high-risk software/research harness.

This record separates repository-visible facts from GitHub-hosted settings. No Pangram detector call was made or authorized during this audit.

## Repository-visible remediation

- Added the canonical portable audit and a test that requires zero error-level findings.
- Replaced the workflow-policy inline scanner whose source text triggered its own `pull_request_target` check.
- Recorded exact non-interactive bootstrap, full/targeted test, repository-audit, lesson-audit, and interactive-run commands.
- Made `state/CURRENT-STATE.md` the only canonical checkpoint.
- Removed top-level issue-write permission from lesson integrity; write permissions remain job-scoped.
- Added Python Dependabot coverage, a private-reporting policy, and stronger PR evidence requirements.
- Kept every remote Action pinned to a reviewed 40-character commit SHA.

## Hosted-setting observations

| Control | Observed state | Evidence and limit |
|---|---|---|
| Default branch protection | Disabled | The `main` branch API returned `protected: false`. |
| Repository rulesets | Unavailable on current plan | The rulesets endpoint returned HTTP 403 with GitHub's private-repository plan-limit message. |
| Code scanning | Disabled | The default-setup endpoint returned HTTP 403 stating that code scanning is not enabled. |
| Secret scanning | Unverified | The connected integration could not read this setting; no inference was made. |
| Push protection | Unverified | The connected integration could not read this setting; no inference was made. |
| Actions default permissions | Unverified | The connected integration returned HTTP 403 for this administration endpoint. |
| Vulnerability alerts | Unverified | The connected integration returned HTTP 403 for this administration endpoint. |
| Evidence-branch protection | Unverified | The connected integration could not read branch protection for the slash-named long-lived ref. |

## Declared exceptions and residual risk

1. `main` has no enforceable required-check rule under the current private-repository plan. Repository workflows provide evidence but cannot prevent an administrator from bypassing them. Owner: repository owner. Follow-up: hardening-audit issue.
2. Secret scanning, push protection, Actions defaults, and vulnerability alerts remain unverified. Treat every credential-sensitive change as high risk until an owner verifies them in GitHub Settings. Owner: repository owner. Follow-up: hardening-audit issue.
3. Code scanning is disabled. This repository has no runtime dependencies today, but Python and shell automation still warrant future evaluation. Owner: repository owner. Follow-up: hardening-audit issue.
4. Evidence PR #19 replaces the historic paid-task workflows with one evidence-ref-bound implementation. GitHub requires its `workflow_dispatch` path to exist on the default branch, so prerequisite PR #22 adds a no-secret, no-checkout, fail-closed registration stub at the same path. Do not manually dispatch either candidate during migration.
5. No recognized dependency lockfile exists. The package currently declares no runtime dependencies and only a broad pytest test extra; monthly Python Dependabot coverage reduces but does not eliminate resolution drift. Track this in issue #17.

## Verification contract

Expected commands:

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python scripts/audit_codex_github.py --root . --fail-on error
PYTHONPATH=src python -m pangram_lab.lesson_closeout check --base 4eb9e3f76c2d7007682bc92cf0586fe742c61009 --head HEAD
PYTHONPATH=src python -m pangram_lab.lesson_closeout audit --ref HEAD
```

## Verification evidence

- TDD red checkpoint: lesson-integrity run `31774735028` failed exactly at `tests/test_codex_github_audit.py` because the audit module did not yet exist.
- Universal-audit import defect: runs `31774980341` and `31774980358` failed because the inherited regex placed a second inline multiline flag after an alternation; commit `87537c744bb45c0c9422c79c1ea87a02ef44f788` corrected the compile failure.
- First clean baseline: repository-policy run `31775055295` and lesson-integrity run `31775055265` succeeded on `87537c744bb45c0c9422c79c1ea87a02ef44f788`; 53 tests and both lesson gates passed.
- Security-review TDD checkpoint: lesson-integrity run `31775842762` failed exactly four previously undetected but valid `pull_request_target` YAML forms while 56 other tests passed.
- Code-bearing review remediation: repository-policy run `31775932523` and lesson-integrity run `31775932515` succeeded on `61f86ae74908447c92e6320b815b07cd60d9125a`; 60 tests, changed-range closeout, and current-ref audit passed.
- Final synchronization head before this report correction: repository-policy run `31776130741` and lesson-integrity run `31776130748` succeeded on `752fea76088d10c37b128e19bff9ecfb366e6fc7`.
- Governance closeouts: `L-6b3333a2c4-01` and post-review `L-e96b341584-01`, both `no-new-lesson`.
- Final report-correction closeout path: `state/lesson-closeout-requests/codex-github-compliance-final-2026-08-14.json`; its processed receipt is authoritative.
- Durable hosted-control follow-up: issue #17, https://github.com/u-dont-existDOTcom/pangram-humanization-lab/issues/17
- PR: #16, https://github.com/u-dont-existDOTcom/pangram-humanization-lab/pull/16

## Paid-route follow-up evidence

- Main compliance PR #16 merged as `8bf49ac0132c2fa55429d78d4ab79997081413a3`; post-merge repository-policy run `31776570388` and lesson-integrity run `31776570359` succeeded.
- Independently authorized lesson closeout advanced `main` to migration baseline `62495d48208136327c5e3da9bb8bc59e5f876d92`; prerequisite PR #22 branches from and preserves that head.
- Default-registration TDD RED run `31778121462` failed exactly because `.github/workflows/pangram-paid-dispatch.yml` did not exist; 61 unrelated tests passed.
- Registration code head `928ea5ccf82360a80a20beac95d731d608ece5d6` passed lesson-integrity run `31778173435` with 62 tests and both lesson gates, plus repository-policy run `31778173455` with 0 audit errors and 5 warnings.
- Evidence-route security TDD RED run `31777929822` exposed four exact gaps: CR/LF audit/section IDs, surplus untrusted outputs, missing registered path, and absent evidence-ref/credential-delay policy.
- Evidence code head `e140e164828cf3128e1d8f6139fd5d1cd393d487` passed run `31778048629`: 78 tests, 0 audit errors, detector skipped.
- Default-branch registration contains no Pangram secret, checkout, paid runner, push trigger, or pull-request trigger; it exits with an error if run from `main`.
- No manual workflow dispatch or paid Pangram call was authorized or performed.
- Lesson closeout: no new project humanization lesson; promote the default-registration requirement, output-file injection regression, and credential-delay boundary with immutable source evidence to `universal-dev-architecture`.

The exact code-bearing remediation and its validation are recorded above. Later documentation and closeout-receipt commits do not alter executable behavior, but the latest PR head must still show executable green policy and lesson-integrity jobs before merge. The PR check suites and PR body are the authoritative final-head evidence; this durable report records exact code-bearing SHA/run evidence without pretending a file can contain its own commit SHA.
