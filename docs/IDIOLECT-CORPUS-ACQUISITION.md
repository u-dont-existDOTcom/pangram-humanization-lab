# Idiolect corpus acquisition

Status: **acquisition infrastructure; not a calibration result.**

This workflow builds the provenance-audited text corpus required by `IDIOLECT-VALIDATION-PROTOCOL.md` before Tier-B SVM/LUAR calibration. It is designed to prevent the two easiest ways to invalidate an authorship benchmark: contaminating the target-author profile with AI-written prose and leaking duplicated source material across train/test boundaries.

## Canonical records

Two metadata-only files have different jobs:

- `../state/IDIOLECT-CORPUS-SOURCE-INVENTORY-2026-08-18.json` — comprehensive provenance record: confirmed/current/pending sources, mixed-provenance segments, explicit exclusions, and acquisition status.
- `../state/IDIOLECT-CORPUS-ACQUISITION-QUEUE-2026-08-18.json` — reviewed operational queue: only public samples for which an explicit extraction mode has been assigned.

Do not turn the comprehensive inventory into an automatic scraping target. A source becomes automatable only after its page structure and authorship boundary are understood well enough to assign an extraction mode.

## Privacy boundary

Raw and canonicalized corpus prose stays outside Git under:

`.local/idiolect-corpus/`

That path is gitignored. Repository state may contain public source URLs, hashes, word counts, provenance labels, source-group identities, register labels, redaction counts, and quality flags, but not the acquired prose itself.

The current local command also strips raw URLs, email addresses, and phone-number-like strings from modeling text. Visible hyperlink anchor text is retained when the HTML exposes it because the words may be author-written; the destination URL is not an idiolect feature.

## Run the reviewed acquisition queue

Install the repository as usual, then run:

```bash
python -m pip install -e '.[test]'
pangram-lab idiolect-corpus-acquire
```

The CLI defaults to the reviewed acquisition queue and writes:

- canonical local text: `.local/idiolect-corpus/text/`
- local acquisition metadata: `.local/idiolect-corpus/acquisition-manifest.json`

The command can be narrowed to one or more sample IDs:

```bash
pangram-lab idiolect-corpus-acquire \
  --sample-id tafka-2019-03-08-plant-spirits \
  --sample-id dc-2014-02-04-holographic-universe
```

To run a different metadata queue explicitly:

```bash
pangram-lab idiolect-corpus-acquire path/to/reviewed-queue.json
```

## Current extraction modes

The acquisition tool is deliberately conservative.

### `post-body`

Keep the recognized authored Blogger post body, preserving visible anchor text while dropping link destinations and page chrome.

Use only when the post body itself is owner-authored rather than a multi-author transcript or quote-heavy artifact.

### `post-body-drop-blockquotes`

As above, but remove HTML blockquotes. Use when quoted interlocutors, articles, books, or other third-party text would otherwise enter the target-author profile.

This is not enough when third-party material appears without `<blockquote>` markup; such a sample still requires manual cleanup or a narrower extractor.

### `speaker-prefix:Joel Rosenblum`

After extracting the post body, retain only lines explicitly prefixed with `Joel Rosenblum`. This is intended for archived multi-author discussions such as Dharma Connection.

If a discussion page does not preserve speaker prefixes reliably, acquisition must fail/manual-review rather than guessing paragraph authorship.

### `message-by-you`

Retain only explicit Messenger-export lines beginning `Message by You:`. Platform timestamps appended to those turns are removed.

## Mandatory manual audit after acquisition

Automated extraction is a first pass, not promotion into the benchmark.

Before a sample becomes profile/validation/test eligible, inspect it and confirm all of the following:

1. only Joel-authored text remains;
2. third-party quotations and interlocutor turns are absent or explicitly excluded;
3. platform chrome, editor debris, repeated timestamps, share controls, and embed remnants are absent;
4. phone numbers, email addresses, raw URLs, credentials, and tracking strings are absent;
5. the sample is not a repost/mirror/export duplicate of another sample;
6. the source/post/thread is assigned one stable `source_group` and any near-duplicate identity;
7. modality is correct (`written` versus `spoken`);
8. provenance is `natural-owner-confirmed` for the primary written profile;
9. register labels describe the text rather than being inferred from the site name alone;
10. the sample is long enough for the intended instrument or is deliberately pooled only inside its own source group.

A quality flag is a reason to inspect, not an automatic exclusion rule.

## Source splitting and duplicate control

Never random-split paragraphs from one article, blog post, discussion thread, or mirrored copy.

All derived chunks from one independent source remain in the same profile/validation/test partition. Mirrors and near-duplicates share a `near_duplicate_group` and must never cross partitions.

Do not assign the final split until canonical extraction, hashing, and duplicate reconciliation are complete.

## Current provenance boundary

The primary written corpus currently accepts only owner-confirmed written sources. Owner-confirmed spoken material remains useful as a separate speech/process corpus but does not train the primary written authorship profile.

Known mixed-provenance documents are segmented rather than assigned one whole-document label. In particular, the Cancer article contains owner-confirmed human spans and discrete owner-confirmed AI-written spans. Detector output may help locate those already-known boundaries, but detector predictions do not establish provenance.

Community material known to be partly AI-written and detector-targeted Romance revisions remain outside the natural-owner written profile unless an independently established span has a different provenance.

## Manual acquisition backlog

The operational queue intentionally leaves some confirmed owner sources manual/pending until safe extraction exists, including:

- the 2021 Buddhism StackExchange answer, because a named-answer selector is not yet implemented;
- older Blogspot sources whose pages were not reliably retrievable in the acquisition environment;
- the owner-pasted `JEWS LOVE ANTISEMITES` piece until its canonical source/date is fixed.

Do not compensate for an unavailable source by scraping a mirror or whole multi-author page into the corpus without preserving duplicate and authorship boundaries.

## Cancer segmentation rule

The supplied Pangram report is useful because it visibly separates several blocks in the exact mixed article. For corpus provenance, however, Joel's direct authorship statement is the authority: he wrote the human spans, discrete AI sections were inserted as AI prose, and he did not rewrite those AI sections.

Therefore:

- human spans can become `natural-owner-confirmed` after exact text boundaries are reconciled against the source article;
- AI spans are controls/synthetic material, not Joel profile text;
- the Pangram block boundaries are locators to reconcile, not proof that an arbitrary green/red detector label establishes authorship.

## Completion gate before Tier B

The Joel-side acquisition pass is ready for deterministic splitting only when every eligible sample has:

- canonical text stored locally;
- canonical SHA-256;
- word count;
- provenance and modality;
- register label(s);
- source group;
- near-duplicate audit;
- manual extraction audit status.

Only after that should the project freeze profile/validation/final-test partitions and acquire topic-matched non-Joel comparison authors for closed-set attribution.
