# Historical Pangram whitespace audit — 2026-08-12

Purpose: re-evaluate previously promoted detector/humanization lessons after the oxytocin case demonstrated that one accidental ASCII space can cause a reproducible Pangram-4 classification flip.

## Status classes

- **SURVIVES NORMALIZATION**: the substantive detector finding remains after removing the identified anomalous whitespace.
- **QUANTITATIVELY SENSITIVE**: classification family survives, but score changes enough that exact numerical claims should be tied to the literal input.
- **CONFOUNDED**: the apparent endpoint/classification depends materially on anomalous whitespace.
- **NO ANOMALOUS HORIZONTAL WHITESPACE FOUND**: archived exact detector inputs contain ordinary single horizontal spacing, so no horizontal-whitespace retest is required.
- **OLD-MODEL LIMIT**: source discovery was on Pangram 3.3.2 and current API retest is Pangram 4.0; current normalization evidence cannot retroactively isolate the old model.

## Completed checks

### Oxytocin owner endpoint — CONFOUNDED

Normalized visible owner rewrite with a single space after `if`:
- Mixed, AI 0.4439140856266022 / Human 0.5560859441757202
- independent repeat reproduced the same result

Exact owner-pasted version with `if  people`:
- Human, AI 0.0 / Human 1.0, high confidence
- independent repeat again Human 0.0 AI

Conclusion: the visible three-part owner rewrite materially improved the detector boundary, but the final 100% Human endpoint was caused by a reproducible whitespace artifact. Never use the green endpoint as proof of a prose-only effect.

### Love-definition open-list topology — SURVIVES NORMALIZATION

Current-v4 normalized retest:
- closed list: 100% AI
- `and so forth`: 100% Human
- `etc.`: 100% Human

Conclusion: the local openness/topology lesson survives and is not an accidental whitespace artifact.

### Nibbāna r15 X11 owner endpoint (`books ,`) — SURVIVES NORMALIZATION + OLD-MODEL LIMIT

Current-v4 retest:
- malformed `books ,`: 100% Human
- normalized `books,`: 100% Human

Conclusion: current-v4 green status survives normalization. Historical Pangram-3 discovery remains an old-model result, but there is no evidence here that the stray pre-comma space created the endpoint.

### Nibbāna r16 X111 (`books ,`) — QUANTITATIVELY SENSITIVE + OLD-MODEL LIMIT

Current-v4 retest:
- malformed: Mixed, AI 0.2250700891
- normalized: Mixed, AI 0.1939102560

Conclusion: no qualitative flip; normalization actually moves slightly toward Human. Do not attribute the historical staged-repair effect to this whitespace. Exact old Pangram-3 whitespace causality is not recoverable from a Pangram-4 retest.

### Different Levels owner-final r23 — QUANTITATIVELY SENSITIVE

The archived owner source explicitly contains a trailing heading space and `Is the  one playing the client...`.

Current-v4 complete-section retest:
- exact: Mixed, AI 0.16474543511867523 / Human 0.8352545499801636
- normalized: Mixed, AI 0.19553206861019135 / Human 0.8044679164886475

The exact value reproduces the previously recorded r26 owner-endpoint AI fraction. The anomalous whitespace makes the exact input somewhat more Human-scored, but does not create the qualitative result.

### Romance matched-clause 2×2 — NO ANOMALOUS HORIZONTAL WHITESPACE FOUND

The archived exact submitted texts for A0B0, A0B1, A1B0, A1B1, and the Human endpoint use ordinary single horizontal spaces. Their paragraph blank lines are normal formatting and Pangram returns paragraph-newline normalization. No `word  word`, tab, NBSP, pre-punctuation space, or comparable anomaly appears in the tested clause boundary.

Conclusion: no horizontal-whitespace retest is required for the matched-clause interaction. Preserve the existing interaction finding.

## Historical claims requiring wording correction

1. `whitespace-only normalization difference` must never again be treated as equivalent to `detector-irrelevant difference`.
2. Any old exact numerical result with anomalous whitespace is valid only for that literal submitted text until a normalized pair is tested.
3. Owner-reported `all green` prose containing an accidental spacing error is not a stable detector endpoint until normalized and retested.
4. Detector green remains separate from natural authorship and editorial quality.

## Remaining queue

Recheck older owner-final detector controls only when the exact tested source can be recovered. Prioritize any source with documented double spaces, pre-punctuation spaces, tabs/NBSP, or trailing horizontal spaces. Do not reconstruct unavailable exact detector inputs from memory and call the reconstruction historical evidence.

The File Library/source-side audit should specifically revisit owner-final sections whose ledgers preserve literal whitespace anomalies (including the known Romance corpus examples) and the r27 owner-calibration frozen probes if their exact submitted files become available.

## Evidence files

- `state/PANGRAM-WHITESPACE-SENSITIVITY-2026-08-12.md`
- `state/experiments/romance-oxytocin-c-2026-08-12-results.json`
- `state/experiments/historical-whitespace-audit-r1-2026-08-12-results.json`
- `state/experiments/historical-whitespace-audit-r2-2026-08-12-results.json`
- archived matched-clause cache records under `cache/pangram-4/4.0/`
