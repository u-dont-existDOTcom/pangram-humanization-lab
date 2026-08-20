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

## Read-only localization of existing results

When an existing long-document result has only aggregate Human/AI fractions, use the stored History record before buying diagnostic detector calls:

```bash
pangram-local localize \
  --input path/to/part1.txt \
  --expect-sha part1.txt=<sha256> \
  --input path/to/part2.txt \
  --expect-sha part2.txt=<sha256>
```

`localize` has **no detector-submission path**. It opens authenticated Pangram History, exact-binds the stored record to each authorized input, then inspects structured result objects such as `response.overall` and `response.in_page`.

### Long-document window coordinates

Live Romance History evidence on 2026-08-20 exposed an important transport detail: `response.overall.windows[].text` can be only a short preview even when `start_index`, `end_index`, and `word_count` describe a much larger detector window. The first localizer therefore localized some previews correctly but could not yet claim the complete windows.

The current full-window proof is **collection-wide**, not a one-window heuristic. Complete `response.overall.windows` coordinates are accepted only when all of these checks pass together:

1. the stored History record exact-binds to the authorized full input;
2. the window collection begins at Pangram index `0`, ends at the complete linebreak-stripped input length, and each window's `end_index` equals the next window's `start_index`;
3. mapping every window start/end through the exact input with CR/LF characters removed yields monotonic raw source boundaries;
4. **every** stored window preview begins exactly at its mapped raw start.

When all previews validate the same coordinate transform across the complete contiguous collection, the localizer can recover full raw window spans even when a preview is non-unique elsewhere in the article. Pangram's stored `word_count` is preserved as detector metadata but is **not** used as a Python-whitespace-tokenization equality gate; live evidence showed those two word-count conventions are not identical.

If the collection-wide proof fails, the complete-window claim fails closed. The parser falls back only to separately provable exact raw offsets or unique exact preview/span matches and records privacy-safe unresolved shapes for anything else.

The persisted schema-v3 `localization.json` contains 0-based/end-exclusive character and word offsets, a SHA-256 for each exact bound span/window, source field paths, binding mode, the count of collection-validated full overall windows, and Pangram scalar metadata such as label/confidence/score fields. It does **not** persist the submitted text, localized span text, History UUID, private report URL, cookies, storage, headers, or credentials.

A page/window result is localization evidence only. `response.overall` remains the whole-document score authority; `response.in_page` must never be promoted into a document-level fraction merely because it contains stronger local scores.

### Direct lookup of an already-known stored report

If a durable prior receipt already contains the exact stored Pangram History route, a single-input localization may skip History-list ordering and inspect that report directly:

```bash
pangram-local localize \
  --input path/to/text.txt \
  --expect-sha text.txt=<sha256> \
  --report-url 'https://www.pangram.com/history/<uuid>'
```

`--report-url` is accepted only for one input, is validated as a Pangram History route, is used read-only, and is never persisted in localization or failure evidence. The exact stored-document identity gate still applies; knowing a route never authorizes a mismatched result.

### Failure durability

A localization failure writes and Git-syncs `localization-failure.json` containing only the exact input hash/word count, failure stage/type, candidate counts, and whether an exact stored record had been observed. It excludes raw exception text and private report identifiers. Multi-input localization attempts continue to the remaining inputs after one failure and return a non-zero process status only after durable failure evidence has been written.

If Pangram's live schema contains no exact-bindable windows/spans, `localize` returns `no_bound_spans` plus privacy-safe key/length shapes so the schema can be adapted without guessing or spending another detector call.

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
- History recovery/localization may inspect stored records in memory to prove exact identity and exact span offsets; private record text and UUID lists are not committed as diagnostics.
