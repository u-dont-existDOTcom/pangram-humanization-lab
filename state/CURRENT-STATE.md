# Pangram Humanization Lab current state

Updated: 2026-08-14

## Goal

Preserve the lab's exact detector-evidence, editorial, and lesson-closeout architecture while making the Codex + GitHub operating path recoverable, least-privileged, and safe around paid detector work.

## Authority / baseline

- Canonical branch: `main` at baseline commit `4eb9e3f76c2d7007682bc92cf0586fe742c61009`.
- Long-lived evidence branch: `automation/pangram-fixed-batch` at audited baseline `88d225f36d6da8de9b8cbff8fa11b999d01d749a`.
- Start lesson recovery at `state/LESSON-INDEX.md`; start repository documentation at `docs/INDEX.md`.
- Current owner instructions, exact repository evidence, and tests outrank historical chat.

## Completed

- Exact bootstrap, test, focused-test, repository-audit, lesson-audit, and interactive-run commands are recorded in `.github/codex-repository.json`.
- `state/CURRENT-STATE.md` is the single canonical recovery checkpoint; the older Codex-named file is a redirect only.
- The portable universal repository audit is covered by a repository regression test and invoked by the workflow-policy gate.
- Workflow permissions are job-scoped where writes are required; remote Actions remain pinned to full commit SHAs.
- Hosted-setting observations and plan/integration limits are recorded without guessing.

## Current checkpoint

- Draft PR #16 contains the default-branch baseline and is awaiting final GitHub Actions evidence.
- A separate evidence-branch PR is required because paid-workflow definitions live on a divergent long-lived branch and cannot be changed atomically by a PR to `main`.
- No Pangram API call is part of this compliance work.

## Remaining

- Obtain green full-test, lesson-closeout, and repository-audit checks for PR #16.
- Harden the evidence branch to one dispatch-only, confirmation-gated paid runner; archive historic task workflows outside `.github/workflows`.
- Promote the transferable paid-workflow lifecycle lesson to `universal-dev-architecture` with source commit/path/hash and limits.
- Recheck hosted settings after repository-visible changes and close or update the hardening-audit issue.

## Blockers / unresolved

- GitHub rulesets for this private repository returned a plan-limit error; `main` is verified unprotected.
- The connected integration could not read Actions default permissions, vulnerability alerts, secret scanning, or push protection. These remain `unverified`.
- Code scanning returned disabled. Enabling it may require plan/owner action and a language-appropriate configuration.

## Evidence / artifacts

- Repository profile: `.github/codex-repository.json`
- Compliance record: `docs/CODEX-GITHUB-COMPLIANCE-2026-08-14.md`
- Implementation plan: `docs/superpowers/plans/2026-08-14-pangram-codex-github-compliance.md`
- Required checks: `.github/workflows/lesson-integrity.yml` and `.github/workflows/repository-workflow-policy.yml`
- PR: https://github.com/u-dont-existDOTcom/pangram-humanization-lab/pull/16

## Next safe action

Wait for PR #16 checks. If all repository-visible gates pass, update this checkpoint with exact run IDs, make the PR review-ready, and merge it before opening the evidence-branch hardening PR.

## Recovery rule

After interruption, fetch actual Git refs and current workflow/PR state before resuming. Never repeat a paid detector submission from chat memory; recover its task ID, cache, ledger, and exact evidence first.
