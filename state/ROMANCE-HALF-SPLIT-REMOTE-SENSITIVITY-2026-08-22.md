# Romance half-document split sensitivity incident — 2026-08-22

Status: transferable detector-method finding from exact Romance aggregate controls. This note does not establish article authority and does not license prose edits.

## Exact evidence

The preservation-r12 / old-split Part 2 reader-visible text had SHA-256 `9e4c6a522c95741c7dfc9e040b2dcc40773427cbc0aef8f45211de77208b0c85`, 9,892 words, and measured Pangram 4.0 at exact Human `1.0`, AI `0.0`, AI-assisted `0.0`.

The r14 experiment changed article prose only in the earlier Affection section and, separately, moved the half-document detector boundary to **before the complete Maturity section**. Its Part 2 therefore prepended the complete Maturity material while retaining the old 100%-Human Part-2 stream byte-for-byte as a suffix. r14 Part 2 SHA-256 was `c20e97cd3b168b4c9c7f5688a8e5c8f0a6d7fc558b875bc0ce02538c3579c515` and measured Human `0.9565388560295105`, AI `0.04346117004752159`, AI-assisted `0.0`, with four AI windows.

Those four r14 Part-2 AI windows appeared far downstream in:
- the opening of `Not A Performance`;
- the female strength / receiving / ordinary-role sequence;
- the vows / Biblical promise passage;
- the breakup-perspective passage.

Each of those passages was inside the exact old Part-2 suffix that had already measured 100% Human.

The r15 control changed **no article prose at all** from r14. It restored the old aggregate split immediately before the Key/guru continuation, yielding the exact prior Part-2 SHA `9e4c6a522c95741c7dfc9e040b2dcc40773427cbc0aef8f45211de77208b0c85`. That exact boundary retains its prior 100%-Human evidence. r15 Part 1 measured Human `0.9506160616874695`, AI `0.04938393086194992`, AI-assisted `0.0`.

## Finding

Half-document segmentation is part of the detector input. Changing only where a long document is split can create or remove AI windows **far downstream from the changed boundary**, even when the flagged passage itself is byte-identical and previously measured 100% Human.

This is stronger than the existing general rule that a red window is localization rather than causal attribution: the causal disturbance can be the aggregate boundary itself, and its effects need not remain boundary-adjacent.

## Durable rules

- After changing a long-document detector split, compare every newly red remote passage against exact prior-boundary evidence before rewriting it.
- If byte-identical prose was previously green and turns red only after segmentation changes, treat the new red window as boundary/composition evidence first, not as edit authority.
- Do not optimize article prose to repair remote windows created by an arbitrary half-document split.
- Keep detector segmentation stable during controlled prose comparisons whenever possible. When the split itself is the variable, change no prose and record that explicitly.
- Prefer coherent discourse boundaries over arbitrary mid-thought cuts, but do not assume a more natural split will score better; r14's more coherent pre-Maturity split made the downstream half worse.
- Section/local scores and half-document scores remain diagnostic unless they are the actual delivery boundary. Stable exact-boundary identity is required for causal comparison.

## Scope and limits

This is exact Pangram 4.0 evidence from one long Romance article lineage. It demonstrates that remote split sensitivity can occur; it does not quantify how often it occurs, identify Pangram's internal mechanism, or establish that every downstream regression after a split is noncausal.
