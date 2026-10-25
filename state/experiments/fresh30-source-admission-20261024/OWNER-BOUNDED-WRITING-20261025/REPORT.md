# Owner-bounded writing: preserving decisions without preserving every sentence shape

**2026-10-25. Development experiment on twelve known owner decisions; no article edits or new Pangram calls.**

## What changed in the method

The earlier model was asked to decide whether each qualification deserved to remain. It frequently disagreed with Joel, even after being given the full source section. This experiment removes that authority. The baseline first applies only the actual owner decision: six cuts, six keeps, and the additional correction from “There are just” to “These are just” in the caution-sign paragraph.

A fresh restricted-context writer then sees the complete source section and the explicit owner instruction. It may propose at most two local replacements, or none. A deterministic assembler preserves six specifically retained spans verbatim, rejects overlapping/invalid patches, and refuses exact restoration of deleted wording. These are conservative experimental controls, not a new universal ban on rewording or a claim that locks prove semantic fidelity.

All twelve first attempts were committed before review. Changed candidates received two separate fresh-context reads: the unchanged source-free style comparison, and a source-aware inventory of concrete changes in meaning. The latter was NOT asked whether it considered the owner's retained points important. Its task was to identify differences, not grant deletion authority.

## Observed outcomes

| Measure | Result |
|---|---:|
| Known source cases | 12 |
| Exact owner decision/locked-span constraints preserved | 12 |
| Writers chose no additional change | 6 |
| Writers proposed a local change | 6 |
| Small cleanups with consistent model style preference and no material delta reported | 4 |
| No clear style gain | 1 |
| Candidate rejected for a material meaning difference | 1 |
| Fresh model calls | 24 |
| New Pangram calls | 0 |

Scope preservation is achieved partly by construction. It is not a 12/12 score for learning which clauses are useful. The model was told the owner's decisions, rather than being tested on hidden decisions.

The four tentative cleanups were: “an inference you're guessing” to “a guess you're making”; removing the second nearby “too”; repairing quotation-mark placement around “glass half full”; and “keeping our ground” to “holding our ground,” with “when feasible” unchanged. They are model-reviewed local suggestions, not owner-approved prose or detector passes. The writer's explanation that an inference is necessarily a guess is not adopted as a general linguistic fact.

The “sounded” to “used to sound” change received equal numeric style scores but a slight verbal preference for the candidate. It is recorded as no clear style gain, not a success manufactured by choosing the favorable part of the review.

## The important failure: repeated words were not necessarily repeated thought

The source said:

> before that love starts to feel like yours, and then bit by bit it starts to become your own.

The candidate said:

> before that love gradually starts to feel like your own.

The writer described the source as saying the same thing twice. The style-only reviewer found the shorter version smoother, but its numeric score and verbal tie did not agree. More importantly, the separate delta reader identified a concrete loss: the source can distinguish first feeling ownership from gradually internalizing it. The rewrite retained gradualness but collapsed that sequence into a change in feeling alone.

The owner-retained sentence about continuing to relate to spiritual beings remained byte-identical. That did not make the whole candidate faithful. The surrounding explanation had changed, so the candidate is **fidelity-rejected** for this research; it is not installed anywhere. This conservative rejection preserves the distinction visible in the source rather than deciding for Joel that it was dispensable.

This is a specific, inspectable example of the broader compression concern: shared words do not prove shared function. It is not a general claim that shorter writing is worse, or that every apparent sequence deserves more words. The removal of the repeated “too” is a contrasting case where the independent reader found the additive relation remained carried by “And” and “also.”

## What this approach actually establishes

It provides a safer way to implement explicit corrections: decide authority from the owner's record, apply those decisions mechanically, and reserve generation for a limited residual wording task. Six no-change outcomes are legitimate restraint, not six failures to produce enough edits. None of the earlier keep/cut disagreements was reopened as an editorial vote.

It does NOT show that a model has learned the deeper transformation in the golden forgiveness example. Most proposed changes were small cleanup. Nor does the absence of a delta flag certify the other five proposals: the delta reader remains a model, the input set is familiar development material, and Joel has not judged these new variants.

The lesson is therefore bounded: exact owner constraints can remove one source of destructive editorial discretion, but they cannot substitute for understanding the relations in the rest of the passage. Local wording repair and whole-thought humanization remain different tasks.

## Evidence, limits and continuation boundary

All twelve cases are from one article and already have known owner judgments. They are not twelve independent authors, an untouched holdout, or a test of a universal stylistic operation. No claim of 80%, 100% or any population-level accuracy is made. The unchanged style prompt still produces occasional disagreement between its numbers and its stated preference; both are retained.

INPUTS.json pins the exact historical source/owner records and full-section context. CANDIDATES.json contains every first attempt/no-change. RESULTS.json records literal edit patches, model judgments and their disagreements. OUTPUTS holds every execution prompt and raw textual answer; verify_bounded.py checks exact source, prompt, response, assembly and score identities without calls.

No current article master, published copy, owner-final text or production rule changed. The next humanization trial should use genuinely weak model prose with a documented relational thought to recover, rather than treating these mostly readable owner-corrected excerpts as failed AI baselines. Do not add more phrase bans or buy detector calls merely to certify these grammar-level changes. These new results remain provisional, with the one meaning-changing candidate explicitly rejected.
