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
4. The long-lived evidence branch contains historic paid-task workflow definitions at the audited baseline. They require a separate PR because they are not on `main`. Until that PR merges, do not edit or manually dispatch those workflows.

## Verification contract

Expected commands:

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python scripts/audit_codex_github.py --root . --fail-on error
PYTHONPATH=src python -m pangram_lab.lesson_closeout check --base 4eb9e3f76c2d7007682bc92cf0586fe742c61009 --head HEAD
PYTHONPATH=src python -m pangram_lab.lesson_closeout audit --ref HEAD
```

Exact passing run IDs, final head SHA, issue number, and merge commit are intentionally pending until GitHub Actions completes. Update this file rather than claiming success from an in-progress run.
