# Frozen idiolect score-map inventory run — 2026-08-18

## Purpose

Recover already-paid/already-computed comparative author scores before considering another LUAR or GitHub Actions run. This is evidence discovery only; it does not assign authorship reliability, compute IER, or change corpus authority.

## Implementation

- utility: `src/pangram_lab/score_map_inventory.py`
- tests: `tests/test_score_map_inventory.py`
- input class: local JSON files and ZIP artifacts
- required score map: exactly the declared author set, all finite numeric values
- durable output: source/member identity, object path, score-field name, nearby metadata, and per-author score vector
- prohibited output: raw/canonical prose, embeddings, or local text paths

## Local execution

The utility was run against the already downloaded synchronized idiolect and transformation-sensitivity artifact ZIPs for:

- Joel Rosenblum
- Stian Gudmundsen Høiland
- David Vardy

A metadata-only JSON inventory and interactive recovery tables were returned in the current ChatGPT conversation. The local receipt path was:

`/mnt/data/idiolect-frozen-score-map-inventory.json`

That local path is execution evidence only and is not a repository dependency.

## Interpretation boundary

Finding a complete three-author score vector establishes that comparative evidence can be recovered. It does not establish that:

- the row is a held-out natural original;
- the fold-specific profile identity is complete;
- the original was reliably attributable under a predeclared rule;
- a transformation is an erasure case;
- another heavy model run is unnecessary for every remaining field.

Normalization into the author-neighborhood analyzer must fail closed unless sample, source-group, register, true-author, canonical hash, fold/profile identity, and original-reliability provenance can all be bound without inference.

## Next safe action

Create a metadata mapping from the recoverable rows to their exact frozen fold/profile identities. Admit only unambiguous natural-original rows. List each absent required field explicitly. One batched source-frozen LUAR score export may be proposed only for those named gaps; do not rerun embeddings to reproduce winners or margins already preserved.
