# Explanatory development: held-out predictions and controlled Pangram checks

## Result in brief

The explicit thought-development interpretation was not yet a strong predictor. Frozen forecasts matched 11 of 15 previously uninspected exact 4.1 inputs; always predicting Human would match 10. Eight subsequent one-paragraph API submissions tested two source families. Both unchanged Mixed controls reproduced. Expanded and repetitive endings all remained Mixed. A direct rewrite retaining the happiness passage’s explicit criteria returned all-Human segments, with Low confidence on its revised ending. The corresponding institution/credentials rewrite remained Mixed.

This is evidence against these particular attempts at explanatory unpacking, not against all useful elaboration. The expanded versions repeatedly restated distinctions; whether they genuinely instantiate the owner’s proposed sideways, reader-responsive explanation remains an unresolved operationalization question. No general humanization recipe is validated.

## Boundaries and provenance

- Source snapshot: joel-articles dc929e66beb4b06cbc8b80d5be7eec7cd967c89f. Lab base: f73e5fa91bec4522f9ce19d89edc883f48941460.
- The intended separate two-arm evaluator did not run. The executed diagnostic used the current Chat model, with exact selected labels hidden until all forecasts were saved. Earlier archive familiarity remains; this is not an independent model comparison or a globally pristine holdout.
- Fifteen distinct source-lineage/near-duplicate groups, one text from each. Selection aimed for up to ten per class and yielded ten Human and five non-Human cases. This is a selected diagnostic sample, not natural prevalence.
- Primary observed label: every returned segment Human versus any non-Human segment. This is a detector-outcome target, not authorship truth.
- All new submissions were one paragraph, 61–94 whitespace-delimited words, with explicit forecasts and hypotheses before submission. No long sections or whole articles were submitted.
- Exactly eight accepted POSTs, 644 submitted words in total, including two deliberately repeated unchanged controls. No ambiguous POSTs, automatic resubmissions, or article changes. Currency cost was not inferred.
- The exact API model request was pangram-4; every returned version was 4.1. Returned input, input hashes, terminal status, and complete window-text coverage were checked.
- The source material is writing-analysis data; inclusion is not endorsement or fact-checking of its therapeutic, religious, or scientific assertions.

## Frozen forecast diagnostic

Accuracy: 11/15 (73.3%). Human recall 7/10; non-Human recall 4/5. Balanced accuracy 75.0%. Brier score 0.1981, compared with 0.2500 for constant 0.5 and 0.2222 for the sample class-rate constant. No statistical superiority or transfer to other authors is established.

| ID | Forecast P(all Human) | Recorded outcome | Correct? |
|---|---:|---|---|
| T01 | 0.78 | Human | yes |
| T02 | 0.25 | NotHuman | yes |
| T03 | 0.30 | Human | no |
| T04 | 0.42 | NotHuman | yes |
| T05 | 0.60 | Human | yes |
| T06 | 0.67 | NotHuman | no |
| T07 | 0.64 | Human | yes |
| T08 | 0.66 | Human | yes |
| T09 | 0.34 | NotHuman | yes |
| T10 | 0.64 | Human | yes |
| T11 | 0.38 | Human | no |
| T12 | 0.62 | Human | yes |
| T13 | 0.30 | NotHuman | yes |
| T14 | 0.77 | Human | yes |
| T15 | 0.35 | Human | no |

Three of the four misses were Human texts judged too likely to be non-Human. Lists, abstractions, metaphors, and packaged teaching are therefore not sufficient vetoes. The fourth miss was a Mixed passage whose final institutional-credentials coda was flagged, while its concrete maze imagery remained Human. These are post-result observations, not retroactively corrected forecasts.

## Controlled API outcomes

`fraction_ai` below is the API’s recorded document field, not a probability of actual authorship. Altered length and segmentation limit direct comparisons of these fractions. The categorical results and exact unchanged-substring label changes are reported separately.

| Family | Variant | Words | Outcome | Recorded fraction_ai |
|---|---|---:|---|---:|
| T04 | Unchanged original | 66 | Mixed | 0.400465161 |
| T04 | Expanded explanation | 77 | Mixed | 0.711362779 |
| T04 | Lengthened repetition | 80 | Mixed | 0.725144804 |
| T06 | Unchanged original | 81 | Mixed | 0.241536468 |
| T06 | Expanded explanation | 93 | Mixed | 0.461512834 |
| T06 | Lengthened repetition | 94 | Mixed | 0.573495805 |
| T04 | Direct wording; criteria explicit | 61 | All segments Human | 0.000000753 |
| T06 | Direct wording; criteria explicit | 92 | Mixed | 0.462204874 |

## What changed—and what can be inferred

### Expanded explanations did not reproduce the intended benefit

The six-cell experiment kept each prefix exact and changed only the final inference. The expanded endings made duties, misery, institutional authority, truth, and safety more separately explicit. The repetition controls increased length without that intended development. Neither expanded version passed, and both caused exact unchanged earlier text to become AI-labeled. The narrow predeclared expectation failed. We should not rename this a success because one numerical score was slightly less unfavorable than the repetition control.

### A direct same-criteria rewrite worked in one passage

Original ending:

> I’d still take real suffering seriously, and do what you owe the people around you, but skip the part where you have to be miserable too.

New ending:

> Take real suffering seriously, and do what you owe the people around you. You don’t have to make yourself miserable too.

The prefix was unchanged. Taking suffering seriously, meeting obligations, and not requiring one’s own misery remained explicit. The complete input returned Human Written, with every segment Human; the revised ending was Low confidence. The tiny nonzero fraction_ai was 0.000000753, so this is an all-Human-label result, not mathematical zero or proof of robust dark-green status. The edit changed stance framing, sentence division, and phrasing together. It does not isolate which change mattered.

### The apparently analogous repair did not generalize

An archived Human repair of the credentials passage used the single judgment “I wouldn’t trust a model more just because there’s a big institute behind it handing out certificates.” That compresses the original separate truth and personal-safety criteria into trust. In the new follow-up, retaining that judgment while explicitly restoring both criteria still produced Mixed. The old successful rewrite is therefore not clean evidence that an equivalent wording operation solves the fully explicit source meaning.

### Labels changed on words that did not change

In the happiness family, this exact sentence was Human in the reproduced original and AI-labeled after either expanded ending:

> That might not be how it goes for everyone, and it doesn’t mean unhappy people can’t help.

In the credentials family, “Others seem to leave people more split up than when they started.” also changed from Human to AI after ending-only edits. These observations demonstrate contextual segment classification at these boundaries. They do not prove that those unchanged sentences are the cause of the failing result, or that their authorship changed.

## Learning disposition and next decision

The current explanation is a candidate interpretation, not an operative predictor. The failed variants must remain in the learning set beside the single success. Before further paid generation, the unresolved issue is specifying what productive explanation does for the reader, as distinct from repeating a qualification in several sentences. The next useful semantic comparison is between the owner’s actual aligned rewrites and these failed unpacking attempts, preserving any changes to scope, stance, or criteria rather than treating them as stylistic noise. No additional unguided variants are authorized by this report.

The 8-call experiment is closed with its failures preserved. This does not claim the overall Pangram interpretability question is solved. The continuation boundary is the absence of a sufficiently supported further repair hypothesis after the registered comparisons—not exhausted API permission.

## Reproduction and supporting files

Run `python3 verify.py` in this directory. It validates the frozen forecast hash, recomputes diagnostic scores, checks the eight exact inputs against raw responses, confirms their one-paragraph boundaries, and validates the manifest. It performs no network calls and reads no credential.

- RESULT.json: complete selected inputs, original predictions, historical outcomes, new API responses, and local dispositions.
- INPUTS.json: every new exact submitted passage.
- API-EXPERIMENT.json and FOLLOWUP-SPEC.frozen.json: hypotheses and predictions saved before their respective submissions.
- v2-predictions.frozen.json and PROTOCOL-v2.json: the executed single-arm forecast study.
- MANIFEST.json: SHA-256 checksums, excluding itself.
- RESULTS.html: readable text and measured segment highlighting. Green/orange indicates the detector’s labels, not verified human/AI authorship.
