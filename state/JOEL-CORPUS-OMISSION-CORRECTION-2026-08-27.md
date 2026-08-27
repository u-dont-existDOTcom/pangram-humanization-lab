# Joel corpus omission correction — 2026-08-27

## Status

Durable workflow correction from live Joel-byline humanization work.

## What went wrong

During the Somatic Therapies Introduction humanization and subsequent held-out generation probes, the worker loaded repository governance, detector lessons, voice rules, and some article state, but did not load and actively condition generation on the relevant labeled natural-owner corpus before producing fresh Joel-byline prose.

The resulting process effectively attempted zero-shot or rules-only imitation of Joel's voice. Multiple fresh passages remained Pangram AI / low confidence even after surface lessons such as reduced overcompletion, ordinary wording, less hedging, stronger opinions, and avoidance of architectural/mechanical language were applied.

## Existing authority already covered this

This is not a new conceptual policy. `u-dont-existDOTcom/joel-articles/project-sources/VOICE-REFERENCE.md` explicitly identifies genre-specific owner-authored calibration sources, including `cancer-and-research-samples.txt` for research-conversational prose. `IDIOLECT-PRESERVATION-PROTOCOL.md` likewise directs production work to reuse good natural owner prose and preserve owner thought route, under-specification, and stopping points.

The failure was execution: abstract rules derived from the corpus were used in place of the corpus itself.

## Corrected production rule

For actual Joel-byline generation, reconstruction, or humanization that requires fresh prose:

1. Load the relevant genre/register slice of the labeled natural-owner corpus before drafting.
2. Use abstract voice rules as guardrails, not as a substitute for corpus conditioning.
3. Prefer actual owner sentence/thought patterns, ordinary lexical choices, connective habits, under-specification, and stopping behavior evidenced in the corpus; do not merely sprinkle catchphrases or copy surface tics.
4. Keep production and zero-shot research distinct. A deliberately corpus-blind probe may be useful for model research, but it must be labeled as such and must not silently replace the corpus-grounded production workflow.
5. If a corpus-grounded fresh generation still fails, compare it with a matched owner Human realization and extract bounded lessons; do not conclude from corpus-blind failures that the corpus cannot help.

## Evidence from the live sequence

- Multiple corpus-blind fresh attempts on trauma and unrelated AstroHD-inspired topics returned Pangram AI / low confidence.
- One owner rewrite of a grounding paragraph returned Human / low confidence.
- On that fixed Human boundary, changing `relaxes your body` to the more vivid `makes your body unclench` flipped the result back to AI, supporting the broader concern that model optimization pressure can appear in very small lexical realizations.

Do not treat that lexical pair as a universal phrase ban; it is boundary-local evidence.
