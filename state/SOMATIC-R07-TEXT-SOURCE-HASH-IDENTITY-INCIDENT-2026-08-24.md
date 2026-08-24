# Somatic r07 text-source hash identity incident — 2026-08-24

Status: **OLD R07 SPEC PRE-DETECTOR INVALID; NO PAID CALL; CORRECTED R07B SPEC REGISTERED**

## Incident

The first Somatic r07 Job2→end spec registered this immutable GitHub text source:

- repository: `u-dont-existDOTcom/joel-articles`
- Git blob: `01825fbd46497c17eac14aa709e29429f5caf05b`
- spec `text_sha256`: `6091db45d7ddf80f027cc591396abd75ab7b144c206e28befee86b2f5d3589ec`

A later article-registry audit mechanically hashed the exact checked-out boundary file bytes as:

`91dd31d6519e76f30831780789d9a13c2761378978d153f2cc3f602c4b5b0b87`

A dedicated hosted regression then proved:

- exact raw file bytes SHA-256: `91dd31d6519e76f30831780789d9a13c2761378978d153f2cc3f602c4b5b0b87`;
- the file ends with one newline;
- removing exactly that terminal newline yields SHA-256 `06d068603b3a9c0d26bd9537240550ab18ae589ea795aa6bc2f443bffb96451b`;
- therefore stale `6091db45...` matches **neither** the Git blob's raw bytes nor the same text with one terminal newline removed.

The immutable Git blob itself never changed. The stale hash was introduced in the r07 preflight/spec bookkeeping rather than being a later article edit.

## Why the bad request cannot bill

`src/pangram_lab/text_sources.py` fetches the exact GitHub blob bytes and checks their SHA-256 against `text_source.text_sha256`.

`scripts/run_fixed_batch.py` calls `resolve_text_sources(registered_spec)` **before** reading `PANGRAM_API_KEY`, constructing the Pangram client, probing auth, or entering paid call accounting.

Therefore the old r07 spec must fail closed on source-hash mismatch before detector access. Its original immutable private request and later same-request replay do not create a paid reservation merely by existing.

The stable audit remained 4/6 paid calls with no pending resume and no cache/result for the old r07 identity when this incident was recorded.

## Correction

Do **not** mutate or reuse the old frozen experiment path:

`experiments/somatic-therapies-r07-job2-to-end-20260824-a.json`

It remains provenance for the invalid pre-detector identity.

The corrected spec is a new experiment under the **same stable audit and section**:

`experiments/somatic-therapies-r07b-job2-to-end-20260824-a.json`

It pins:

- the same Git blob `01825fbd46497c17eac14aa709e29429f5caf05b`;
- correct raw-byte SHA-256 `91dd31d6519e76f30831780789d9a13c2761378978d153f2cc3f602c4b5b0b87`;
- audit `somatic-therapies-r03-job2-to-end-20260824`;
- section `job2-to-end`;
- `budget_scope: section`.

Changing experiment/spec identity corrects bookkeeping only. It does **not** reset the section paid-call cap; r07b is still the intended fifth paid measurement if and only if it reaches a reservation.

## Durable rule

For GitHub-blob text sources, never derive `text_sha256` from an in-memory editor string, copied chat text, rendered file view, or guessed newline normalization. Compute it from the exact bytes of the pinned Git blob/file and validate that `(repository, blob_sha, text_sha256)` triple before creating an immutable detector spec/request.

A text-source hash mismatch is a **pre-detector identity failure**, not a detector result and not a paid call. Correct it with a new immutable spec identity while preserving the same stable audit/section accounting; never mutate the frozen bad spec behind an existing request.
