# Spiritual Bypassing visible-boundary incident — 2026-08-14

## Finding

Pangram certification must use the reader-visible representation, not source markup.

During the Spiritual Bypassing audit, the exact r06 raw Markdown source had previously measured 100% Human on Pangram 4.0. Joel then checked the Markdown-only article in Pangram's GUI and received 88.3% Human. Reproducing the GUI representation deterministically by stripping Markdown link destinations/source markup and collapsing the article to its 1,482-word visible plaintext produced 88.3194506% Human through the Pangram 4 API. The API and GUI therefore agreed when given materially equivalent visible text.

## Root cause

The earlier completion claim certified a different representation from the one a reader and Pangram UI saw. Raw Markdown syntax, link destinations, and source-only punctuation changed the detector boundary enough to produce a materially different result.

This was a representation/certification error, not evidence of a broad API-versus-GUI disagreement.

## Durable rule

- For Markdown article work, raw Markdown is diagnostic only.
- Derive and hash the reader-visible plaintext after stripping source-only Markdown syntax and link destinations before the certification call.
- For Substack, certify the rendered reader-visible text surface, including card/embed text if Pangram actually surfaces it.
- Preserve raw-source measurements when useful for representation research, but never use them to certify a different rendered publication boundary.
- Before interpreting API/GUI disagreement, first make the submitted/extracted representations equivalent and compare word count/text extraction.

## Exact evidence

- Raw Markdown r06 hash previously certified: `ec5a59dfd61d3cc3263ccff836a935d12104c85ab9d64f2707026a363ab2f4e9`.
- Visible control result: `state/experiments/spiritual-bypassing-visible-boundary-r07-2026-08-14-results.json` on `automation/pangram-fixed-batch`.
- Visible control text hash: `21dbb0dc33c0634f6dd113d43053445d8ce99cd949d1a730e0cd0704851a66d5`.
- Pangram 4.0 visible control: `fraction_human=0.8831945061683655`, `fraction_ai=0.09417040646076202`, `fraction_ai_assisted=0.022635063156485558`.

## Scope

This is a cross-article workflow rule about measurement representation. It is not a phrase rule and does not imply that Markdown syntax always raises or lowers Pangram scores in a predictable direction.
