# Pangram local Playwright GUI transport

Status: supported on `main`; live-certified on Joel's Zorin/Brave machine.

## Purpose

This is the local authenticated-browser fallback for Pangram. The self-hosted Pangram API is the normal programmatic transport when available; this GUI path remains useful for visual evidence, authenticated History recovery, and resilience when API access or report inspection is insufficient.

It uses a dedicated persistent browser profile rather than the owner's ordinary browser profile. The normal local transport does **not** require Browserbase. The shared `gui_browserbase.py` module is retained because it contains the older GUI parsing/evidence primitives and the optional remote Browserbase adapter; local execution launches Brave/Chromium directly through Playwright.

## Install

From a repository virtual environment:

```bash
python -m pip install -e '.[test,browser]'
playwright install chromium
```

On Joel's Zorin machine, the validated browser is Brave at `/opt/brave.com/brave/brave`; the runner also discovers common Chromium/Chrome executables.

## One-time authentication

```bash
pangram-local bootstrap
```

The browser profile defaults to `~/.config/pangram-local-browser`. Finish login in the visible dedicated browser and return to the terminal when the dashboard is ready.

Read-only verification:

```bash
pangram-local verify
```

No detector text is filled or submitted by `verify`.

## Submit an exact file

```bash
pangram-local run --input path/to/text.txt
```

For a pre-authorized immutable boundary, add an exact hash gate:

```bash
pangram-local run \
  --input path/to/text.txt \
  --expect-sha text.txt=<sha256>
```

Multiple `--input` values are allowed. If `--expect-sha` is used, every input must have a matching hash gate.

## Completion and duplicate safety

The current long-document Pangram dashboard is a SPA. A rendered report page is not sufficient evidence that the report belongs to the submitted text. The runner therefore:

1. verifies the authenticated detector surface;
2. prepares and hashes the exact input;
3. writes and Git-pushes a `submission-reservation.json` before the detector click;
4. attaches the authenticated History API response listener before the click;
5. submits once;
6. accepts completion only when `/api/history/<uuid>/` contains the same document under the bounded exact-text contract;
7. reads Pangram 4's explicit structured `response.overall` result rather than guessing score semantics from `prediction_prob`;
8. captures a labeled report PDF and persists the result before another input may proceed.

A reservation without a complete result blocks automatic repeat submission. A failure after the click is therefore recover-first, not retry-first. `--force` is an explicit dangerous override and should be used only after evidence review establishes that another paid submission is actually intended.

## Read-only recovery

```bash
pangram-local recover --input path/to/text.txt
```

Recovery opens Pangram's authenticated application History, reads the SPA's `history-list` records, opens stored report records read-only, and accepts only an exact/bounded stored-text match. It does not click the detector action.

The accepted transport-only text normalizations are deliberately narrow: exact UTF-8, line-ending normalization, terminal-newline normalization, and outer-whitespace normalization with identical word count. Fuzzy similarity, interior-whitespace collapse, and near word counts do not clear ambiguity.

## Status and smoke checks

```bash
pangram-local status
pangram-local status --check-auth
pangram-local status --launch-smoke
```

The headed browser is the default. Headless mode exists for controlled testing but is not the default authenticated operating mode.

## Live provenance

The implementation was live-certified on 2026-08-20 against two approximately 10k-word Pangram 4 boundaries. The first result was recovered from the original ambiguous paid submission with no repeat call; the second was submitted exactly once and exact-bound to its stored History record. Both returned Pangram 4.0 `STAGE_SUCCESS`. The detailed evidence remains on the historical local-GUI evidence branch and its content-addressed result directories.

The reusable transport was promoted onto current `main` without importing the old Romance article-editing branch history or establishing any article authority. The old remote Browserbase proposal and old stacked local GUI development/evidence proposal are closed as superseded; their histories remain provenance.

## Clean-main validation

The first clean-main integration run exposed only two obsolete Browserbase tests that depended on the old Browserbase command script and an article-specific workflow; those branch-topology tests were removed rather than importing obsolete infrastructure. The next clean-main run passed **226 tests with 5 intentional skips**. Its changed-file lesson-closeout gate passed. The repository audit passed after five pre-existing Romance lesson artifacts already present on `main` were explicitly closed as either `article-specific` or `superseded` through the trusted lesson-closeout processor. Repository workflow policy also passed. No Pangram detector submission is performed by these CI gates.

## Privacy and profile safety

- Never use the owner's ordinary Brave/Chrome profile by default.
- Never place the persistent auth profile inside a Git repository.
- Diagnostics omit cookies, browser storage values, auth headers, submitted text, and private response bodies.
- History recovery may inspect stored records in memory to prove exact identity; private record text and UUID lists are not committed as diagnostics.
