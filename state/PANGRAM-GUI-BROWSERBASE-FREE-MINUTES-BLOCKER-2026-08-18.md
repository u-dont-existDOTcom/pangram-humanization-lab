# Pangram GUI Browserbase — free-minute blocker — 2026-08-18

Status: external account-capacity blocker; no Pangram article-half submission occurred.

## Exact attempted target

Romance source branch: `agent/romance-primal-crucible-gui-repair-20260817`

Reader-visible boundary:
- total words: 20,496
- reader SHA-256: `10359ab2119ffbe9a8a7a4a52cd0c3216bb1a6a2c0bffbd7e66fca01287f17ce`
- Part 1: 10,236 words; SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`
- Part 2: 10,260 words; SHA-256 `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`

The article's card-game URLs were added as Markdown links without changing reader-visible text, so these detector hashes remain current.

## Execution evidence

GitHub Actions repository secrets `BROWSERBASE_API_KEY` and `BROWSERBASE_CONTEXT_ID` were successfully present on the rerun. The job verified both exact input hashes before any browser session was opened.

The read-only `verify` step then failed while creating a Browserbase session with:

`HTTP 402 Payment Required: Free plan browser minutes limit reached. Please upgrade your account.`

Therefore:
- no Pangram detector text was filled;
- no Pangram detector action was clicked;
- no Pangram credits were spent by this attempt;
- no ambiguous Pangram submission exists for either current half;
- it is safe to retry the exact current halves after Browserbase account capacity is restored.

## CI cleanup

A temporary observable PR launcher was added only to prove the execution path and was removed after the 402 blocker was identified. The normal `lesson-integrity.yml` workflow is restored. Temporary push/one-shot Browserbase launchers were also removed/restored; the durable Browserbase runner remains `.github/workflows/pangram-gui-browserbase.yml` on the tooling branch.

## Next safe action

Restore Browserbase browser-minute capacity (plan upgrade or quota reset, as applicable), then run the exact current halves through the existing Browserbase runner. Do not use `--force`; there is no prior Pangram submission for these SHAs. Keep the read-only authentication verification before submission and preserve the no-repeat-on-ambiguous-failure guard.
