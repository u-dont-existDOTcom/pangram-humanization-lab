# Working humanization lessons supplement — idiolect preservation — 2026-08-17

Read after the 2026-08-15 supplement. Direct Joel owner correction and exact project authority still control conflicts.

Source integration: `state/IDIOLECT-ERASURE-PAPER-INTEGRATION-2026-08-17.md`.

Operational research protocol: `docs/IDIOLECT-PRESERVATION-PROTOCOL.md`.

## 1. Humanization must preserve the author, not merely remove AI shape

Semantic fidelity and detector passing do not prove that a rewrite still carries the author's distinguishable writing signal.

For named-byline work, treat idiolect retention as a separate objective. A candidate can preserve propositions and still normalize the author's recurring choices of phrasing, function words, punctuation, rhythm, and deeper stylistic representation.

This does not authorize stylometric cosplay. Preserve real owner material rather than manufacturing quirks.

## 2. Minimize rewrite dose

AI rewriting should be dose-conscious.

Prefer P1 or the smallest bounded repair that fixes the diagnosed problem. Use an architecture-level reconstruction when the inherited thought architecture is genuinely wrong, but do not escalate to broad professionalization merely because a model can make the passage smoother.

The IER study found materially greater erasure under heavy rewriting than under light grammar correction. Treat `heavy-polish` as a useful adverse control, not the default humanization move.

## 3. "Preserve voice" in the prompt is not evidence

An instruction telling a model to preserve voice is only an intervention label.

The IER study found that explicit voice-preservation prompting still left most deep recoverable authorship signal erased. Therefore the lab must inspect or measure the resulting candidate rather than infer preservation from the prompt.

This aligns with existing project practice: prompt intent never outranks literal output.

## 4. Style-sensitive attribution needs topic controls

A model can appear to recognize an author because it recognizes the author's subject matter.

When the lab adds computational idiolect testing:

- use style-sensitive attribution, not semantic similarity alone;
- include topic-matched human negatives where feasible;
- include function-word/content-light checks;
- use a semantic encoder only as a confound monitor;
- separate train/test by source/document to prevent leakage.

A topic-driven classifier is not a Joel-voice gate.

## 5. Keep the natural-owner profile uncontaminated

Do not train the primary Joel reference profile on a mixture that silently includes assistant-written prose.

Natural owner-authored/owner-final writing, assistant-produced owner-accepted prose, detector-targeted owner edits, and synthetic probes are different provenance classes. Keep them separable so the experiment does not teach the detector that prior AI mediation is Joel's native idiolect.

Register differences must also remain visible.

## 6. Reserve the term IER for the real experiment

IER is the corpus-level drop in held-out attribution accuracy under a specified rewrite condition and attributer.

Do not label a single passage's LUAR similarity, classifier probability, embedding distance, or before/after score "IER." Use `idiolect-retention diagnostic` or another accurate local term.

## 7. Pangram green plus idiolect loss is not a byline success

Pangram and authorship attribution answer different questions.

When a calibrated idiolect layer exists, a Pangram-green candidate that materially degrades Joel attribution remains a failed Joel-byline candidate unless Joel explicitly prioritizes anonymity/privacy over voice preservation.

Until quantitative calibration succeeds, apply this qualitatively through minimum-edit, owner-provenance, architecture, and cold-audit safeguards.

The paper's `double erasure` has a narrower experimental definition. Use `double-erasure-like byline failure` for the local pattern unless both components have actually been measured under a comparable protocol.

## Quantitative status

No Joel-specific IER threshold or scoring gate is established by this integration.

Before quantitative use, the lab must validate natural-owner provenance, held-out source splits, above-chance baseline attribution, topic/content-light controls, register effects, and stability. See the protocol for the rollout sequence.
