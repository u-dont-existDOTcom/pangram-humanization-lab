# Specialized humanization audit development — GPT-6 Sol result

Date: 2026-09-23
Status: SCOPED PROCESS SUCCESS / GLOBAL-JUDGE FAMILY RETIRED / NO PANGRAM CALLS

## Why this experiment exists

Four materially different attempts to make one external LLM emit a global Human/AI or good/bad-realization verdict failed to generalize:

1. abstract authorship rubric v1 — 14/20;
2. hard scaffold-veto v2 — 10/20;
3. literal contrastive absolute holdout v3 — 10/20 after 11/12 development;
4. matched pairwise realization-defect chooser — 5/8.

Those failures reached the method-escalation threshold. The production task was decomposed into narrow observable audits instead of adding another global rule stack.

## Current scoped auditors

### Reader-purpose / pragmatic act

Seeded controls:
- RP1 — readiness paragraph under `Before You Try to Go Deep`: expected PASS, got PASS.
- RP2 — dangerous-present-adult H2 in its natural local boundary: expected FAIL, got FAIL.

Score: **2/2**.

The RP2 failure matched Joel's correction: the passage silently switched from the ordinary guide user to a hypothetical adult who enjoys frightening/humiliating vulnerable people, with no visible reason for that reader/problem to appear there.

### Cumulative instruction-manual/listicle cadence

Seeded controls:
- CD1 — readiness paragraph: expected FAIL, got FAIL.
- CD2 — dangerous-present-adult paragraph: expected FAIL, got FAIL.
- CD3 — known Human/no-AI 5-MeO hypothesis list: expected PASS, got PASS.
- CD4 — direct owner Human/medium advice paragraph: expected PASS, got PASS.

Score: **4/4**.

This is the discrimination Joel asked for: a literal list or direct advice can be Human; the failure is the cumulative question/command/condition/verdict/lesson staircase.

### Antecedent / referent coherence

V1 found the orphaned `ask` but overcalled a source setup paragraph.

V2 improved role classification but its controls were partly malformed: one supposed PASS isolated a Human paragraph while hiding real dependencies such as `also` / `Ball`; another tested the setup sentence itself rather than the later `ask` sentence.

V3 corrected the experiment:
- AV3-1 — same humanized `ask` paragraph without source setup: FAIL.
- AV3-2 — same exact paragraph with `“Voice,” “ask,” and “answer”` source setup restored: PASS.
- AV3-3 — self-contained known Human/no-AI paragraph: PASS.
- AV3-4 — controlled deletion removing the subject antecedent before `They`: FAIL.

Score: **4/4**.

## Combined result

Current owner-correction-relevant controls: **10/10** across three narrow axes.

This is **not** evidence that GPT-6 Sol can determine hidden authorship, certify Human prose, or catch every possible humanization defect.

It supports a narrower and more useful process claim:

> A fresh model can be useful as a set of narrow falsification auditors for observable editorial defects when each audit asks one question and is calibrated on positive and negative examples for that exact question.

## Process correction

Retire the global provenance-authorship classifier as a production admission gate.

Do not ask one fresh critic to decide `Human vs AI` and then treat its non-detection as a certificate.

Instead:
1. run the applicable narrow audits on the natural reading boundary;
2. each audit reports exact spans and only its own defect class;
3. use owner/editorial controls for that axis, not model-authorship provenance, as the calibration label;
4. an axis auditor that fails its regression controls is non-gating until repaired;
5. any narrow FAIL is a concrete repair candidate, not proof of AI authorship;
6. absence of FAILs still requires the editor's direct natural-boundary read;
7. Pangram remains downstream of preservation/coherence/editorial admission and cannot rescue a failed unpaid audit.

For the dangerous-present-adult case, the unpaid gate should have blocked before Pangram on at least three independent grounds:
- cumulative manual cadence;
- missing reader-purpose/pragmatic setup;
- broken `ask` antecedent in the following accepted paragraph.

## Scope

No Pangram call was used in this debugging sequence after the six-call dangerous-adult budget was exhausted.

This result is project/process evidence. It does not promote phrase bans or a universal authorship detector.
