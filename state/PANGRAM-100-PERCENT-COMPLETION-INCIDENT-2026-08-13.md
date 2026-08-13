# Pangram 100% Human completion-gate incident — 2026-08-13

## Status

Promoted owner correction.

## Observed failure

Joel reported that a requested humanization pass stopped at 93% Human. He requires the pass to continue until the exact intended delivery boundary measures 100% Human, unless the worker genuinely does not know a further faithful and coherent repair. At that point the worker must identify the exact unresolved passage and ask Joel for the narrow authorial help needed. A partial score is not a completed delivery.

## Root cause

The canonical instructions required prose to meet “the required Pangram criterion” and described some measured candidates as `detector-green`, but did not define Joel's standing acceptance criterion in detector fields. The operational runbook required `STAGE_SUCCESS` and detector version `4.0` without checking the Human/AI fractions. Pangram can therefore return a successful result and a Human headline while still assigning less than 100% of the measured boundary to Human.

The missing definition allowed 93% Human to be treated as terminal progress instead of an unresolved detector result.

## Promoted rule

Whenever Joel asks to humanize text, make it pass Pangram, or otherwise makes Pangram success a delivery requirement, this gate applies. Completion requires the exact intended delivery boundary to return all of the following from Pangram 4:

- `detector.stage == "STAGE_SUCCESS"`;
- `detector.version == "4.0"`;
- `detector.fraction_human == 1.0`;
- `detector.fraction_ai == 0.0`; and
- `detector.fraction_ai_assisted == 0.0`.

A `Human` headline, `prediction_short == "Human"`, or partial result such as 93% or 99% Human is progress only. It is not a pass and must not be reported as complete.

Section/window measurements are diagnostic unless that unit is the complete requested deliverable. For a full article, the complete exact article boundary must itself satisfy the gate after every accepted edit; section-level 100% results do not aggregate into an article pass.

The repair task has only two terminal states: (1) the exact intended delivery boundary satisfies the 100% detector gate and all editorial/fidelity gates; or (2) the worker genuinely knows no further faithful and coherent repair and makes an unresolved authorial handoff. While a known faithful and coherent repair remains, continue the task.

The unresolved authorial handoff must report the exact failing span and measured boundary; exact `text_sha256`; `fraction_human`, `fraction_ai`, and `fraction_ai_assisted`; detector version; result path; result commit; attempted faithful approaches and their measured results; protected claims/functions that cannot be sacrificed; why no further faithful repair is known; and the narrow question or raw author input needed from Joel.

A spending limit may change batching or trigger internal coordination, but while a known faithful repair remains it cannot end the task, create an authorial handoff, or make Joel supply prose. Any operational suspension remains an open blocker, not a delivery.

## Scope and safeguards

This is Joel's standing detector-acceptance target for humanization work. Editorial quality, semantic sanity, fidelity, provenance, and protected rhetorical function remain independent required gates. A 100% Human result with semantic, rhetorical, editorial, fidelity, or provenance loss also fails the gate. Detector repair may not weaken Joel's argument, invent lived material, drop evidence, or accept worse prose merely to reach the number.

