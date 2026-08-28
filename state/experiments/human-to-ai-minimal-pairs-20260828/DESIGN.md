# Human→AI minimal-pair packet — 2026-08-28

Status: **COMPLETE / fifteen model-touched candidates / baselines not resubmitted**

Purpose: start from genuinely human Joel prose and change one primary editorial/model feature at a time to learn which interventions can introduce Pangram-AI signal. This is detector research, not proposed article prose and not article authority.

Owner authorization: up to **15 paid calls** if required for understanding. Calls are adaptive, not a quota. Stage 1 contains six candidates; later calls are allowed only when a Stage-1 result identifies a decision-relevant interaction, counterexample, or repeat need.

## Anchor result

R09 held its first paragraph byte-identical to R08 and appended one 66-word model/editorial paragraph. Joel reported:

- paragraph 1: **Human / high confidence**;
- paragraph 2: **AI / high confidence**.

The added paragraph bundled several functions, so R09 proves that model-added connective/expository material can introduce a strong local AI signal but does not isolate which feature did it.

## No-submit Human baselines

| Baseline | Register | Exact identity | Current evidence | Submission rule |
|---|---|---|---|---|
| A0 | first-person confessional / inner-child conflict | R08 normalized text SHA-256 `6ceaa3becafb78bb75df043e5ff88cd41d46496ef93d9a0500b6759856c5811a` (terminal-newline-normalized) | R08 Human/medium; same paragraph in R09 owner-localized Human/high on 2026-08-28 | Do not submit. |
| B0 | research-conversational / cancer | file SHA-256 `26720c63247e52278d1820bd683aafee689870d59332d21334e0254084e86a84`, 270 words; source `experiments/somatic-genre-calibration-owner-cancer-20260822-a.json@automation/pangram-fixed-batch` | Pangram 4 Human `1.0`, High confidence | Do not submit. |
| C0 | compact therapy explanation / owner-preferred Somatic intro | file SHA-256 `d71d468efb46c3eda21193ef6a5377a742b43007d31930235425fdbac0cc4ee7`, 108 words; source `cases/somatic-intro-owner-human-vs-model-ai-low-20260827.md` | owner-reported Pangram Human | Do not submit. |

These controls are not rerun under Joel's 2026-08-28 correction: untouched ordinary human prose is not a useful paid control in his observed corpus outside the known technical/academic exception class. Causal conclusions therefore remain bounded by the recorded baseline evidence and exact current candidate results.

## Stage-1 candidates

| ID | Primary controlled feature | Secondary style tags | Exact file SHA-256 | Words | Exact delta |
|---|---|---|---|---:|---|
| A1 | explanatory completion | significance staging; balanced contrast | `78966db7d5fae9e891d6b941cb8efe918e543bb65427f5381a962360b7941279` | 145 | Append one sentence that labels the demonstrated trust problem; A0 otherwise byte-identical. |
| A2 | sentence equalization | clause repartition; polished cadence | `45b10d6457f9199276c3ea95a8a53c837833fdef64b39cd98b265fc90669d1a1` | 125 | Repartition long clauses into shorter, more even sentences with minimum grammar repair; no proposition added or removed. |
| B1 | taxonomy/list closure | three-part parallelism | `a729a0ff68111e19a2562efdc735e4f7afaf0a770e74bd5dcc0b2815144668f8` | 295 | Append one three-category synthesis of treatment states already present; B0 otherwise byte-identical. |
| B2 | model-generated connective tissue | polished transition; significance staging | `fd769658a9e4cec311066b586d23be325e924bd5f2fc918baabb8df14bad75f6` | 280 | Insert one abstract bridge between the two existing paragraphs; B0 otherwise byte-identical. |
| C1 | abstraction/compression | denser clauses; explicit cross-domain synthesis | `b115de4e6f70c09eaa6a35245f5fbc4bdf06fcc2b7fc3dce3de685e3394e7c12` | 91 | Compress 108 words/three paragraphs to 91 words/one paragraph while retaining all protected claims and attributions. |
| C2 | polished transition | model-style cross-paragraph connective tissue | `1c9f634c4cb1233a225d15406e50a90eec00c9b51462db25ca3785164a50a7c0` | 112 | Replace only `In inner-child therapy,` with `The same principle extends to inner-child therapy:`; all other bytes unchanged. |

## Preservation receipt

All six candidates are diagnostic-only and barred from article authority.

- A1: base propositions unchanged; appended sentence is a faithful restatement of the already-demonstrated love/trust distinction. Unexplained substantive deltas: 0.
- A2: adult/child actors, distrust, resentment, war, protection/nurturing vow, child challenge, and relaxation result all remain. Only sentence/coordination architecture changes. Unexplained substantive deltas: 0.
- B1: source text unchanged; the new taxonomy maps exactly to lower-trust treatments, newly discovered treatments, and reader-requested future investigations already present. Unexplained substantive deltas: 0.
- B2: source text unchanged; the bridge states the already-demonstrated relation between research method and recommendations. Unexplained substantive deltas: 0.
- C1 preserves: physical response after danger despite conscious safety; complex/developmental deepest-memory overwhelm; gradual approach; Pema Chodron/Buddhist-nun attribution and feather touch; Peter Levine/founder attribution, Somatic Experiencing, work around the edges, and pendulation; knowing the younger part's need while losing enough adult perspective to provide it. Unexplained substantive deltas: 0.
- C2 changes only the explicit transition relation. All source claims and attributions are byte-identical. Unexplained substantive deltas: 0.

Forward traceability: **PASS**. Reverse traceability: **PASS**. Article authority impact: **none**. Detector eligibility: **PASS**.

## Stage-2 results and Stage-3 stopping packet

| ID | Result | Structured score | Interpretation |
|---|---|---:|---|
| C3 | Human | AI `0.0`, Human `1.0` | One-paragraph packing alone was insufficient. |
| C4 | Human | AI `0.0`, Human `1.0` | Explicit cross-domain relation in colloquial wording was insufficient. |
| C5 | Human | AI `0.0`, Human `1.0` | C1's compression package without explicit synthesis was insufficient. |
| C6 | Human | AI `0.0`, Human `1.0` | Compression confined to the middle explanatory paragraph was insufficient. |
| A3 | Human | AI `0.0`, Human `1.0` | Explanatory completion × sentence equalization remained null on the confessional baseline. |
| B3 | Mixed | AI `0.132098034`, Human `0.8679019809` | Taxonomy closure × polished bridge introduced middle-part AI signal although each edit alone was Human. |

Stage 2 therefore supports an interaction account: C1 crossed the boundary only when abstract compression and model-polished cross-domain synthesis appeared together; B3 crossed when taxonomy closure and polished connective tissue appeared together. Stage 3 uses the owner's remaining three-call allowance only for alternate realizations that test whether those interactions generalize.

| ID | Comparison | Primary question | Exact SHA-256 / words | Exact delta |
|---|---|---|---|---|
| C7 | C5 + alternate polished transition | Does compression × polished cross-domain synthesis generalize beyond C1's exact `same limit appears` wording? | `fc023c3f605c1ffedcbf0939133b436cc749cffda9347c48bdfa6d8291c9687a` / 91 | Replace only `In inner-child therapy,` with C2's `The same principle extends to inner-child therapy:`. |
| B4 | B3 with colloquial bridge | Does the cancer interaction require the polished bridge realization? | `c6896d2182b2f55155422dc36bcb428822df204124da37c62f66112bb9fd941f` / 309 | Replace only `That experience is why the method matters alongside the recommendations.` with a first-person colloquial restatement. |
| B5 | B3 with colloquial closure | Does the cancer interaction require the polished three-part taxonomy realization? | `9562f1c63483b5fa6658ab435f594f13a53fc25ec4de78b2912b0ff55c458983` / 304 | Replace only the three-category sentence with two uneven, colloquial sentences preserving all three category claims. |

### Stage-3 preservation receipt

- C7 changes only the relationship lead-in; all C5/C1 protected claims and attributions remain. Unexplained substantive deltas: 0.
- B4 retains B3's exact taxonomy and both owner-source paragraphs; the bridge restates the same method/recommendations relation in first person. Unexplained substantive deltas: 0.
- B5 retains B3's exact bridge and both owner-source paragraphs; its two closure sentences preserve lower-trust treatments, newly discovered treatments, and possible reader requests without the closed taxonomy form. Unexplained substantive deltas: 0.

Forward traceability: **PASS**. Reverse traceability: **PASS**. Article authority impact: **none**. Detector eligibility: **PASS**. Stage 3 is the stopping packet; no further paid calls are authorized or needed for this experiment.

## Stage-3 results and conclusion

| ID | Result | Structured score | Interpretation |
|---|---|---:|---|
| C7 | AI | AI `1.0`, Human `0.0` | Compression × polished cross-domain synthesis reproduced with alternate transition wording. |
| B4 | Human | AI `0.0`, Human `1.0` | Colloquializing only the bridge removed B3's Mixed signal. |
| B5 | Human | AI `0.0`, Human `1.0` | Breaking only the neat taxonomy closure removed B3's Mixed signal. |

The durable finding is interactional. On compact Somatic explanation, abstract compression and polished cross-domain synthesis were each insufficient in the relevant counterexamples but together produced AI `1.0` twice. On long research-conversational prose, a polished bridge and a closed parallel taxonomy were each insufficient alone but adjacent use produced a Mixed result; replacing either realization with a colloquial, uneven equivalent restored Human.

Do not turn these results into phrase bans. Preserve natural owner thought routes, minimize model-generated relationship announcements, and test complete boundaries when multiple editorial closures accumulate. Exact structured results and call accounting are in `RESULTS.json`; durable interpretation is in `LESSONS.md`.

## Duplicate and transport gate

- local content-addressed cache: checked for all six exact file hashes; no completed result and no ambiguous reservation;
- authenticated Pangram application History: exact-bound recovery checked for all six; no match; no detector submission occurred during recovery;
- transport: current `pangram-local` main runner, dedicated persistent Pangram profile, Brave/Chromium, Pangram GUI;
- owner UI correction: remaining candidates run in one background browser session with tab reuse; do not foreground/close/reopen tabs between candidates;
- every paid click must have a durable pre-click reservation and exact file-SHA gate;
- after any ambiguous click, recover before repeat; `--force` is prohibited without exact evidence review.

## Adaptive follow-up rule

Stage 2 may use up to nine further calls, but only as follows:

1. If a single-feature candidate flips AI, test the smallest realization/counterexample needed to distinguish the feature from its local wording.
2. If two related single features are null but their interaction is plausible, run the combined cell on the same fixed baseline.
3. Repeat an exact candidate only when the result is Mixed/low confidence or when reproducibility is necessary before a durable causal claim.
4. If all six are Human, do not token-hunt. Use the remaining budget only for a predeclared interaction such as explanatory completion × polished connective tissue or clause balancing × sentence equalization.
5. Stop when the effect is distributed/interactive enough that another call would only create phrase folklore.

Exact inputs live under `state/experiments/human-to-ai-minimal-pairs-20260828/inputs/`.

## Stage-1 results

All six results were submitted through the authenticated Pangram GUI in one headless Brave session with tab reuse, durable pre-click reservations, exact SHA gates, and exact UTF-8 History transport binding. Pangram version: 4.0.

| ID | Result | Structured score | Interpretation |
|---|---|---:|---|
| A1 | Human | AI `0.0`, Human `1.0` | Explanatory completion alone was insufficient on the confessional baseline. |
| A2 | Human | AI `0.0`, Human `1.0` | Sentence equalization alone was insufficient on the confessional baseline. |
| B1 | Human | AI `0.0`, Human `1.0` | Taxonomy/list closure alone was insufficient on the research-conversational baseline. |
| B2 | Human | AI `0.0`, Human `1.0` | One abstract bridge alone was insufficient on the long research-conversational baseline. |
| C1 | AI | AI `1.0`, Human `0.0` | The abstraction/compression package crossed the detector boundary. Confidence was limited by short text. |
| C2 | Mixed | AI `0.3076923192`, Human `0.6923077106` | Replacing only the final paragraph lead-in with a polished cross-domain transition introduced later-part AI signal. Confidence was limited by short text. |

Read-only localization could not re-bind Pangram's History rows after the completed receipts had already been stored. No repeat was attempted: the result-page capture itself reports that C2's AI-generated content appears in the later part, while C1 was classified as entirely AI.

## Stage-2 decomposition and interaction cells

| ID | Comparison | Primary question | Exact SHA-256 / words | Exact delta |
|---|---|---|---|---|
| C3 | C0 → C3 | Is one-paragraph packing sufficient? | `b3f7120403408aa7d9db8f0d8f7fc92f8d449df63da827332e5ff80f2e8dbbfa` / 108 | Remove the two paragraph breaks; all words and punctuation otherwise identical. |
| C4 | C0 → C4, counterexample to C2 | Does explicit cross-domain relation generalize beyond C2's polished wording? | `707e14ba5942801cf985240ad64df1dc5c01967a0395b5800363f0845b09d009` / 111 | Replace only `In inner-child therapy,` with the more colloquial `This also happens in inner-child therapy:`. |
| C5 | C1 → C5 | Is C1's compression package sufficient without explicit cross-domain synthesis? | `5a00ed0537636acac1cd3c13b5e0e32eb398b9844006456c13458b8d8612697d` / 87 | Replace only `The same limit appears in inner-child therapy:` with baseline lead-in `In inner-child therapy,`. |
| C6 | C0 → C6 | Is compression of the explanatory middle paragraph sufficient while boundary paragraphs stay Human-baseline exact? | `d3453f1a84f937ec6eae2cedc00448e65acc527b66e42b4fe2569467b6204d74` / 92 | Replace only paragraph 2 with its C1 compressed counterpart; retain paragraph breaks and baseline paragraphs 1 and 3. |
| A3 | A2 + A1 sentence | Do two individually null interventions interact? | `d4cbb9c52499af0c05ac639a6c58aae38ef2c44351a896f277948e7ff34b8c31` / 144 | Append A1's exact explanatory-completion sentence to A2; no other change. |
| B3 | B2 + B1 sentence | Do two individually null interventions interact? | `82a3b66f9cf4f2f4162fbffa7c8ffaaa89a78dc61c9f8a4600c0f2c19b1e1311` / 305 | Add B1's exact taxonomy sentence to B2; no other change. |

### Stage-2 preservation receipt

- C3 changes layout only. Claims, wording, punctuation, and attributions are unchanged. Unexplained substantive deltas: 0.
- C4 makes the cross-domain relationship explicit in a less polished realization; all source claims and attributions are otherwise byte-identical. Unexplained substantive deltas: 0.
- C5 keeps every C1 claim and attribution and removes only its explicit synthesis phrase. Unexplained substantive deltas: 0.
- C6 retains C0 paragraphs 1 and 3 exactly; paragraph 2 preserves overwhelm, gradual approach, Pema Chodron/Buddhist-nun attribution and feather touch, Peter Levine/founder attribution, Somatic Experiencing, edge work, and pendulation. Unexplained substantive deltas: 0.
- A3 is the exact union of the already-receipted A1 and A2 deltas. Unexplained substantive deltas: 0.
- B3 is the exact union of the already-receipted B1 and B2 deltas. Unexplained substantive deltas: 0.

Forward traceability: **PASS**. Reverse traceability: **PASS**. Article authority impact: **none**. Detector eligibility: **PASS**.
