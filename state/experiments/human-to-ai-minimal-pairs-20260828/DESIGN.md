# Human→AI minimal-pair packet — 2026-08-28

Status: **FROZEN STAGE 1 / six model-touched candidates / baselines not resubmitted**

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
