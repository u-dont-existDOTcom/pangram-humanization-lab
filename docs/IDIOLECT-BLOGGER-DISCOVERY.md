# Idiolect Blogger source discovery

Status: **source discovery only; not corpus admission and not a calibration result.**

This stage sits before `IDIOLECT-CORPUS-ACQUISITION.md`.

Its job is to enumerate exact post identities from Joel-confirmed legacy Blogger sites without storing or modeling the post body. Discovery answers **what independent source documents exist?** Acquisition later answers **which of those documents can be safely isolated as Joel-authored prose?**

## Why discovery is separate

Search-engine results are incomplete and can surface mirrors rather than canonical posts. Guessing Blogger permalinks also creates silent omissions and duplicate risk.

Blogger exposes a public Atom post feed. The discovery command uses that feed with the platform's documented `max-results` and 1-based `start-index` pagination, then records only:

- source/blog ID;
- Blogger entry ID;
- title;
- published/updated timestamp;
- canonical alternate/permalink URL;
- labels when present.

Feed post content is never written to discovery output.

## Queue and pre-LLM boundary

The reviewed queue is:

`../state/IDIOLECT-BLOGGER-DISCOVERY-QUEUE-2026-08-18.json`

It contains only blog roots Joel confirmed as his (or, for Dharma Connection, a site where he confirmed the comments under `Joel Rosenblum` are his).

The first-pass discovery cutoff is **before 2022-11-30 UTC**, deliberately choosing the pre-ChatGPT-public period as the clean legacy lane. This does not imply that later Joel writing is AI-assisted; it simply makes this discovery tranche maximally unambiguous.

## Run locally

```bash
pangram-lab idiolect-blogger-discover
```

Output defaults to:

`.local/idiolect-corpus/blogger-discovery.json`

The `.local/idiolect-corpus/` tree is gitignored.

## Networked GitHub run

`.github/workflows/idiolect-blogger-discovery.yml` runs the same discovery on a networked GitHub runner when the discovery queue/tool/workflow changes.

The workflow:

1. tests the metadata-only parser;
2. enumerates confirmed-owner Blogger feeds;
3. stores the full metadata-only discovery JSON as a short-retention workflow artifact;
4. publishes/updates one compact GitHub issue receipt containing per-blog counts/date ranges/errors and the workflow run URL;
5. never commits or uploads post prose.

The workflow artifact is metadata only. It must not be repurposed to store acquired corpus text.

## Discovery does not equal admission

A discovered post is not automatically a Joel corpus sample.

Before selection/acquisition:

- determine whether the whole post is Joel-authored, a multi-author transcript, a quotation archive, or mixed material;
- prefer independent source groups and topic/register diversity rather than maximal word count;
- avoid selecting many posts that repeat or quote one another;
- for Dharma Connection, discovery identifies candidate threads only; text extraction still keeps only Joel's turns;
- select enough long documents for held-out attribution while allowing short genuine comments to contribute only as profile/support material when methodologically appropriate.

## Selection target

The initial target is roughly **15–30 independent clean written source groups**, with enough diversity that a classifier cannot identify Joel primarily from recurring subject nouns.

Selection should cover, where available:

- research/contemplative argument;
- practical/explanatory writing;
- political or institutional polemic;
- personal/relational writing;
- humor/irreverence;
- dialogue/Q&A.

This is a diversity target, not a quota. Source provenance and independence outrank category balance.

## Next gate

After metadata discovery:

1. curate candidate posts by independence, length, provenance, and register diversity;
2. assign conservative extraction modes;
3. acquire/canonicalize selected prose locally;
4. manually audit author boundaries, quotations, platform debris, and duplicates;
5. hash and freeze the Joel-side corpus;
6. only then acquire non-Joel control authors and run Tier-B SVM/LUAR calibration.
