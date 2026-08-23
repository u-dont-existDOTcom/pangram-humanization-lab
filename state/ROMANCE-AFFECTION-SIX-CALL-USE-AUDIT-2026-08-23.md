# Romance Affection six-call use audit — 2026-08-23

Status: retrospective detector-process audit. Article authority is unchanged. Human editorial quality, preservation, and owner authority outrank detector score.

## Exact paid sequence

All six calls were charged under `part1-affection-simmer` / Pangram 4.0.

1. `AFFECTION_SIMMER_BASELINE`
   - experiment: `romance-detector-repair-20260820-part1-natural-sections-r1-20260821`
   - SHA-256: `1e2d12bae4685093585663f899c96e49a51ed4dfe3889c31a16a80a95133c11c`
   - 259 words
   - Human `0.0`; AI `1.0`
   - exact full natural-section baseline. Necessary and high-value.

2. `AFFECTION_SIMMER_R2B`
   - experiment: `romance-detector-repair-20260820-part1-natural-sections-r2b-20260821`
   - SHA-256: `636a4312a9427981f619a3f8793f1fcc980f68ab35299a31487659aa9fe29dd1`
   - 229 words
   - Human `0.21385541558265686`; AI `0.7861445546150208`
   - broad multi-variable rewrite into more first-person/situated syntax; first 54 words Human, remaining 175 AI. Some localization value, weak causal isolation.

3. `AFFECTION_SIMMER_R2C`
   - experiment: `romance-detector-repair-20260820-part1-aff-r2c-20260821`
   - SHA-256: `636a4312a9427981f619a3f8793f1fcc980f68ab35299a31487659aa9fe29dd1`
   - 229 words
   - Human `0.21385541558265686`; AI `0.7861445546150208`
   - byte-identical to call 2 and returned the same fractions. The spec contains no explicit repeat/reproducibility designation. It counted as a new paid call with `cache_hits: 0`. Under the current duplicate-defense contract an already-completed same model/version/text result should normally be reused. Treat this historical call as low-value/waste unless independent evidence establishes that a paid exact repeat was deliberately authorized as a reproducibility test.

4. `AFFECTION_SIMMER_R3`
   - experiment: `romance-detector-repair-20260820-part1-affection-r3-20260821`
   - SHA-256: `66349071b2f77696ffd24669da14e3a4f9d2eb2d4b49904182ecacf3a145f5f7`
   - 268 words
   - Human `0.19545766711235046`; AI `0.8045423030853271`
   - another broad rewrite using first-person, questions, and more conversational realization. Again first 54 words Human and the remaining 214 AI. It falsified the simple idea that conversational first-person alone would solve the section, but changed too many variables at once for strong causal inference.

5. `AFFECTION_R4B`
   - experiment: `romance-detector-repair-20260820-part1-residuals-r2b-20260821`
   - SHA-256: `28bc7c5eb0d12a508d67dbab64855bfdf46b1e11db1528c9a4c50ec96f2036a2`
   - 132 words
   - Human `0.3731931746006012`; AI `0.6268068552017212`
   - aggressive compression/residual probe. First 54 words Human, remaining 78 AI. Useful localization evidence, but it omitted/consolidated multiple full-section functions and therefore was not a preservation-valid article replacement.

6. `AFFECTION_TRANSITION_R6`
   - experiment: `romance-detector-repair-20260820-part1-affection-transition-r6-20260821`
   - SHA-256: `f1798598a2ab68535f63261296e590f584b6afc337af9b862052b85070faea18`
   - 274 words
   - Human `1.0`; AI `0.0`, High confidence
   - boundary probe consisting of the Toft opening plus one short Anami/simmer sentence followed immediately by the Casual heading/opening. It was highly informative evidence that detector classification was context/boundary-sensitive. It was not a full Affection realization: barometer, self-responsibility, protected erotic-time/priority, and other Affection functions were absent. The ledger nevertheless treated this as the sixth Affection call and `first_human_measurement_key`, exhausting the local 6/6 cap.

## Retrospective assessment

The six calls were not used efficiently as an article-repair budget.

- Call 1 was necessary.
- Calls 2 and 4 (R3) were broad paraphrase attempts rather than high-information controlled contrasts; they changed many variables while retaining the same balanced/counseling architecture.
- Call 3 was byte-identical to call 2 and has no durable explicit rationale as a paid repeat; this is the clearest wasted slot.
- Call 5 was useful as diagnostic localization but should not be confused with a preservation-valid replacement.
- Call 6 was the most informative experiment after baseline because it exposed context/boundary sensitivity, but it was a transition-boundary probe rather than a full-section repair. Counting it as the successful sixth natural-section measurement made the cap semantically misleading.

The sequence did not directly test the higher-level discourse-stance hypothesis later raised by Joel: polished balanced/therapeutic/explainer voice versus situated, committed, opinionated prose. Calls 2–5 mostly varied realization inside the same underlying balanced relationship-advice architecture.

## Process implication

For future capped section audits:

1. baseline first;
2. formulate one or two causal hypotheses from the actual window/voice structure before rewriting;
3. prefer one-variable/minimum-dose or explicit factorial contrasts over repeated broad paraphrases;
4. exact same model/version/text SHA should be cache-reused unless an explicitly authorized reproducibility repeat is recorded as such;
5. diagnostic compressed/transition boundaries must be labeled separately from preservation-valid section candidates and should not be allowed to masquerade as a successful complete-section repair merely because they share a section budget identifier;
6. reserve at least one slot for a preservation-valid final candidate rather than exhausting the cap on diagnostics.

This audit does not itself reopen the exhausted Affection cap or authorize a seventh call.