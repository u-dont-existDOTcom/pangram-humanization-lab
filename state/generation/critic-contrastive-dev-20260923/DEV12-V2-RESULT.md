# Contrastive critic development v2 — GPT-6 Sol dev12 result

Date: 2026-09-23
Status: DEVELOPMENT DATA / PROMISING CONTRASTIVE METHOD / NOT PRODUCTION-CALIBRATED / NO PANGRAM CALLS

## Configuration

- model requested and returned: `openai-gpt-6-sol`
- provider: Venice through authenticated UDA gateway
- prompt SHA-256: `6c418eac5ee443d467f602d183232cc0dbc0c3a2ad5bcec16eb1026e6fd54790`
- blind dev12 SHA-256: `cf1cb360b201a31071532f9280a4277448d63fe156e8f6140a46aaf430db62e5`
- hidden development key SHA-256: `c811882f862942e134588f46164021f25d5575c1eeac8cc1fc000c32ce8eff09`
- frozen response record SHA-256: `e100a59291b9298dae6b2314da712952df0cd367ae4fbd4554cba86d093feb1a`
- response-freeze commit before score: `bd91f9a940c31112bc3010f87a514c594b11610e`
- valid calls: 12
- transport errors: 0
- Pangram calls: 0

## Calibration examples

The v1 four matched pairs were retained. Two literal pairs were added from the two v1 misses:

- P5: direct owner-final Write-It opening versus the model unsent-draft passage;
- P6: owner Romance exclusivity thought route into the B. decision versus the compressed assistant anecdote.

No new abstract anti-pattern or hard veto was added.

## Score

- total: **11/12 = 91.7%**
- Human: **5/6**
- AI: **6/6**
- invalid/missing: 0

This is the first tested configuration in this debugging sequence to combine high sensitivity to AI with high specificity to Human prose, but it is still development evidence and does not satisfy the production 20/20 holdout requirement.

## Only miss — CD2-04 / B18

Gold: HUMAN
Predicted: AI

Direct owner paragraph:

> Don't be afraid to ask your therapist/yourself "What is this practice supposed to help, and how would I know if it's helping?" This sovereign, gently curious stance should apply to everything in life. Feeling calmer or having deeper insights or explanations for the trauma response are some possible signs of initial progress, but if that's the endgame, it's just a cope. Real healing is ultimately measured by reduced need for the therapy, just like real growing up is not something you do forever. And if the therapy is actually working, it should improve your daily life, and especially the health of the inner child-inner adult relationship. Going at it harder isn't as useful as going at it with more wisdom and compassion. Take the parts that work, and innovate on the rest.

The classifier called this AI because it is strongly conceptual, coherent, advice-heavy, and ends in a compact practical stance. That is a real Human counterexample to any residual assumption that owner prose must show obvious wandering, narrative discovery, or unresolved residue.

## Next literal pair

The same article slot has an explicit model predecessor:

> Before doing the same exercise again, know what it is supposed to help and what would actually look different if it were working. You can leave a session calmer and full of insight while the original problem doesn't move at all. If the method keeps giving you no useful contact—or mostly makes you monitor yourself more while daily life gets worse—don't answer that by doing more of it. Keep what genuinely helps and try another way of meeting the same need.

This predecessor is explicit unresolved model prose and had a cached Pangram AI 1.0 result, but the contrastive training label should rest on model provenance, not the detector result.

The owner replacement is **OWNER_REAUTHORING**, not a strict same-thought style-only pair: it expands/reroutes the evaluative stance. Use the pair to teach literal class contrast in the same article function, not as proof of a single causal style variable.

## Method state

Add this as P7 and test on new development passages. Do not add another abstract prohibition.

If the seven-pair classifier continues to discriminate strongly on new development material, the next scientific step is a new untouched 20-item provenance holdout. Only 20/20 on that holdout can make the materially fixed classifier configuration eligible to gate production Pangram.
