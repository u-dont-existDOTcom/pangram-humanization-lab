# `.github/` Agent Instructions

- Treat workflow, release, ownership, and repository-policy changes as privileged changes.
- Declare explicit least-privilege `permissions`; begin with `contents: read` and add write scopes only to the smallest job that needs them.
- Pin remote actions and reusable workflows to reviewed full 40-character commit SHAs; retain release tags only as comments and update through reviewed dependency automation.
- Never check out or execute untrusted pull-request code in a privileged `pull_request_target` context.
- Preserve the existing lesson-integrity/closeout gates and exact passage-specific evidence routing; workflow cleanup must not weaken them.
- Keep detector credentials, text supplied under confidentiality, and secret values out of workflows, logs, artifacts, prompts, and state files.
- PR templates must request exact test/detector/audit evidence, editorial semantic review, final-diff review, continuity updates, lesson dispositions, and residual uncertainty.
- CODEOWNERS does not prove branch protection. Do not claim rulesets or hosted scanning controls are enabled without GitHub settings/API evidence.
- Do not rename required checks without verifying and updating the ruleset atomically.
- Run the existing lesson-integrity gate, repository audit, and applicable tests before reporting changes complete.
