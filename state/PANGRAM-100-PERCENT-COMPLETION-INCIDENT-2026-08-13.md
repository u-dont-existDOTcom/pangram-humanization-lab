# Pangram 100% Human completion-gate incident — 2026-08-13

## Status

Promoted owner correction.

## Observed failure

Joel reported that a requested humanization pass stopped at 93% Human. He requires the pass to continue until the exact intended delivery boundary measures 100% Human, unless the worker genuinely does not know a further faithful and coherent repair. At that point the worker must identify the exact unresolved passage and ask Joel for the narrow authorial help needed. A partial score is not a completed delivery.

## Root cause

The canonical instructions required prose to meet “the required Pangram criterion” and described some measured candidates as `detector-green`, but did not define Joel's standing acceptance criterion in detector fields. The operational runbook required `STAGE_SUCCESS` and detector version `4.0` without checking the Human/AI fractions. Pangram can therefore return a successful result and a Human headline while still assigning less than 100% of the measured boundary to Human.

The missing definition allowed 93% Human to be treated as terminal progress instead of an unresolved detector result.

## Promoted rule

When Joel requests Pangram humanization, completion requires the exact intended delivery boundary to return all of the following from Pangram 4:

- `detector.stage == "STAGE_SUCCESS"`;
- `detector.version == "4.0"`;
- `detector.fraction_human == 1.0`;
- `detector.fraction_ai == 0.0`; and
- `detector.fraction_ai_assisted == 0.0`.

A `Human` headline, `prediction_short == "Human"`, or partial result such as 93% or 99% Human is progress only. It is not a pass and must not be reported as complete.

Continue faithful, coherence-preserving repair and exact-boundary retesting until the criterion is met. Stop the editorial repair loop only when the worker genuinely lacks a further faithful and coherent repair. That is an unresolved authorial handoff, not completion. Report the exact failing span and boundary, current exact score and result hash, attempted approaches and results, protected claims/functions that cannot be sacrificed, why the worker is stuck, and the narrow question or raw author input needed from Joel.

An API-call or section budget may pause paid calls for explicit escalation, but it cannot convert the best-so-far candidate into an accepted result or close the task. The worker must state whether a known faithful next repair remains.

## Scope and safeguards

This is Joel's standing detector-acceptance target for requested Pangram-humanization work. Editorial quality, semantic sanity, fidelity, provenance, and protected rhetorical function remain independent required gates. A 100% Human result with semantic or editorial regression still fails. Detector repair may not weaken Joel's argument, invent lived material, drop evidence, or accept worse prose merely to reach the number.

Section-level measurements are diagnostic unless a section is itself the intended delivery. The final exact delivery boundary must independently satisfy the 100% criterion after every accepted edit.

