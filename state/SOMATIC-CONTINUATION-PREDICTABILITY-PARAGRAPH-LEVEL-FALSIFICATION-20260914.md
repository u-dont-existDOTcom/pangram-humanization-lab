# Somatic continuation-predictability — paragraph-level falsification — 2026-09-14

Status: **OWNER-REPORTED DETECTOR EVIDENCE / MODEL-CORRECTION / NO NEW DETECTOR CALL**

Joel clarified that his manually humanized Somatic article did not merely score Human as a whole: **every individual paragraph was Human in Pangram**.

This is a stronger local test of the continuation-predictability / editorial-inevitability hypothesis than the earlier article-wide comparison.

## Result

The current transition model does **not** predict that fact paragraph-by-paragraph.

Several individual paragraphs in the manual positive control contain structures that the current local representation would plausibly flag as editorial-inevitability risk, including compact scope/qualification/safety/aftercare sequences, balanced contrast structures, and research/recommendation/conclusion progressions. Under Joel's report, those paragraphs nevertheless classify Human individually.

Therefore the stronger claim is falsified:

`paragraph is Pangram-Human <=> paragraph lacks local editorial-inevitability structure`

and so is any equivalent claim that a local transition-route score alone is sufficient to predict Pangram paragraph classification.

## What survives

Continuation structure may still be a useful **diagnostic feature of model-shaped prose**, especially when the same routing grammar recurs across model-written material. It is not established as a paragraph-level Pangram classifier.

The driver labels (`source`, `judgment`, `causal necessity`, `generic discourse`) are also too interpretive to rescue the prediction post hoc. If a paragraph that contains a tidy sequence is labeled `author judgment` only because it is already known to be owner-written/Human, the model becomes circular rather than predictive.

## Required distinction

Keep separate:

1. **editorial diagnosis:** does this paragraph exhibit a model-frequent continuation shape?
2. **Pangram prediction:** would Pangram classify this exact paragraph Human or AI?
3. **generation guidance:** does changing the continuation route improve model generation?

Evidence for (1) does not establish (2) or (3).

## Validation requirement

A real local prediction test would require a predeclared paragraph-level scoring rule and a genuinely label-blind evaluation set containing both Human and AI paragraphs. Same-context recoding after the labels are known is not independent validation.

Until such a test exists, treat editorial inevitability / route recurrence as an explanatory and drafting diagnostic, not a detector surrogate.
