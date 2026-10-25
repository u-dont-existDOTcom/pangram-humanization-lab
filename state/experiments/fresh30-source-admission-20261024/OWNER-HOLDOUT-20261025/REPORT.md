# New-family evaluator check: style improved; deletion judgments remain unreliable

**2026-10-25. Research evidence, not a production acceptance rule. No new Pangram calls.**

## What was tested

The existing source-free style prompt was kept unchanged and applied to five different, previously owner-judged comparisons. Each was presented in both orders, in a separate restricted Claude Sonnet/medium context. The evaluator received neither owner answers nor earlier detector results. The curator had seen the labels; inputs, prompts and case choices were committed before evaluation, and all 22 initial responses were committed before scoring.

A separately frozen, narrower evaluator assessed twelve proposed deletions from twelve named sections. Six were owner-approved cuts and six were owner decisions to retain the wording. This measures agreement with editorial decisions, not external proof of semantic equivalence. The full owner answers and exact original questions remain the source of the labels.

These are new to this particular evaluator comparison, not pristine data across the project's history. The September contrasts had earlier developmental use. The original four recent calibration cases were excluded; the five style contrasts are not ten independent cases merely because their presentation orders were swapped.

## Style: four of five preferences matched consistently

| Exact comparison | Owner preference | Order 1 model rank | Reversed model rank |
|---|---|---|---|
| EFT portability | B, slightly; both still AI-like | A | Tie |
| Cross-domain transition | B, slightly; both still AI-like | B | B |
| Added polished explanatory ending | A, without the extra explanation | A | A |
| Personal movement versus instruction-like advice | A, the personal passage | A | A |
| Chart caption: “as best as I can fit” | A, retaining the qualifier | A | A |

The rank matched in 8 of 10 calls, representing 4 of 5 consistently matched comparisons. Three of these owner preferences were stronger/explicit; the first two were qualified preferences. The second comparison's successful relative ranking must not become a claim that the preferred version is acceptable: the owner said both still look AI.

The EFT case changed from preferring A to a tie when presented in the reverse order. A two-call comparison cannot isolate order effects from ordinary model variability, but its decision was not stable. The personal-versus-instruction case is not a same-thought edit, and the caption is only one sentence. These limitations preclude a general 80% accuracy claim.

## Deletion: only three of twelve exact recommendations agreed

The excerpt-based checker made 3 matching decisions, 6 opposite decisions, and 3 UNCERTAIN calls. The set was balanced 6 KEEP / 6 CUT; a constant recommendation would agree with 6 of 12. This is a small curated test, not a population benchmark.

The most concerning errors were not simple failures to notice what disappeared. The checker sometimes named a lost qualification or rhetorical function and still approved the cut because the main point remained.

For example, it acknowledged losing the statement that therapy can sometimes feel worse because awareness increases, yet called this a secondary generalization and accepted its removal. Joel's recorded answer was “h4. b it wouldn't even make sense anymore after cutting that, please.” It also approved removing the continuing relationship with benevolent spiritual beings and its joke; Joel explicitly rejected that cut. “When feasible” was dismissed as a redundant softener, despite Joel's explanation that people may fight too many battles and need to choose them.

Conversely, it wanted to retain two reassurances Joel approved cutting: that the exercise is not a test of having been loved enough, and that getting no response from a childhood photograph is completely OK. It was not applying a reliably owner-aligned distinction between necessary qualification and extra cushioning.

## Different architecture: supply the full surrounding section

Rather than adding another phrase rule, six definite disagreements were tested with the SAME task instructions and exact proposed deletion, but the complete original section was supplied. Fresh calls received no owner answers or previous verdicts. This was a diagnostic selected after observing failures, not a second held-out accuracy test.

Three of six decisions moved to the owner's choice:

- The photograph reassurance became an acceptable cut.
- The warning against imposing gratitude on someone who needs to grieve was retained as an action-changing condition.
- “When feasible” was retained because the surrounding section shows real costs of holding one's ground.

Three remained wrong relative to the owner: the test-of-being-loved reassurance was still protected, while the therapy-can-feel-worse explanation and continuing spiritual-relationship qualification were still cut. None became an author-approved edit. The other six initial cases were not rerun, so there is no full-context 12-case accuracy result.

This supports using sufficient source context, but context alone did not solve the valuation problem. The evaluator could recognize a genuine function and still call it secondary. That is an interpretation of its literal explanations, not a proven account of its internal mechanism.

## What can and cannot be used now

**Promising, limited use:** source-free pairwise style comparison as advisory evidence. It recognized four new owner preferences, including a longer caption and a less formally packaged transition. Do not turn its score into authorship, detector probability or automatic editorial approval.

**Not ready:** an autonomous preservation/cutting gate. Original thought, conditions, humor and actual author-intended functions cannot be reduced to a preserved gist. Known direct owner judgments control these cases and must not be reopened because a new model disagrees.

For current work, retrieve exact owner rulings first. Let a source-aware reader identify possible changes and quote the words at issue, without granting it authority to decide that an independent point is dispensable. A style preference cannot authorize deletion, and an implication already understood by readers need not be repeated just to satisfy a sentence inventory.

The next useful validation must concern specific unresolved functions on different owner-rated material, not another tuned global quality judge on these same cases. These newly inspected examples are now development data. No new generation method has been shown to improve article prose in this continuation.

## Evidence and recovery

BLIND-INPUTS.json contains exact source contrasts and source pins. GOLD-KEY.json preserves the direct owner answers and their limited interpretation. PROMPTS.json contains the unchanged style task and the separately frozen function task. OUTPUTS contains every prompt and raw textual model answer with SHA-256. RESULTS.json and CONTEXT-RESULTS.json retain every success, failure and uncertainty. SOURCE-SNAPSHOTS.json preserves original owner wording, including whitespace. Scripts run_validation.py and run_context_diagnostic.py performed the work; score_validation.py recomputes the initial score without calls.

No article master, accepted owner paragraph, active production rule, or detector output was changed. The owner-golden forgiveness revision remains golden and was not reused in these five style checks.
