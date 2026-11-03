# Paragraph census of the registered articles on Pangram 4.1

Date: 2026-11-03. Owner direction (Joel, 2026-11-03): use this week's spare Pangram credits on work that teaches humanization better and quicker. Status: INPUTS FROZEN; transport (API or GUI) pending Joel's answer on which credits expire.

## What

Every reader-visible block of 25+ words in each registered joel-articles master (registry at joel-articles `1cac9dd`, every master hash verified), checked alone: 1,536 paragraphs, about 84,000 words, about 1,634 credits at one per started 100 words. `build_census.py` makes `census_inputs.json`; it keeps each paragraph's exact characters and its nearest heading.

## Why

- **For the articles:** Joel's rules are that every paragraph passes alone and that less than High confidence is not done. This is the first full map of where each article stands on both, under 4.1. It is a snapshot of the masters at that commit, not an edit and not certification of any article; one census check counts as one attempt in its paragraph's lineage under the 2026-10-20 budget.
- **For the lab:** about 1,500 labelled paragraphs from distinct passage families in real articles. Rounds 1 and 2 drew on 98 saved lane outputs. This set supports measuring which tells actually go with AI windows in his finished prose, and calibrating forecasts on paragraphs nobody chose for checking.

## Rules

No article text changes. Results go to the lab, not into any article's detector evidence, until Joel asks. Paragraphs are sent one per check, never whole articles.
