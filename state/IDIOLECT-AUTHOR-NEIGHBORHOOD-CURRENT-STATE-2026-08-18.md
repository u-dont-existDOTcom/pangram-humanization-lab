# Idiolect author-neighborhood diagnostic checkpoint — 2026-08-18

## Trigger

Joel corrected the interpretation of the PR #79 Joel-to-Stian nearest-author flip. He reports that Stian naturally writes/thinks somewhat like him and that this affinity is part of why they clicked.

## Durable interpretation

- Stian is a plausible natural stylistic/intellectual near-neighbor and a valuable hard negative.
- The PR #79 flip is not clean evidence of genericization or idiolect erasure.
- It still disproves Joel-only similarity as sufficient identity evidence.
- Preserve historical metrics unchanged; attach the owner-corrected interpretation separately.

## Implemented branch

Branch: `task/idiolect-natural-neighbor-diagnostic-20260818`

Files:

- `state/IDIOLECT-TRANSFORMATION-SENSITIVITY-OWNER-INTERPRETATION-2026-08-18.md`
- `state/IDIOLECT-AUTHOR-NEIGHBORHOOD-DIAGNOSTIC-SPEC-2026-08-18.json`
- `src/pangram_lab/author_neighborhood.py`
- `tests/test_author_neighborhood.py`

The analyzer accepts metadata and per-author score vectors only. It reports:

- profile cosine matrices when supplied;
- natural-original confusion matrices;
- true-author margins by author and source group;
- empirically ranked hard negatives;
- declared-neighbor confusion counts;
- aligned rewrite score deltas against every author;
- target-versus-nearest-alternative margin deltas;
- whether the winning alternative was already a declared natural neighbor;
- separate eligible and ambiguous original counts.

It never invents a reliability threshold and never computes IER. Upstream evaluation must explicitly mark an original `eligible` under a predeclared held-out/resampling rule; an eligible original must also be uniquely and correctly attributed.

## Validation

The focused natural-neighbor test module and the full repository test suite passed in a fresh clone of the branch. No GitHub Actions workflow or paid detector/model call was launched for this work.

## Cost decision

Do not open another pull request yet. Private GitHub Actions minutes are constrained, and PR #80 is already resolving the register-corpus authority. Keep this branch durable but unmerged until:

1. PR #80's corpus freeze is resolved;
2. the existing synchronized and transformation artifacts are checked for complete per-author score vectors;
3. a concrete missing-data field is documented if a new LUAR run is truly necessary.

## Next safe action

Reuse existing frozen scores to build the first natural-original Joel/Stian/David neighborhood receipt. If the artifacts contain only winner/margin summaries rather than complete score vectors, document exactly what is missing and batch one source-frozen metadata-only LUAR score export after the register corpus is merged. Do not rerun embeddings merely to reproduce already-preserved winners or margins.
