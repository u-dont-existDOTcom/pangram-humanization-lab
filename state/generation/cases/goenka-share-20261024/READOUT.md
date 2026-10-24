# Owner-linked Goenka/metta Pangram report — local repairs and GPT-method results

Date: 2026-10-24
Status: **research/owner review, not owner-final article authority**
Source: user-supplied shared Pangram report `https://www.pangram.com/feed/009da24e-89ca-4f3c-a71a-91fee2d15c3e`.
Report: Pangram 4.1, 1,968 words, 14% AI / 86% Human on **original full report**, 51 highlight spans, 12 AI spans in six natural editing clusters. Exact displayed spans/source neighboring context: `ai-units-frozen.json` and preserved laptop `segments.json`. Neither the report text nor its user-shared URL establishes GitHub canonical article master.

## What was actually done (not just proposed)

1. The authenticated Pangram share was opened with Playwright via Joel's connected laptop. Exact segment text and GUI shading/labels were extracted without OCR.
2. Fresh GPT-6.1 Sol High semantic planner produced six source-grounded maps. Six independent fresh writers then generated from original source + map. Independent fresh Claude Opus audit rejected five of six for changes in claim scope, voice, attribution or formulaic aftercare. These outcomes are **not transferable generator skill**.
3. Tested structurally different writers without original AI-shaped spans, using plan + unchanged green neighbors. Many outputs still collapsed into conditional guides or accidentally changed what the author said. An independent audit rejected or questioned several.
4. Created source-anchored local replacements and had a separate independent Claude Opus review. Several were rejected **before Pangram**; only two passed the meaning check and had plausible natural-boundary revisions. Their exact replacement contexts/hashes/predictions were frozen before testing in `pangram-v4-preflight.json`.
5. Authenticated Pangram GUI submitted each of these two excerpt inputs exactly once. An older local GUI parser timed out looking for obsolete Pangram HTML elements despite successful scans; recovered exact Pangram 4.1 History records without repeat submissions. Exact structural `response.overall` outputs plus SHA/word counts are in `pangram-scopes-exact-readout.json`.

### Two measured successes (not whole-article certification)

**B — Kindness-first order, local excerpt 77 words**, including unchanged green neighboring text. Exactly tested replacement:

> The Buddha taught that kindness was necessary preparation for real nibbana meditation. Goenka puts it after nine days of the intense stuff instead. I’d want that kindness there when trauma starts coming up, not nine days in.

Pangram 4.1 exact stored History: **99.4509875% Human**, document confidence **Low** (short-text UI “Possibly human”). Original highlighted text in `ai-units-frozen.json`. Editorial caveat: preceding green text already says Goenka introduces metta on day ten, so the owner should read for repetition in the real section. No independent fact-check of attributed Buddha teaching was performed.

**F — Intro to survivor accounts, local excerpt 117 words**, including unchanged green introduction and two survivor-story summaries. Exactly tested replacement:

> You can skip these accounts if you don’t need them; some are rough to read. They’re anecdotes, not a measure of how often this happens.

Pangram 4.1 exact stored History: **100% Human**, document confidence **High**; GUI may still show the generic short-text “Possibly human” warning. This retains the reader's option to skip and the distinction between anecdote and incidence data.

### Other passages — not solved/approved

- **A — Metta allows care without desperation:** short casual rewrites sometimes changed whether metta *allows* a wish versus merely *helps*, who bears the fear/desperation, or presupposed the reader already wants suffering to end. Do not claim a clean pass.
- **C — Oliver anecdote:** removing formulaic caveat wording repeatedly narrowed the non-prescriptive statement to copying *his five weeks in a cave*, or weakened “one reason to take the metta-first possibility seriously.” The entire anecdote also includes ayahuasca, so the scope of the non-prescription matters. Do not silently delete the limit.
- **D — Retreat alternatives:** all candidate approaches so far either preserved the source's nested conditional structure and still sounded AI-shaped, or lost claims/conditions about *gentler ways*, the writer's conditional choices, **Plum Village or any other considered retreat**, and whether **pausing is treated as an ordinary option by the retreat**. A combined D/E move additionally displaced unchanged green text and added an oppositional tagline; it failed independent fidelity review. STOP local same-method reparaphrasing until owner weighs the permitted structural tradeoff. No new Pangram result for D/E.
- **E — Character-test conclusion:** categorical “A trauma-informed retreat shouldn’t turn continuing into a test of character” must not become the softer personal doubt “I'd question how trauma-informed it really is,” or add claims about coercion. Reader agency “Your path is yours to shape” is separately protected; untested alternative wordings remain proposals only.

## Learning conclusion

This case does **not** show generalized GPT-on-new-target Human writing. B/F show locally successful, source-anchored edits in context; four other marked AI regions remain unresolved. The main consistent generation failure is confusing the author's *actual logical role and force* with a polished, comprehensive safety/contingency template, even after a separate meaning planner. A fresh writer often converts warnings about a retreat's handling of pausing into generic personal permissions, adds new steps or hedges, or overwrites the owner's committed judgment.

Do not add another global ban for “If,” “I’d,” or “though.” The needed difference is composing around genuine causal/reader decisions while keeping actor, condition and certainty fixed. If the author wants a stronger claim, that is owner re-authoring, not silent detector repair. Pangram results are **scope-specific** and not authorship proof.

## Owner-facing delivery

A full six-passage side-by-side HTML review packet was generated in this conversation as `goenka_pangram_before_after_review_20261024.html`, with the two verified passages and the four speculative/rejected entries distinctly labeled. It also reproduces two earlier GPT-only somatic examples that Joel requested to read. No external Substack post was edited; no article master or owner-final source overwritten.

## Remaining editorial dependency

Joel's reading judgment on candidate B/F and authorization of any substantive D/E restructuring. The original six source spans remain exact in the frozen source. The next detector test, if any, must be a specific meaning-clean local/section repair with prediction frozen before submission; avoid duplicate tests of already stored hashes.
