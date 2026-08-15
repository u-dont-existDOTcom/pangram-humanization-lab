# Romance Talk r32/r33 closeout — 2026-08-15

## Scope

This closes the `Talk about making love before you do it` / `If slow isn’t realistic for you` recovery sequence after the owner's fidelity correction to the father quotation.

The article opening remains the sole home of the father's exact direct quote:

> “Sex is what you do when you are older and you find a friend you want to have children with.”

The readiness / raising-children formulation is the owner's later paraphrase/lesson, not the father's direct speech.

## Authorial blocker resolved

The prior checkpoint incorrectly treated the missing relation after the father's quote as unresolved. The owner clarified that the article already explains the missing relation in its existing opening/final paragraph: the father's sentence was a useful basic explanation of sex, but it did not supply the larger romance/relationship curriculum. No new father anecdote or invented bridge belongs in `Talk`.

Accordingly, `Talk` was rebuilt only around its local heading promise and protected functions: distinguish making love from the physical act; explain why the honest conversation should happen before chemistry/consequences make honesty harder; surface practical mismatch/meaning concerns; allow real uncertainty; and hand off cleanly into the locked `Slow` section. The complete `Slow` bytes were preserved unchanged in both tests.

## r32 — best assistant reconstruction in this sequence

- Experiment: `romance-authorial-recovery-r32-owner-relation-2026-08-15`
- Exact candidate SHA-256: `950ee47a0d1d10912092fc40ee8534cf9086dab8556e42d25bc9bf8f954b97e3`
- Pangram 4: Human `0.7146716117858887`; AI `0.28532838821411133`; AI-assisted `0.0`; headline `AI Detected`
- Segmentation: opening 101 words Human; one 306-word AI window across the middle of Talk; final Talk tail plus the complete Slow section Human.
- Fidelity/editorial disposition: fidelity-valid; father attribution is correct; protected Talk functions retained; Slow unchanged; two cold audits found no semantic/reality/heading/join defect requiring repair.
- Detector disposition: below the project's exact 1.0/0/0 install gate, so it is evidence/candidate only, not detector-certified and not owner-final.

## r33 — architectural countertest

- Experiment: `romance-authorial-recovery-r33-live-mismatch-2026-08-15`
- Exact candidate SHA-256: `094a6cd66f3d45c6f7d834c3bbc80d8f6223ba404c44d2f5b10c1ac1f4ec1f89`
- Pangram 4: Human `0.6013631820678711`; AI `0.3986368477344513`; AI-assisted `0.0`; headline `AI Detected`
- Segmentation: the entire 428-word Talk section formed one AI-generated window; the complete Slow section remained Human.
- Fidelity/editorial disposition: fidelity-valid and coherent; Slow unchanged.
- Detector disposition: materially worse than r32. Do not prefer r33 merely because its internal architecture was changed from checklist-like exposition to live mismatch examples.

## Interpretation

r32 and r33 together strengthen the existing `ROMANCE-ARTIFICIAL-CHECKLIST-INCIDENT-2026-08-13` lesson: Pangram's rejection is not localized to one obvious phrase that can responsibly be fixed with synonym substitution. A substantive internal re-realization in r33 made the detector result worse and expanded the AI window to the whole Talk section, while the unchanged Slow section remained Human.

This is detector evidence, not proof that the Talk content is bad or inauthentic. The editorial/fidelity gate remains primary. Among these two assistant reconstructions, r32 is the better current candidate because it is editorially sound and materially stronger on the secondary detector evidence.

## Budget / stop rule

The call ledger now records six paid POSTs for the Talk/Slow Pangram-4 audit, exactly the configured section cap, with 11 estimated credits and zero pending resumes. No additional paid Talk/Slow request should be staged automatically in this audit.

## Authority / installation

`Talk about making love before you do it` is historical-retained source material in the current article assembly, not later owner-final prose. Therefore neither r32 nor r33 may be relabeled owner-authored or owner-final merely because it is fidelity-valid.

Current disposition:

1. Keep r32 as the best assistant candidate for the recovered Talk movement.
2. Keep the locked Slow section byte-for-byte unchanged.
3. Do not install r31: its false quotation attribution makes it fidelity-invalid regardless of its higher detector score.
4. Do not install r27: it dropped protected Talk functions.
5. Do not spend more automatic detector budget on assistant paraphrase variants.
6. If exact 1.0/0/0 remains a hard publication requirement for Talk, the next genuinely new evidence should come from an owner rewrite/re-realization in the owner's own syntax, not another assistant synonym pass.

## Evidence

- `experiments/romance-authorial-recovery-r32-owner-relation-2026-08-15.json`
- `state/experiments/romance-authorial-recovery-r32-owner-relation-2026-08-15-results.json`
- `experiments/romance-authorial-recovery-r33-live-mismatch-2026-08-15.json`
- `state/experiments/romance-authorial-recovery-r33-live-mismatch-2026-08-15-results.json`
- `state/pangram-call-ledgers/romance-authorial-recovery-2026-08-14.json`
- `state/ROMANCE-R31-FIDELITY-CORRECTION-2026-08-15.md`
- `state/ROMANCE-ARTIFICIAL-CHECKLIST-INCIDENT-2026-08-13.md`
