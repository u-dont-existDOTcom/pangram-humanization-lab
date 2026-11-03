# Blind forecast test on already-scored Pangram 4.1 texts (round 1)

Date: 2026-11-03. Owner direction (Joel, 2026-11-03): use this week's spare credits for experiments that teach humanization better and quicker. Status: PREREGISTERED. Zero new Pangram calls.

## Question

Can a fresh reviewer that never sees the scores predict Pangram 4.1's verdict on Joel-lane paragraphs better than always guessing "Human"? The lab's earlier 15-text diagnostic (PR #179) scored 11/15 against 10/15 for always-Human, with the current Chat model and prior archive familiarity.

## Sample (frozen before any forecast)

`build_sample.py` read every saved 4.1 result in the laptop lanes' content-addressed caches (25–400 words), merged near-duplicates into families (word-trigram Jaccard ≥ 0.4), took one seeded representative per family, then drew up to 50 all-Human and 50 not-all-Human families with at most 8 per lane. Result: 98 texts (50 all-Human, 48 not), 24 lanes. The sample is balanced on outcome for measuring discrimination; the natural family rate was 118 all-Human of 167.

`blind_packet.json` holds only id, word count and text. The answer key stays outside this branch until every forecast is committed.

## Arms

- A: cold read, no catalogue.
- B: the same reviewer setup plus `joel-articles/docs/HUMANIZATION-TELL-INVENTORY.md`.

Each forecast gives P(all-Human), a label (Human / Mixed / AI) and a one-line reason. Forecasts are committed before the key is added.

## Metrics

Accuracy at P ≥ 0.5 against the 50% always-Human baseline on this balanced sample; Brier score; AUC; accuracy by lane type and length. Misses are read for what they share. No production rule is promoted from this round alone.
