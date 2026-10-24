# Recurrence counterexamples and the next useful decision

Date: 2026-10-24
Status: retrospective archive analysis; provisional, not a new detector experiment
Parent goal: improve explicit recognition and faithful rewriting, without confusing Pangram agreement with Joel's assessment of natural prose.
New Pangram calls: 0. No blocked API or independent-evaluator operation retried. No production article edits.

## What this pass actually did

Reused the 102 exact Pangram 4.1 inputs from the preceding archive audit, verified their hashes and window offsets, and recomputed all 38 complete-block contextual label comparisons. Verified the checksums of their 19 saved source-result files against the immutable source manifest. Examined all targets occurring in more than one measured surrounding input, not only the envy paragraph. Compared repeated surface phrases and recovered a second one-sentence repair plus a counterexample.

Source: u-dont-existDOTcom/joel-articles@dc929e66beb4b06cbc8b80d5be7eec7cd967c89f, articles/inner-child-therapy/experiments/t97-api through t103-api.

## 1. Another local repair, with word count held constant

In t101_borrow_h3, the prior paragraph already says:

> And don’t expect a thank-you for the session, like they booked it.

The next paragraph began:

> The thank-you you weren’t waiting for might not come anyway.

The measured revision, t101b_borrow_h3, changes only that second sentence to:

> Your little one might not take it well at first.

Literal replacement reproduces the complete later input exactly; every other character is unchanged. Both changed sentences have ten whitespace-delimited words, and both full inputs have 353 words. The earlier full input was Mixed; the later input has all Human windows. The unchanged preceding paragraph also changed label. Low-confidence Human windows remain, so this is not uniform dark-green certification.

Records:
- t101-api/API-RESULTS-2.jsonl, line 2; input SHA-256 4b77aa15e37d3ff3c53b14b84b3df0e76ca1f4e20392abf00579108f3eaf081b.
- t101-api/API-RESULTS-3.jsonl, line 1; input SHA-256 c7ce22bd843b51760802f62d4fb6d30a3e8b94973daadcc18ccc6ad7f8f8d0af.

Interpretation limits: removing an echo co-occurs with removing a self-referential restatement of the preceding instruction. More importantly, the replacement broadens 'no thanks' to a potentially negative reception and adds 'at first'. This is not a pure word-repetition experiment. The constant word count rules out a changed total word count as the sole difference, not all segmentation or distribution effects. This pass does not establish that Joel prefers the new prose.

## 2. A local counterexample to echo removal

Heading, unchanged:

> A Belonging Deeper Than Any Group

The original first sentence contains:

> toward a belonging deeper than any group, one that

The revision replaces only that span with:

> toward somewhere you belong that

Every other character of the heading-plus-two-paragraph input is unchanged. Both complete inputs remain Mixed. Their first paragraphs separately had all-Human results. Therefore removing the exact heading phrase was not sufficient in this case. The standalone-to-context comparison adds the heading and following paragraph together; it cannot show which is responsible.

Records:
- t103-api/API-RESULTS-4.jsonl, line 1; input SHA-256 781506cce37df014663f63d3795ae4cc63de4e8674629a746f3c8738329edb46.
- t103-api/API-RESULTS-6.jsonl, line 1; input SHA-256 3e0e62a690d183a5f93b0808f3edf31760292a8391f080816c8b57fc045e80d2.
- Standalone: t103_98_9 and t103e_98_9_s06 in the same source series.

This does not refute the narrower possibility that repeated *advice structure* matters. It does prevent collapsing the hypothesis into 'remove any repeated words'.

## 3. A cheap surface check did not supply a useful discriminator

Among the 33 placements whose exact standalone target had all-Human windows:

| At least one shared consecutive phrase between target and outside context | Placements | Target acquired a non-Human window |
|---|---:|---:|
| Shared three-word phrase | 17 | 3 |
| No shared three-word phrase | 16 | 2 |
| Shared four-word phrase | 6 | 1 |
| No shared four-word phrase | 27 | 4 |
| Shared five-word phrase | 3 | 1 |
| No shared five-word phrase | 30 | 4 |

Method: lowercase Unicode word tokens, retaining internal apostrophes; compare target n-gram sets with the union of preceding and following context sets, never concatenating across the removed target. Exact substring and full-block identity were checked before comparison. No threshold was tuned to maximize accuracy.

This is a lexical recurrence proxy, NOT a measurement of prosody, semantic redundancy or rhetorical structure. It is retrospective, dependent, selected production evidence with only five regressions. No significance claim or generalized classifier follows. The outcome weakens a simplistic word-repeat rule, not Joel's observation about AI cadence.

## 4. Research decision

Do not spend another pass guessing whole-paragraph labels or adding bans. The local repairs suggest at least three competing explanations:

1. repeated wording / repeated advice structure;
2. a sentence re-explaining a thought the reader already understood;
3. a more useful change in the thought or reader interaction, not merely style.

The next useful evidence is Joel's assessment of the exact thank-you pair, separated into naturalness and meaning. The point is not to ask him to rubber-stamp Pangram. The envy example remains owner-disliked despite its Human outcome; that known judgment is retained and need not be requested again.

A small review view was prepared with the envy comparison as the known anchor, the thank-you change as the new question, and the heading-echo change as a counterexample. It shows archived wording, marks only the changed spans, and keeps detector outcomes collapsed by default. This is not genuinely blind: some material has already been discussed. Empty owner ratings remain unknown; detector results must never populate them.

### Exact next decision

**Does the replacement 'Your little one might not take it well at first' genuinely improve the naturalness of the two-paragraph passage, or do both versions still sound AI-shaped? Does it preserve the intended thought or improve/change the thought?**

If the owner regards the change as useful, the next pre-specified comparison should preserve the no-gratitude meaning while distinguishing plain repeated wording from the original self-referential reminder. If the owner regards both versions as AI-shaped, do not teach the detector-green variant as a positive example; retrieve another genuinely owner-approved episode. If meaning changed usefully, classify the episode as reauthoring rather than a clean style-only pair.

Any subsequent live check must use an exact natural boundary of 1–3 paragraphs, recover its cache, register predictions and the specific result-dependent decision first, and respect the existing tool execution restriction. The historical 353-word boundary above is not permission to resubmit a longer section. The previously blocked eight-cell study remains unexecuted.

## Persistence and completion scope

This note is durable research evidence on the existing review branch, not a merged production rule and not a solution to detector interpretability. The parent outcome remains OPEN. The achieved next step is a counterexample audit plus a concrete owner-calibration question; the unresolved gap is whether the measured repair is a good writing demonstration. No factual or therapeutic claims quoted as samples were newly endorsed or checked.
