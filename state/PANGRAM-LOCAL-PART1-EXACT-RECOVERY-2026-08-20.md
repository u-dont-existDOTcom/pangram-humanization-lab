# Pangram local GUI Part-1 exact recovery checkpoint — 2026-08-20

## Status

The latest owner-machine recovery run established the identity of the already-paid Romance Part-1 GUI report without making another detector submission.

- Local deterministic suite: **195/195 passed**.
- Paid Part-1 reservation: `2026-08-18T17:43:00.595741Z`.
- Nearest authenticated Pangram history-list record: `2026-08-18T17:43:13.569363Z`.
- Distance from reservation: **12.974 seconds**.
- That record passed the existing exact/bounded stored-text identity gate for the authorized Part-1 boundary:
  - SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`
  - 10,236 words.
- `detector_submission_attempted_during_recovery` remained `false`.
- Part 1 was **not** resubmitted.
- Part 2 was **not** submitted.

The remaining failure was downstream of identity recovery: the rendered report no longer exposed Human/AI percentages in the form expected by the GUI parser. Therefore the complete Part-1 receipt/cache was not written yet and the existing no-repeat guard remains in force.

## Score-extraction repair

The GUI history record already exposes structured detector data under document-level stored response objects. The branch now prefers the document-level structured result, especially `response.overall`, before attempting rendered-DOM score parsing.

The structured parser:

- accepts only explicit canonical fraction fields (`fraction_ai`, `fraction_human`, and either `fraction_ai_assisted` or explicit moderate/light assisted fractions);
- accepts only `STAGE_SUCCESS` when a stage is present;
- requires detector version `4.0` when version is present, or independent Pangram-4 model provenance when version is absent;
- checks that AI + assisted + Human fractions sum to approximately 1;
- deliberately excludes `response.in_page` as document-level score authority;
- never infers score semantics from `prediction_prob`;
- if the structured schema still does not expose canonical fractions, fails closed with a privacy-safe schema shape containing key names and whitelisted scalar metadata only, never article text, windows, UUIDs, private URLs, cookies, storage, or auth data.

Implementation commits:
- structured parser: `25df8192ccdf95d04999af15b40fd51cc59ce707`
- regression tests: `eae746edd9216322f9d3ba0bd1502fa511f0a601`

Public CI on that head passed the complete suite (**200 tests**), lesson closeout, repository audit, and workflow-policy gate. No detector submission occurs in CI.

## Next safe action

Run `scripts/pangram_local_romance_recover_resume_safe.sh` again.

Expected behavior:

1. read-only timestamp + exact-text recovery re-identifies the already-paid Part-1 record;
2. structured stored-result parsing attempts to recover the Part-1 detector fractions;
3. if successful, write/persist the Part-1 complete receipt and clear only the ambiguity represented by the recovered record;
4. only then may the wrapper proceed to the still-unsubmitted Part-2 GUI call;
5. if structured score extraction still fails, stop without resubmitting Part 1 or submitting Part 2 and report only the privacy-safe structured-result shape.

## Stop conditions

Do not resubmit Part 1, use `--force`, infer fractions from `prediction_prob`, treat `response.in_page` as the whole-document result, broaden text identity beyond the existing bounded normalization contract, or submit Part 2 before the Part-1 complete recovery receipt is durably written.
