# Romance short-boundary confidence lesson — 2026-08-21

Status: **owner operational rule + article-specific detector evidence**. Do not generalize this into a universal Pangram word-count threshold.

## Owner-reported evidence

Joel supplied a 97-word natural-owner Romance passage beginning `When did you two last dance?` and reports that Pangram 4 classified it **Human / low confidence**. A preceding assistant rewrite of roughly the same local function also classified Human / low confidence.

Joel explicitly chose the natural-owner passage because it is his actual writing and instructed that future detector checks should use **at least 2× this amount of text** to improve detection accuracy.

Operationally, for comparable Romance diagnostic work, default to approximately **200+ words of contiguous reader-visible context** around a target span unless the actual intended deliverable itself is shorter. Prefer natural section/context boundaries over mechanically padding to a number.

## Interpretation

This supplements the existing rule that short passages are less reliable detector evidence. It is not evidence that 200 words is a universal Pangram threshold, nor that a low-confidence Human result indicates poor prose. The practical problem is that very short boundaries can leave the detector with too little discourse structure, rhythm, provenance, and surrounding context to classify confidently.

When a short natural-owner passage is already editorially sound, do not keep rewriting it merely to increase Pangram confidence. Widen the diagnostic boundary first.

## Related Romance evidence

The same repair sequence produced a near-minimal owner-reported MEDIUM→HIGH confidence pair in the exclusivity passage by adding only `have you ever looked?` to the opening. Preserve that as local evidence that pragmatic/social discourse function can matter to Pangram, but do not infer a rhetorical-question token rule.
