# T01 specialized audit v1 — fresh held-out result

Date: 2026-09-24
Status: **SCOPED SPECIALIZED-AUDIT DEVELOPMENT RESULT / NO PANGRAM CALLS**

## Why this exists

The compact V2.1 global ledger improved T10 and T11 behavior but over-flagged a fresh source-earned T01 case. This crossed the local same-method refinement threshold for T01.

Instead of adding another exception to the global prompt, T01 was moved into a one-axis audit.

## Calibrated distinction

The narrow auditor compares the depersonalized sentence against the original at the level of:
- proposition;
- speech act;
- epistemic force;
- practical force.

A situated or provisional first-person judgment is not fake-personal merely because its proposition can be rewritten without `I`.

## Fresh held-out cases

### Positive

Target:
> The test I care about is whether I slowly need the helper less. If we disagree, I want to be able to stay on my own ground and make a sane decision without needing them to certify that I'm doing adulthood correctly.

Expected: **PRESENT**

Basis: direct Episode-007 owner correction says first-person wants/cares should not stage a general helper/therapy criterion when the criterion can be stated directly.

Claude Opus 5.5 CLI high:
- **PRESENT**
- rationale: depersonalization preserves the criterion, certainty, and practical force.

### Negative

Target:
> I don't want the adult to arrive, grab the pencil out of his hand because he wrote something embarrassing, and replace him with a more acceptable version of himself.

Expected: **ABSENT**

Basis: owner-cognition-assisted prose. The first person expresses the author's actual self-relating intention inside his inner-child metaphor; depersonalizing it would convert a personal motive/intention into a general rule.

Claude Opus 5.5 CLI high:
- **ABSENT**
- rationale: depersonalization changes the speech act from personal intention to universal prescription.

## Result

**2/2 exact fresh held-out transfer.**

This is enough to justify the architecture change from repeated global-prompt patching to a scoped T01 specialized audit. It is not a universal accuracy estimate and does not make T01 model output owner authority.

Current use:
- when the full ledger marks T01 PRESENT/UNCERTAIN, or direct editorial review disputes T01, run the specialized audit;
- treat its output as calibrated scoped evidence;
- direct owner/editorial judgment still controls conflicts.

No Pangram calls were used.
