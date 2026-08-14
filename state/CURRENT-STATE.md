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

- Draft PR #16 is green at head `87537c744bb45c0c9422c79c1ea87a02ef44f788`: repository policy run `31775055295` succeeded, and lesson-integrity run `31775055265` succeeded with 53 tests plus changed-range and current-ref audits.
- A separate evidence-branch PR is required because paid-workflow definitions live on a divergent long-lived branch and cannot be changed atomically by a PR to `main`.
- No Pangram API call is part of this compliance work.

## Remaining

- Process the metadata-only governance closeout request on PR #16, then confirm the resulting head remains green.
- Harden the evidence branch to one dispatch-only, confirmation-gated paid runner; archive historic task workflows outside `.github/workflows`.
- Promote the transferable paid-workflow lifecycle lesson to `universal-dev-architecture` with source commit/path/hash and limits.
- Recheck hosted settings after repository-visible changes and update hardening-audit issue #17.

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

Allow the same-repository PR workflow to process the pending governance closeout request. Then review the final diff, require fresh green checks on the bot-produced head, make PR #16 review-ready, and merge it before opening the evidence-branch hardening PR.

## Recovery rule

After interruption, fetch actual Git refs and current workflow/PR state before resuming. Never repeat a paid detector submission from chat memory; recover its task ID, cache, ledger, and exact evidence first.
