## Goal

State the intended software, experiment, editorial, lesson, or automation outcome and explicit non-goals.

## Change

Name affected code, cases, evidence, lessons, branch routing, and any hosted GitHub setting touched.

## Acceptance and verification evidence

List exact targeted commands, the full deterministic test command, repository audit, lesson-integrity checks, and GitHub Actions run URLs or IDs. Separate passed evidence from unavailable or unverified controls.

## Detector, credential, and semantic impact

State whether meaning, owner-final prose, cache identities, task IDs, paid calls, detector evidence, secrets, or workflow permissions changed. A compliance-only PR must explicitly say that it made no paid detector call.

## Lesson closeout

List each substantive finding and its disposition, immutable evidence pointer, limits, and promoted index update when applicable.

## Declared exceptions

Name every remaining exception, why it could not be remediated, its risk, owner, and durable follow-up issue.

- [ ] Final diff reviewed
- [ ] `python -m pytest -q` passes
- [ ] `python scripts/audit_codex_github.py --root . --fail-on error` passes
- [ ] Lesson changed-range check and current-ref audit pass
- [ ] No credential, untrusted-PR, or duplicate-call risk introduced
- [ ] No paid detector call was made unless this PR explicitly authorizes and accounts for it
