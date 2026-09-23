# Global tell-ledger calibration coverage — 2026-09-23

Status: PROJECT-SPECIFIC CALIBRATION MAP / NO NEW MODEL CALLS / NO PANGRAM CALLS

## Parent outcome

The production goal is not hidden-authorship classification. It is reliable application of the full current AI-tell ledger to literal prose before Pangram.

The max-effort benchmark showed that Claude Opus 5.5 can execute the current ledger very well on the **cells that already have owner/editorially grounded labels**: 11/12 exact with zero wrong-polarity calls.

Before changing definitions, determine which tell IDs actually have two-sided calibration evidence.

## Current scored coverage

| Tell | Current meaning | Known PRESENT controls | Known ABSENT controls | Coverage state |
|---|---|---|---|---|
| T01 | fake personal stake / irrelevant first-person authority | none in current scored benchmark | none | **UNSCORED** |
| T02 | cumulative instruction-manual / compressed-listicle cadence | readiness; dangerous-adult | 5-MeO open hypothesis list; owner Human direct-advice paragraph; owner Human seat-belt paragraph | **TWO-SIDED / STRONGEST CURRENT** |
| T03 | abrupt complication without reader-visible setup | dangerous-adult | none | **POSITIVE-ONLY** |
| T04 | scene-skinned semantic staircase | RT2 | none | **POSITIVE-ONLY** |
| T05 | synthetic/didactic prop continuity | RT2 | none | **POSITIVE-ONLY** |
| T06 | generic therapeutic abstraction | RT2 | none | **POSITIVE-ONLY** |
| T07 | simulated spontaneity / filler as transition camouflage | RT2 | none | **POSITIVE-ONLY** |
| T08 | concrete image -> explanatory aftercare / overcompletion | RT2 | none | **POSITIVE-ONLY** |
| T09 | equalized / optimal semantic efficiency | RT2 | none | **POSITIVE-ONLY** |
| T10 | generic therapeutic permission syntax | none in current scored benchmark | none | **UNSCORED** |
| T11 | generic bridge / connective tissue | none in current scored benchmark | none | **UNSCORED** |
| T12 | symmetry / balanced contrast / tidy taxonomy | none in current scored benchmark | none | **UNSCORED** |

## Existing evidence that can seed the missing controls

### T01

The tell library and `OWNER-CORRECTION-FIRST-PERSON-PREFERENCE-PERMISSION-REGISTER-20260916.md` already contain direct owner-rejected fake-personal forms such as `I want ...`. These are candidate PRESENT controls.

A negative control still needs a source-earned first-person passage where Joel's actual judgment materially changes the argument/action. HT05 provides the distinction, but a literal owner-labeled excerpt should be frozen before scoring.

### T03

Dangerous-adult supplies a direct owner-grounded PRESENT control.

A negative control should preserve a superficially abrupt turn whose necessity is visible from prior context, so the audit learns "unexpected" is not automatically "unprepared." Do not invent the label from model output.

### T04–T09

RT2 supplies one owner-grounded positive cluster containing all six tells.

That is useful but dangerous: one passage cannot establish that the six tell definitions discriminate independently. Each tell needs at least one negative/counterexample where neighboring RT2-like surface features are present without that operation.

Prefer owner-authored / owner-final controls:
- real concrete image with no source-function staircase;
- causally load-bearing props;
- specific emotional relation rather than generic therapeutic abstraction;
- genuine colloquial/self-talk that is not transition camouflage;
- a concrete image whose following sentence adds new information rather than explanatory aftercare;
- concise Human prose with genuinely unequal attention despite high local efficiency.

### T10

The retrospective checking ledger already records generic `You don't have to X before Y` permission syntax as a negative diagnostic candidate. Freeze the exact rejected realization plus a source-earned owner permission/allowance counterexample before scoring.

### T11

The tell library says Romance reciprocity already supplied controlled counterexample evidence: deleting a **necessary temporal bridge** hurt coherence while generic explanatory linkage was removable. This is the best next tell to promote into explicit two-sided scored controls because the evidence already exists.

### T12

No current scored owner-grounded cell. Find one direct owner-rejected balanced/tidy taxonomy and one owner-authored genuine enumeration/necessary contrast before asking a model to clear this tell.

## Decision

Do **not** rewrite the tell catalog wholesale.

The evidence currently supports a different next step:

1. preserve the current tell wording;
2. build two-sided owner/editorial controls tell-by-tell;
3. start with T11, T01, and T10 because existing owner-correction records already point to literal examples;
4. separate the RT2 cluster into independent T04–T09 controls rather than treating one red paragraph as six fully calibrated tells;
5. only revise a definition if repeated Opus-xhigh errors remain after good positive/negative controls exist for that exact tell; use max only as a decision-changing escalation before blaming the definition.

## Model-routing consequence

Current bounded evidence:
- Opus 5.5 **xhigh**: preferred high-rigor global sweep; two runs scored 11/12 and 10/12 with zero wrong-polarity calls at roughly one-sixth the cost of max;
- Opus 5.5 max: escalation only when xhigh leaves a decision-changing tell unresolved or editorially disputed;
- Sol/Astra max: cheaper/free-credit Venice alternatives but still produce wrong-polarity calls;
- Jev: optional cheap positive triage only; ABSENT cannot clear a tell.

No further paid Opus call is justified until the next batch adds genuinely new tell-level calibration coverage.
