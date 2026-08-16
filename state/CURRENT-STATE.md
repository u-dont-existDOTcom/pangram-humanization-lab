# Pangram fixed-batch evidence branch current state

Updated: 2026-08-16

## Goal

Preserve exact detector evidence and the owner's no-click operating model with one reusable, budget-aware automatic runner. Ordinary changes remain free; paid work begins only from a new immutable request that byte-binds one fixed-batch spec on the exact evidence ref.

## Authority / baseline

- Evidence branch: `automation/pangram-fixed-batch`
- Automatic-run code/governance merge: `34621f38d702b5739e59cb8f81831604f01e5a52` (PR #23)
- Canonical article prose remains outside this evidence branch.
- Direct Joel rewrites supersede assistant candidates in editorial authority.
- The father's exact direct quote belongs once in the article opening: “Sex is what you do when you are older and you find a friend you want to have children with.” The readiness / raising-children formulation is Joel's later paraphrase, not father speech.

## Current Romance Talk checkpoint

The `Talk about making love before you do it` detector problem is no longer an unresolved authorial-thought problem.

The assistant r32 reconstruction was fidelity-valid and coherent but Pangram-red from `Once we're having sex...` through the middle of Talk. r33 re-realized the same material but performed worse. Joel then rewrote the red movement directly, preserving the substantive functions while removing repetition and overexplanation. Joel reports his replacement tested **100% Human, high confidence**.

The owner rewrite is preserved in:

- `state/ROMANCE-TALK-OWNER-COMPRESSION-LESSON-2026-08-16.md`

That file records the supplied prose, normalized SHA-256, before/after analysis, and the new durable process lesson.

### Provenance / detector status

- r32 assistant candidate SHA-256: `950ee47a0d1d10912092fc40ee8534cf9086dab8556e42d25bc9bf8f954b97e3`
- r32 Pangram 4: Human `0.7146716117858887`; AI `0.28532838821411133`; AI-assisted `0.0`.
- r33 assistant candidate SHA-256: `094a6cd66f3d45c6f7d834c3bbc80d8f6223ba404c44d2f5b10c1ac1f4ec1f89`
- r33 Pangram 4: Human `0.6013631820678711`; AI `0.3986368477344513`; AI-assisted `0.0`.
- Joel owner rewrite normalized supplied-passage SHA-256: `e01827ab773eafcf4840bce5cb43750c7d5a3f5ec4c325063c65ecf8d89f26d2`.
- Owner reports the rewrite tested 100% Human, high confidence. The lab did **not** independently capture the task ID/version/raw detector response for that owner-run test, so preserve it as owner-reported detector evidence rather than lab-verified raw evidence.

### Authority disposition

- Joel's direct rewrite supersedes r32/r33 as the current editorial candidate for the red Talk movement.
- r31 remains forbidden: it falsely placed Joel's later readiness paraphrase in quotation marks as father speech.
- r27 remains forbidden: it dropped protected C35–45 functions.
- The locked `If slow isn’t realistic for you` section remains unchanged.

## New durable lesson: why the assistant missed the fix

The failure was execution, not lack of a known principle. Existing lessons already said to avoid overcompletion and optimize for the next necessary move. The assistant nevertheless used the protected C35–45 function ledger as a production outline after r27 had been rejected for omissions.

That produced a model-shaped completion pattern: each protected function received an explicit sentence/mini-paragraph, examples were followed by explanations of their implications, and balanced counterparts were added for conceptual completeness.

Joel's rewrite reduced the red movement from roughly 347 words / 28 sentences to roughly 271 words / 19 sentences — about 22% fewer words and 32% fewer sentences — without materially dropping its functions. The main gains were:

- merge mirrored sentences into shared action (`we should also learn...`);
- replace three-sentence uncertainty aftercare with one live line (`Mind-reading is great if it happens...`);
- replace a balanced meaning taxonomy plus explanation with one consequential asymmetric example;
- compress the future-mismatch paragraph from a mini-essay to the actual point;
- replace vague final aftercare (`that tells me something`) with a real decision/stopping point (`that's a blocker`).

Blocking process rule going forward:

> Protected functions are outcome constraints, not sentence slots. Before escalating a detector-red boundary to a global architecture rewrite, run a lossless redundancy audit: label each sentence's job, merge repeated jobs, cut interpretation after examples that already demonstrate the point, reject symmetry added only for completeness, and stop when the reader's live question has actually been answered.

r33 is now understood as a weak test of the overcompletion hypothesis because it changed realization while preserving the same comprehensive function topology. A failed large rewrite does not prove the effect is globally distributed if the rewrite retained the underlying completion pattern.

## Paid-call state / stop rule

`state/pangram-call-ledgers/romance-authorial-recovery-2026-08-14.json` records:

- configured Talk/Slow section cap: 6 paid POSTs
- paid POSTs: 6
- estimated credits: 11
- pending resumes: 0

The cap remains exhausted. No extra Pangram call was made for this owner correction. Do not stage another paid Talk/Slow request automatically in this audit.

## Infrastructure state

- No detector/evidence workflow is currently active.
- Historic task workflows remain non-executable archived provenance.
- Pull requests and ordinary pushes run deterministic suite/audit only.
- Paid eligibility still requires the exact two-file immutable request/spec push contract.
- Hosted branch-protection / secret-control verification remains a separate repository-administration issue tracked in #17.

## Evidence / artifacts

- Owner compression lesson: `state/ROMANCE-TALK-OWNER-COMPRESSION-LESSON-2026-08-16.md`
- r32/r33 closeout: `state/ROMANCE-TALK-R32-R33-CLOSEOUT-2026-08-15.md`
- r32 spec/result: `experiments/romance-authorial-recovery-r32-owner-relation-2026-08-15.json`, `state/experiments/romance-authorial-recovery-r32-owner-relation-2026-08-15-results.json`
- r33 spec/result: `experiments/romance-authorial-recovery-r33-live-mismatch-2026-08-15.json`, `state/experiments/romance-authorial-recovery-r33-live-mismatch-2026-08-15-results.json`
- r31 fidelity correction: `state/ROMANCE-R31-FIDELITY-CORRECTION-2026-08-15.md`
- Artificial-checklist incident: `state/ROMANCE-ARTIFICIAL-CHECKLIST-INCIDENT-2026-08-13.md`
- Working lessons: `state/WORKING-LESSONS.md`
- Call ledger: `state/pangram-call-ledgers/romance-authorial-recovery-2026-08-14.json`
- Executable workflow: `.github/workflows/pangram-paid-dispatch.yml`
- Hosted-control follow-up: issue #17

## Next safe action

Use Joel's supplied rewrite as the Talk replacement in the article authority source outside this evidence branch, preserving the exact Slow bytes. For future humanization, apply the new lossless redundancy audit before any additional detector-driven reconstruction.

## Recovery rule

Before any future paid request, fetch the current evidence head and active Actions runs. Recover exact task IDs, cache, call ledger, result state, request identity, and spec digest from Git; never infer them from chat and never repeat an ambiguous or already-paid POST.
