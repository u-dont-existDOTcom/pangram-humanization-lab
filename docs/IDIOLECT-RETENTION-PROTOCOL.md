# Idiolect-retention protocol

This protocol adds **authorship-signal retention** as a separate evaluation axis in Joel humanization work. It is grounded in Malik and Awan, *The Assistant Erased You: Measuring Loss of Authorship Signals in AI-Mediated Communication* (arXiv:2608.00926v1, 2026-08-02), and is implemented here as a dependency-free local instrument.

The paper's Idiolect Erasure Rate (IER) is the percentage-point drop in closed-set authorship-attribution accuracy from held-out originals to aligned AI rewrites. It is not a property of a model alone: the result depends on the assistant, rewrite condition, attributer, and corpus. The authors found that heavy rewriting erased much more recoverable authorship signal than grammar-only correction in personal blogs and workplace email. A prompt explicitly asking the assistant to preserve the writer's voice reduced surface erasure but left most deep authorship signal unrecovered.

## Three independent gates

Do not collapse these into one score:

1. **Meaning and authority:** claims, argument, certainty, provenance, rhetorical function, chronology, and owner-final language survive.
2. **AI-detector acceptance:** the exact reader-visible delivery boundary meets Joel's current Pangram requirement when that requirement applies.
3. **Authorship-signal retention:** the candidate has not needlessly moved away from a held-out corpus of Joel's actual writing.

A candidate may pass Pangram while losing Joel's recoverable idiolect. It may retain measured surface patterns while changing his argument. It may preserve meaning while becoming more generic. No one gate substitutes for another.

## Edit-dose ladder

Use the lowest dose that solves the actual defect.

| Dose | Operation | Default authorship-retention requirement |
|---|---|---|
| D0 | No visible prose change | None |
| D1 | Mechanical spelling, punctuation, capitalization, spacing, or literal agreement correction | Preserve wording and sentence architecture; no metric required unless the boundary changes materially |
| D2 | Local repair of a sentence or short span | Reuse owner language where available; compare the original and candidate when several sentences or a distinctive passage are changed |
| D3 | Sectional reconstruction, rerouting, consolidation, or substantial assistant rewriting | Build a held-out author profile and run `idiolect-retention` before acceptance |
| D4 | Full regeneration or article-wide rewrite | Presume high erasure risk; require the full fidelity/architecture gates, a held-out author profile, and retention reports for the relevant section and final boundary |

The dose is about transformation, not word count. A short sentence can carry a distinctive memory, joke, judgment, or cadence and therefore require stricter protection than a longer neutral connective passage.

## Reference-corpus construction

Use texts that genuinely establish the target byline:

- Prefer `owner-authored untouched` and `owner-edited final` material.
- Match genre and register where possible. A polemic, personal essay, research-conversational guide, and private message need not share the same surface profile.
- Exclude the original passage being evaluated. The tool flags an exact hash overlap, but near-duplicate leakage still requires human review.
- Do not silently treat `assistant-produced owner-accepted` prose as evidence of Joel's natural idiolect. Include it only when the explicit target is the current hybrid publication voice, and label that corpus accordingly.
- Keep profile texts private. The report stores hashes and aggregates, not raw prose.
- More varied, independent samples are better. Fewer than three samples, less than 1,000 profile words, or a test boundary under 50 words is flagged as weak evidence rather than converted into a pass/fail judgment.

A profile is contextual evidence, not a bag of quirks to imitate. Never add errors, filler, catchphrases, odd punctuation, autobiographical details, or pet constructions merely to raise similarity.

## Single-author retention proxy

Use this for routine Joel work:

```bash
pangram-lab idiolect-retention \
  --profile-dir path/to/private-joel-reference-texts \
  --original path/to/original-visible-text.txt \
  --candidate path/to/candidate-visible-text.txt \
  --output path/to/idiolect-retention.json
```

The report contains:

- exact SHA-256 identities for the profile samples, original, and candidate;
- token-change fraction, length ratio, and lexical-set overlap;
- original-vs-profile and candidate-vs-profile similarity for two channels;
- metadata-only quality flags and no raw source text.

The channels are deliberately separate:

- `surface` uses character 2–4-grams and word 1–2-grams. It is closer to a lightweight stylometric fingerprint, but topic and repeated content can affect it.
- `content_light` uses function words, punctuation, contractions, casing, sentence/paragraph length bins, word-length bins, and a reduced syntax skeleton. It is less topic-dependent but still not a deep authorship representation.

Interpret `candidate_minus_original` as direction, not a calibrated score. A negative value means the candidate moved farther from the reference profile on that instrument. A positive value does not prove better voice, natural authorship, or quality. There is intentionally no universal threshold.

The report's lexical overlap value is not semantic similarity. Meaning, claim, and rhetorical-function review remain mandatory.

## Closed-set IER

Use this only for benchmark or method-development work with at least two authors, disjoint profile/evaluation samples, and aligned originals/rewrites:

```bash
pangram-lab idiolect-ier path/to/dataset.json \
  --output path/to/closed-set-ier.json
```

Dataset shape:

```json
{
  "profiles": {
    "author-a": ["training text 1", "training text 2"],
    "author-b": ["training text 1", "training text 2"]
  },
  "items": [
    {
      "id": "a-001",
      "author": "author-a",
      "original": "held-out original",
      "rewrite": "aligned rewrite"
    }
  ]
}
```

The local instrument uses nearest-author cosine against equal-sample profile centroids and reports IER in percentage points for its `surface` and `content_light` channels. It is a valid closed-set attribution-drop calculation for this named instrument, but it is **not numerically equivalent** to the paper's TF-IDF/linear-SVM or LUAR results.

Do not interpret closed-set IER when baseline attribution is not meaningfully above chance. Report author count, evaluation count, chance rate, baseline accuracy, post-rewrite accuracy, corpus design, and instrument version together.

## Decision procedure

For D3/D4 work:

1. Freeze the authoritative original and reader-visible comparison boundary.
2. Create the source–meaning–context–destination and protected-function ledgers.
3. Build the private held-out author profile.
4. Make the smallest coherent edit.
5. Run semantic sanity, fidelity, architecture, and cold prose-shape audits.
6. Run `idiolect-retention`.
7. If either measured channel moves substantially away from the profile, inspect the exact edit rather than manufacturing stylistic tics:
   - restore owner wording;
   - reduce the edit dose;
   - localize the repair;
   - recover a missing owner realization;
   - separate structural movement from sentence rewriting;
   - preserve a necessary neutral connective rather than polishing it.
8. Run Pangram only under the existing authorization, boundary, cache, and paid-call rules.
9. Accept a candidate only when the editorial gates pass. Treat detector and idiolect evidence as distinct recorded results.
10. Preserve the report beside the revision evidence. Never commit the raw private profile corpus unless the owner explicitly chose that repository destination.

When two candidates are equally faithful and coherent, prefer the lower-dose candidate and use the retention report as one tie-breaker. Do not use it to overturn a clearly better owner-selected sentence.

## Known limitations

- The paper measures computational attribution, not recognition by readers who know the author.
- Surface methods are confounded by topic, genre, source quoting, formatting, and repeated subject vocabulary.
- The local instrument is intentionally lightweight and does not reproduce LUAR's deep representation.
- Short passages and small or contaminated profiles are unstable.
- A metric can be gamed. Optimizing directly for it can produce caricature or corpus mimicry.
- Reduced attributability can be desirable for privacy or anonymity; preservation is the chosen objective for Joel's byline, not a universal moral rule.
- AI-detector status and authorship retention are orthogonal. A text can become difficult both to attribute to its author and to identify as AI-assisted.

## Repository boundary

- `u-dont-existDOTcom/joel-articles` owns editorial authority, edit-dose policy, corpus/provenance rules, and article acceptance.
- This repository owns the measurement implementation, tests, metadata-only reports, detector evidence, and research-method limitations.
- A paper result or local metric never authorizes changing Joel's claims, certainty, politics, allegations, personal history, or argument.
