# Immutable text sources for fixed Pangram batches

Status: supported on `automation/pangram-fixed-batch` for exact aggregate inputs that already exist as immutable public GitHub blobs.

## Why this exists

Large article halves should not be copied into another 20,000-word JSON spec merely to submit the same exact bytes to Pangram. A fixed-batch variant may therefore reference an immutable GitHub blob while retaining the existing content-addressed cache, paid-call ledger, Pangram-4/version gate, result identity, and recovery-before-repeat rules.

This is an input transport feature only. It does not change article authority, detector acceptance criteria, or paid-call budgets.

## Supported form

A variant supplies exactly one of `text` or `text_source`.

```json
{
  "id": "PART1",
  "section_id": "part1-current",
  "budget_scope": "aggregate",
  "text_source": {
    "kind": "github_blob",
    "repository": "owner/repository",
    "blob_sha": "0123456789abcdef0123456789abcdef01234567",
    "text_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  }
}
```

Current source contract:

- `kind` must be exactly `github_blob`;
- `repository` must be an `owner/name` GitHub repository identifier;
- `blob_sha` must be an exact 40-character lowercase Git blob SHA;
- `text_sha256` must be the exact SHA-256 of the decoded UTF-8 bytes Pangram is intended to receive;
- resolved text must be nonempty UTF-8 and no larger than 2,000,000 bytes.

The resolver calls only GitHub's REST blob endpoint on `api.github.com`, verifies the returned Git blob identity, base64-decodes the exact blob, checks `text_sha256`, and only then supplies the text to the ordinary fixed-batch runner.

The current implementation is intentionally unauthenticated and therefore suitable for public GitHub source blobs. Do not use it as a private-repository data transport.

## Identity and paid-work safety

The registered fixed-batch spec is fingerprinted by the immutable `text_source` metadata. Runtime resolution adds a derived `text` field in memory, but this field is excluded from the spec fingerprint whenever `text_source` is present. Therefore the same registered source metadata has the same experiment identity before and after resolution.

The resolved text then enters the existing detector path unchanged:

- exact submitted-text SHA-256/cache lookup;
- pending-task/reservation recovery;
- stable audit and section identity;
- aggregate vs local-section budget semantics;
- explicit Pangram 4.0 gate;
- durable result and call accounting;
- lesson-review registration.

Results record the resolved text SHA-256 and the immutable `text_source` identity. The current result schema also retains the resolved text, matching prior fixed-batch evidence behavior.

## Fail-closed rules

Reject before detector access when:

- both `text` and `text_source` are supplied;
- neither is supplied;
- source metadata is malformed;
- GitHub returns a different blob identity or unsupported encoding;
- decoded bytes do not match `text_sha256`;
- the blob is empty, non-UTF-8, or over the size cap;
- a caller reaches `run_batch` without resolving a source first.

Code-only tests must inject a fake resolver and must not depend on live GitHub or Pangram access.

## Romance r10 use

The first intended live use is the preservation-r10 Romance aggregate audit. The article-side materializers already produced exact reader-visible Part 1 and Part 2 Git blobs with independent SHA-256 manifests and zero unexplained preservation deltas. The Pangram spec references those immutable blobs rather than duplicating the article text.
