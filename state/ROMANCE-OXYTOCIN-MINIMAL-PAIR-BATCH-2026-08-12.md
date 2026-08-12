# Romance oxytocin minimal-pair batch — 2026-08-12

Goal: isolate why the model-written oxytocin/attachment paragraph remains high-confidence AI while Joel's one-pass rewrite is high-confidence Human, without changing the underlying explanation more than necessary.

## Known endpoints

### AI endpoint

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or people disappearing on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious, turn hostile, feel worthless, or just want to run.

Owner report: full high-confidence AI.

### Owner endpoint as actually pasted

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or if  people disappeared on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious. You might feel worthless or fight or flight mode may kick in.

Owner report: full high-confidence Human. Note the two ASCII spaces after the second `if`; this turned out to be detector-causal in this exact boundary.

## Factors

- **R — conditional restart:** `or people disappearing on you` → `or if people disappeared on you`
- **S — reaction-inventory split:** one coordinated reaction sentence → sentence break after `suspicious`
- **C — reaction realization/content:** `turn hostile, feel worthless, or just want to run` → `feel worthless or fight or flight mode may kick in`
- **W — one additional ASCII space:** `or if people` → `or if  people`

R, S, and C are visible editorial changes. W is an accidental formatting difference and must not be treated as a human-writing technique.

## First batch — R/S topology with original reaction realization

| Cell | R | S | C | Pangram 4.0 result | AI fraction |
|---|---:|---:|---:|---|---:|
| R1S0 | 1 | 0 | 0 | AI, high confidence | 1.0 |
| R0S1 | 0 | 1 | 0 | AI, high confidence | 1.0 |
| R1S1 | 1 | 1 | 0 | AI, high confidence | 1.0 |

Conclusion: neither R, S, nor R×S was sufficient. The original topology-only hypothesis was falsified for this boundary.

## Second batch — add owner reaction realization C

| Cell | R | S | C | W | Pangram 4.0 result | AI fraction |
|---|---:|---:|---:|---:|---|---:|
| C1 | 0 | 0 | 1 | 0 | AI, high confidence | 1.0 |
| C2 | 0 | 1 | 1 | 0 | AI | 1.0 |
| C7 | 1 | 0 | 1 | 0 | AI | full-text AI classification |
| C3 | 1 | 1 | 1 | 0 | Mixed | 0.4439140856 |
| C4 owner exact | 1 | 1 | 1 | 1 | Human, high confidence | 0.0 |

The visible owner changes form a local three-way interaction: every tested one- or two-factor subset remained fully AI, while R+S+C together moved the boundary to Mixed. None of the visible components should be promoted as an independent humanization rule.

## Whitespace minimal pair and repeat

The exact C3/C4 difference is one additional ordinary ASCII space after `if`:

- **C3:** `or if people disappeared ...` → Mixed, AI fraction 0.4439140856
- **C4:** `or if  people disappeared ...` → Human, AI fraction 0.0, high confidence

Fresh independent measurement keys reproduced the effect:

- **C6 repeat, single space:** Mixed again, AI fraction 0.4439140856
- **C5 repeat, double space:** Human again, AI fraction 0.0, high confidence

Therefore the final jump from Mixed to full high-confidence Human is a reproducible **Pangram whitespace artifact in this exact boundary**. The detector is sensitive to an invisible formatting difference that has no plausible authorship meaning.

## What this does and does not teach

### Supported

1. The model repeatedly over-organized this material, but the initially suspected R/S topology changes alone did not explain Pangram's classification.
2. Joel's visible rewrite did materially alter the detector boundary only as a combination: conditional restart + sentence split + changed reaction realization moved the text from full AI to Mixed.
3. The owner-reported full-Human endpoint was confounded by an accidental double space. The one-space version of the same visible prose is Mixed, not full Human.
4. Pangram 4 can be extremely sensitive to whitespace in a short boundary. Detector endpoints must therefore be checked for invisible formatting differences before they are used as writing evidence.
5. Exact-text SHA-256, whitespace normalization comparison, and repeated measurements are necessary when a one-pass owner edit appears to produce a dramatic detector flip.

### Not supported

- `repeat if = human`
- `split the sentence = human`
- `fight or flight = human`
- `double spaces = human`
- deliberate typo/spacing injection as a humanization technique
- treating the full-Human C4/C5 result as proof that its prose is more naturally human than C3

## Editorial consequence

Do not preserve or introduce a double space merely to satisfy Pangram. Choose wording on semantic, coherence, and voice grounds, normalize accidental formatting for publication, and treat the detector result as confounded when normalization changes the verdict. If a normalized, editorially preferred passage remains Mixed, improve it only for a real prose reason; do not add invisible noise to force green.

## Run discipline and evidence

- Detector: Pangram 4, terminal version `4.0` in every recorded cell.
- Exact texts and SHA-256s are stored in `state/experiments/romance-oxytocin-r1-2026-08-12-results.json` and `state/experiments/romance-oxytocin-c-2026-08-12-results.json`.
- Exact repeat measurement keys were used for C5/C6 rather than reading the original result from cache under the same measurement identity.
- The GitHub Actions fixed-batch path checkpoints task IDs and terminal results to the private repository before proceeding to another paid call.

## Process lesson

When an owner rewrite seems to solve in one obvious try while the model repeatedly fails, compare the literal strings before inventing a psychological or rhetorical explanation. Distinguish:

1. visible editorial changes;
2. interactions among those changes;
3. invisible formatting changes;
4. detector variance.

Only after those are separated should the result become a humanization lesson. In this case, the visible edit was useful evidence, but the final green classification was partly a detector-formatting accident.
