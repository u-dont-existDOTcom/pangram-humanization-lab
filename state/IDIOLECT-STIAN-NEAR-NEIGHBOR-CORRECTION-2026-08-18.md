# Stian near-neighbor correction — 2026-08-18

## Owner correction

Joel reports that it is normal for Stian Gudmundsen Høiland's writing and thinking to resemble his. That resemblance was part of why they connected.

This is an owner-supplied relationship between authors. It changes the interpretation of the current benchmark; it does not retroactively change the measured cosine scores, predictions, hashes, or confusion matrices.

## Independent conception preserved

Before checking established work, the working correction was:

- Stian should remain in the candidate set because distinguishing Joel from a genuinely similar writer is a valuable hard test.
- Stian should not be treated like an arbitrary negative control.
- A rewrite moving from Joel to Stian may remain within a real stylistic/intellectual neighborhood rather than demonstrating simple genericization or erasure.
- The benchmark therefore needs separate results for Joel versus Stian, Joel versus ordinary matched controls, and the complete candidate set.
- Removing Stian can be useful only as a candidate-set sensitivity analysis, not as a way to improve the headline number.

## Bounded existing-work scan

The underlying problem is already partly established in authorship-attribution and authorship-verification work:

1. **Candidate-set composition matters.** Closed-set attribution is relational: the winner is the nearest author among the authors supplied. Changing the impostor/background set can change the decision even when the questioned text is unchanged.
2. **Hard negatives are informative, not defective controls.** Verification methods deliberately use difficult impostors or background authors to test whether a target is distinguishable from plausible alternatives rather than only from easy, unrelated authors.
3. **Topic, domain, platform, and register can masquerade as authorship.** Matched controls and source-group-disjoint evaluation are therefore necessary, but matching can also expose genuinely similar writers whom a broad benchmark would hide.
4. **LUAR-like authorship representations are not pure style coordinates.** They contain useful authorship signal, but style, content, discourse, domain, and evidence length are not fully separable. Distances are meaningful relationally; an isolated increase toward Joel cannot be interpreted without the competing-author distances.
5. **Abstention is an established response to insufficient separation.** When target and near-neighbor score distributions overlap, a calibrated system should be allowed to report uncertainty rather than forcing every text to one author.

Relevant established baselines include LUAR authorship representation, topic-leakage-controlled authorship evaluation, and impostor/background-set authorship verification. They support adaptation rather than a bespoke new metric.

## What is solved, partial, and unresolved

### Already solved or directly reusable

- source-group-disjoint train/holdout separation;
- matched topic/platform controls;
- closed-set nearest-profile scoring;
- explicit hard-negative/background-author roles;
- pairwise and candidate-set ablation diagnostics;
- uncertainty/abstention once margin distributions are calibrated.

### Partially solved

- deep authorship representations can improve attribution, but do not cleanly isolate style from content/domain;
- equal-length controls reduce one confound but do not make short passages stable;
- adding a hard negative makes evaluation more realistic, but aggregate accuracy can then obscure where the difficulty lies.

### Genuinely unresolved in this Joel benchmark

- whether Joel and Stian are reliably separable on independent, sufficiently long, same-register originals;
- how their natural between-author margin compares with Joel's own within-author variation;
- whether a rewrite moves away from Joel toward Stian specifically, toward ordinary controls generally, or merely within an uncertainty region;
- how these relationships change across philosophical dialogue, political polemic, health/practical writing, and personal/relationship prose.

## Method decision

**Adapt and compose**, rather than invent.

Keep the closed-set LUAR lane, but add:

- an owner-identified `hard-negative` role for Stian;
- at least two ordinary same-topic/platform controls before interpreting rewrite degradation;
- separate target-vs-hard-negative, target-vs-ordinary, and full-candidate results;
- candidate-set ablations with the hard-negative exclusion clearly labeled secondary;
- per-document target rank and pairwise margins;
- an abstention region calibrated only from independent original-text distributions.

Do not average these strata into one idiolect-preservation verdict.

## Correction to the first Romance transformation interpretation

The oxytocin owner rewrite increased cosine similarity to Joel by `+0.09258`, but increased similarity to Stian slightly more, changing the three-author nearest-profile winner from Joel to Stian.

The supported conclusion remains:

> Joel-only similarity is insufficient retention evidence.

The stronger earlier implication does **not** survive the owner correction:

> The Joel-to-Stian flip does not independently establish that Joel's idiolect worsened or was erased.

It is now a hard-negative/candidate-set counterexample. It demonstrates the need to compare all plausible authors and to understand the Joel–Stian natural margin before interpreting rewrite movement.

## Historical Dharma result under the corrected roles

The synchronized LUAR result remains numerically unchanged:

- whole document: Joel `3/4`, Stian `2/3`, with no Joel-to-Stian errors and one Stian-to-Joel error;
- exact 50 words: Joel `1/4`, with all three Joel errors going to Stian; Stian `3/3`.

Under the corrected role model, the exact-50 outcome primarily exposes unstable short-text discrimination between a target and an owner-identified near-neighbor. It is not clean evidence that short Joel text lacks idiolect, and it is not a reason to remove Stian.

## Full-vector follow-up

The frozen artifacts were re-read rather than recomputed. The complete owner-endpoint score movement is:

- Joel: `+0.092580`;
- Stian: `+0.104337`;
- David: `+0.109486`.

David—not Stian—had the largest cosine increase. Joel's margin against Stian narrowed by `0.011757`, while Joel's margin against David narrowed by `0.016906`.

This further restricts the interpretation. The owner endpoint became more similar to **all three** available profiles. It does not support a specific claim that the rewrite moved into a Joel–Stian neighborhood. The supported reading is narrower:

- the Joel-to-Stian winner flip is not clean erasure evidence;
- Joel-only similarity increase is not sufficient retention evidence;
- the pair is a broad, cross-author, cross-register movement counterexample;
- it is ineligible for IER or rewrite-degradation calibration.

The natural-original score ledgers also show that Stian is the harder negative specifically at exact 50 words: Joel is `1/4` against Stian but `4/4` against David. Whole-document evidence is less one-sided. All four current held-out source groups are shared-thread material, with zero non-overlap held-out groups, so the present evidence cannot distinguish general author proximity from topic, prompt, thread, or discourse accommodation.

Exact metadata-only receipts:

- `state/IDIOLECT-NATURAL-AUTHOR-NEIGHBORHOOD-DIAGNOSTIC-2026-08-18.json`
- `state/IDIOLECT-NATURAL-AUTHOR-NEIGHBORHOOD-SCORES-WHOLE-2026-08-18.json`
- `state/IDIOLECT-NATURAL-AUTHOR-NEIGHBORHOOD-SCORES-50W-2026-08-18.json`

## Next gate

Before another transformation run:

1. census and admit at least one additional ordinary Dharma control beyond David;
2. add non-overlap held-out originals for Joel, Stian, and ordinary controls;
3. only then batch a LUAR rerun that emits direct profile-to-profile cosines and complete per-document score receipts;
4. estimate natural-original target-vs-hard-negative and target-vs-ordinary margin distributions;
5. define a provisional abstention region from those originals;
6. test aligned rewrites only inside a register whose original attribution is stable under the predeclared condition.

The register-separated Joel corpus infrastructure is merged at `cf61352256832cd2fdf6f7a556559c418c2c4d71`, but no live corpus freeze or new LUAR run was performed by this diagnostic.

No IER, Tier-A threshold, `validated-for-register`, neighborhood-retention claim, or erasure claim is authorized by this correction alone.
