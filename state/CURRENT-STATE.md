# Pangram fixed-batch evidence branch current state

Updated: 2026-08-15

## Goal

Preserve exact detector evidence and the owner's no-click operating model with one reusable, budget-aware automatic runner. Ordinary changes remain free; paid work begins only from a new immutable request that byte-binds one fixed-batch spec on the exact evidence ref.

## Authority / baseline

- Evidence branch: `automation/pangram-fixed-batch`
- Automatic-run code/governance merge: `34621f38d702b5739e59cb8f81831604f01e5a52` (PR #23)
- Canonical article prose remains outside this evidence branch.
- `Talk about making love before you do it` is historical-retained material in the current article assembly, not later owner-final prose.
- The father's exact direct quote belongs once in the article opening: “Sex is what you do when you are older and you find a friend you want to have children with.” The readiness / raising-children formulation is the owner's later paraphrase, not father speech.

## Current Romance Talk checkpoint

The prior “missing authorial relation” blocker is resolved. The owner clarified that the article already supplies the missing relation in its opening/final paragraph: the father's sentence was a useful basic explanation of sex, but it did not supply the larger romance/relationship curriculum. Do not invent another father bridge inside `Talk`.

Two fidelity-valid assistant reconstructions were tested while preserving the complete `If slow isn’t realistic for you` section byte-for-byte:

### r32 — current best assistant candidate

- Experiment: `romance-authorial-recovery-r32-owner-relation-2026-08-15`
- Candidate SHA-256: `950ee47a0d1d10912092fc40ee8534cf9086dab8556e42d25bc9bf8f954b97e3`
- Pangram 4: Human `0.7146716117858887`; AI `0.28532838821411133`; AI-assisted `0.0`; `AI Detected`.
- Segmentation: first 101 words Human; one 306-word AI window across the middle of Talk; final Talk tail plus complete Slow Human.
- Editorial/fidelity audit: pass. Protected Talk functions retained, no father misattribution, no substantive claim change, natural handoff to Slow, Slow unchanged.
- Status: best current assistant candidate, but not detector-certified and not owner-final.

### r33 — live-mismatch architectural countertest

- Experiment: `romance-authorial-recovery-r33-live-mismatch-2026-08-15`
- Candidate SHA-256: `094a6cd66f3d45c6f7d834c3bbc80d8f6223ba404c44d2f5b10c1ac1f4ec1f89`
- Pangram 4: Human `0.6013631820678711`; AI `0.3986368477344513`; AI-assisted `0.0`; `AI Detected`.
- Segmentation: entire 428-word Talk section AI-generated; complete Slow Human.
- Editorial/fidelity audit: pass, but detector result is materially worse than r32.
- Status: evidence/counterexample only; do not prefer over r32.

### Earlier exclusions still control

- r31: detector score improved to Human `0.7607057094573975`, but it falsely quoted the owner's later readiness paraphrase as father speech. Fidelity-invalid; never install.
- r27: dropped protected C35–45 functions; never install.

## Detector interpretation

The r32/r33 pair reinforces the existing artificial-checklist incident rather than revealing a magic phrase. Rebuilding the middle of Talk around live mismatch examples did not solve Pangram and made the detector result worse, expanding the AI window to the entire section. The unchanged Slow section remained Human. Treat this as secondary detector evidence, not as authority over article quality or authorship.

## Paid-call state / stop rule

`state/pangram-call-ledgers/romance-authorial-recovery-2026-08-14.json` now records:

- configured Talk/Slow section cap: 6 paid POSTs
- paid POSTs: 6
- estimated credits: 11
- pending resumes: 0

The cap is exhausted. Do not stage another paid Talk/Slow request automatically in this audit.

## Current disposition

- Preserve r32 as the best assistant reconstruction candidate for Talk.
- Preserve the locked Slow section exactly.
- Do not install any detector-failing assistant candidate as owner-final merely to advance state.
- Do not spend more automatic detector budget on synonym/paraphrase variants.
- If exact 1.0/0/0 remains a hard publication requirement, the next genuinely new Talk evidence should be an owner rewrite/re-realization in the owner's own syntax, followed by a new explicitly authorized audit rather than continuation of this exhausted six-call audit.

## Infrastructure state

- All historic task workflows remain non-executable archived provenance.
- Pull requests and ordinary pushes run deterministic suite/audit only.
- Paid eligibility requires the exact two-file immutable request/spec push contract.
- Hosted branch-protection / secret-control verification remains a separate repository-administration issue tracked in #17.

## Evidence / artifacts

- Closeout: `state/ROMANCE-TALK-R32-R33-CLOSEOUT-2026-08-15.md`
- r32 spec/result: `experiments/romance-authorial-recovery-r32-owner-relation-2026-08-15.json`, `state/experiments/romance-authorial-recovery-r32-owner-relation-2026-08-15-results.json`
- r33 spec/result: `experiments/romance-authorial-recovery-r33-live-mismatch-2026-08-15.json`, `state/experiments/romance-authorial-recovery-r33-live-mismatch-2026-08-15-results.json`
- r31 fidelity correction: `state/ROMANCE-R31-FIDELITY-CORRECTION-2026-08-15.md`
- Artificial-checklist incident: `state/ROMANCE-ARTIFICIAL-CHECKLIST-INCIDENT-2026-08-13.md`
- Call ledger: `state/pangram-call-ledgers/romance-authorial-recovery-2026-08-14.json`
- Executable workflow: `.github/workflows/pangram-paid-dispatch.yml`
- Hosted-control follow-up: issue #17

## Recovery rule

Before any future paid request, fetch the current evidence head and active Actions runs. Recover exact task IDs, cache, call ledger, result state, request identity, and spec digest from Git; never infer them from chat and never repeat an ambiguous or already-paid POST.
