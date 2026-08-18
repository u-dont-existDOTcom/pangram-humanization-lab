# Idiolect register-corpus checkpoint — 2026-08-18

## Authority and scope

This checkpoint continues issue #39 after the synchronized LUAR benchmark and the first frozen transformation-sensitivity counterexample. It concerns corpus and instrument calibration only. It does not establish article authority, IER, a Tier-A threshold, or `validated-for-register` status.

## Decision

Reuse and compose the existing source-level provenance, cleanup, deduplication, register-label, exact-hash, and equal-word-budget controls. Do not invent another authorship metric or duplicate raw Joel prose into a second repository.

## Implemented on this branch

- `state/IDIOLECT-JOEL-REGISTER-CORPUS-SPEC-2026-08-18.json`
- `src/pangram_lab/joel_register_corpus.py`
- `tests/test_joel_register_corpus.py`
- `.github/workflows/idiolect-joel-register-corpus-freeze.yml`

The candidate pool contains five conservatively cleaned TAFKA sources and four clean-metadata Insurgency sources. The four Insurgency sources remain explicitly blocked on manual authorship/quotation-boundary audit.

The prior 8,090-word TAFKA intro is preserved as provenance-clean overflow evidence but excluded from balanced views because it supplied 72.55% of the first six-source profile.

The workflow creates local-only full and length-balanced views, including a nine-source exact-180-word view. Only metadata, hashes, counts, concentration measures, register/site strata, and audit status may enter the workflow artifact.

## Fail-closed gates

The workflow rejects:

- any acquisition or cleanup error;
- duplicate sample IDs or exact cleaned hashes;
- any source under the required exact 180-word budget;
- more than 30% single-source concentration in the pooled full candidate;
- any prose or local path in the receipt;
- any claim that the candidate is benchmark-eligible.

## Current blockers

1. Manually audit the four political/journalistic candidate boundaries.
2. Add DYOR, DMSO, and Autism through a hash-bound local cross-repository adapter; do not copy their prose into Pangram lab.
3. Select register-relevant human controls only after the Joel source pool is frozen.
4. Establish above-chance original held-out attribution before measuring rewrite degradation.
5. Keep philosophical and political results separate until cross-site/platform coverage exists.

## Next safe action

Inspect the pull-request workflow receipt. If the source and privacy gates pass, freeze the metadata result and merge the corpus architecture. Then perform the four bounded source audits; do not launch another transformation benchmark against the Dharma-only profile.
