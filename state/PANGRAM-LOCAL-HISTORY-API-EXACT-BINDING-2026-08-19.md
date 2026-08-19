# Pangram local exact history-API binding — 2026-08-19

## Live owner-machine evidence

The 2026-08-19 owner-machine recovery run passed **181/181** deterministic tests and made **no repeat Part-1 detector submission** and **no Part-2 detector submission**.

The privacy-bounded structural diagnostic finally exposed the current long-document report transport clearly:

- real report page route: `https://www.pangram.com/history/<uuid>`;
- current page title: `Your AI Report | Pangram`;
- current long-document overview exposes summary controls such as `AI 8%` and `Human 92%` and paginated highlight navigation (`1 / 6`);
- report data is loaded from `https://web.pangram.com/api/history/<uuid>/`;
- that JSON record exposes keys including `prompt`, `response`, `response_payload`, `prediction`, `prediction_prob`, `model_id`, and `uuid`;
- `https://web.pangram.com/api/history-list/` is the current list endpoint;
- ten existing report identities were discovered/read during recovery;
- the old DOM parser still rejected them because current long reports no longer expose the historical per-segment word-count headings required by that parser.

The diagnostic intentionally did not persist response bodies, cookies, session/storage values, request headers, query strings, or private result URLs.

## Corrected identity contract

For current long-document Pangram GUI results, exact document identity must no longer depend on the rendered segmented-report layout.

A stored result is exact-bound only when the read-only `web.pangram.com/api/history/<uuid>/` JSON record itself contains the literal submitted text matching the authorized UTF-8 boundary. The recovery/paid runner records:

- exact submitted-text SHA-256;
- exact word count;
- the JSON field path in which exact text matched;
- record model/prediction metadata needed for provenance.

The response body is processed only in memory. The raw record is not committed.

## Current result-summary contract

The current rendered long-document overview exposes document-level Human/AI percentages but not the old analyzable per-segment word-count headings. Therefore:

- exact document identity comes from the stored history API record;
- Human/AI fractions come from the exact record's rendered overview when available;
- `prediction`/`prediction_prob` are a bounded fallback only when the rendered summary cannot be parsed and the label determines probability orientation;
- no synthetic segment list or invented segment word counts may be created merely to satisfy the legacy parser.

This is a transport/layout correction, not a new detector-science claim.

## Implementation

New exact-record helper:

`src/pangram_lab/history_api_record.py`

New no-submit Part-1 recovery:

`scripts/pangram_local_romance_recover_part1_api.py`

New paid runner for subsequent exact inputs:

`scripts/pangram_local_romance_paid_api.py`

The paid runner attaches its exact-history response listener **before** the detector click, preserves the existing durable call reservation before that click, and accepts completion only after the stored record exact-matches the submitted text. Part 1 remains blocked from repeat; recovery contains no detector-action path.

The operator wrapper now routes Part-1 recovery through the exact API matcher and, only after successful recovery/cache, routes Part 2 through the API-bound paid runner.

## Current stop boundary

- Do not resubmit Part 1.
- Do not submit Part 2 until Part 1 is recovered and cached through exact stored-record identity.
- If the exact API record cannot be matched, preserve ambiguity and stop.
- If Part 2 is clicked but its exact stored record cannot be bound, preserve that call as ambiguous and recover before any repeat.
