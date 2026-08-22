# Working lessons supplement — 2026-08-22

Research state only. Human editorial quality, semantic fidelity, owner authority, and exact source provenance outrank detector output.

## Long-document split placement can create remote detector flips

Exact Romance r12/r14/r15 controls established that detector segmentation itself can change Pangram classifications far downstream in byte-identical prose.

- The old Part-2 boundary at SHA `9e4c6a522c95741c7dfc9e040b2dcc40773427cbc0aef8f45211de77208b0c85` measured Pangram 4.0 at exact 100% Human.
- r14 prepended the complete Maturity section to that same old Part-2 stream. The old stream remained byte-for-byte as a suffix, yet the new Part 2 fell to 95.6538856% Human and produced four AI windows in remote Not A Performance, vows, and breakup passages.
- r15 changed no article prose and restored the old split. The exact old Part-2 SHA therefore retained its existing 100%-Human evidence.

Durable rules:

- Treat long-document split placement as part of the detector input, not neutral packaging.
- A newly red window after a split change is localization evidence only. Compare it against exact prior-boundary evidence before editing the prose.
- Remote effects are possible: the affected window need not be adjacent to the changed split.
- If byte-identical prose was previously green and becomes red only after segmentation changes, test boundary/composition explanations before rewriting it.
- Keep segmentation stable during controlled prose comparisons. If the split itself is the experimental variable, change no prose and record the boundary-only operation explicitly.
- Prefer coherent discourse boundaries editorially, but do not assume a more natural boundary will score better. Detector score does not choose article architecture.
- Section and half-document measurements remain diagnostic unless that exact unit is the requested delivery boundary.

Exact incident/evidence routing: `state/ROMANCE-HALF-SPLIT-REMOTE-SENSITIVITY-2026-08-22.md` plus the r14/r15 result JSON on `automation/pangram-fixed-batch`.
<!-- closeout-request:romance-half-split-sensitivity-20260822 -->
## Promotion record

The r12/r14/r15 Romance control establishes a reusable detector rule: long-document segmentation is part of the detector input and can flip far-downstream byte-identical prose. Hold segmentation stable for controlled prose comparisons. After a split change, treat newly red remote windows as boundary/composition evidence until exact prior-boundary comparison supports a prose-level cause. Detector score never chooses article architecture.
