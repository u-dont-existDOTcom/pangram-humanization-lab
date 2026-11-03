# Paragraph census of the registered articles on Pangram 4.1

Date: 2026-11-03. Owner direction (Joel, 2026-11-03): use this week's spare Pangram credits on work that teaches humanization better and quicker. Status: INPUTS FROZEN; transport (API or GUI) pending Joel's answer on which credits expire.

## What

Every reader-visible block of 25+ words in each registered joel-articles master (registry at joel-articles `1cac9dd`, every master hash verified), checked alone: 1,536 paragraphs, about 84,000 words, about 1,634 credits at one per started 100 words. `build_census.py` makes `census_inputs.json`; it keeps each paragraph's exact characters and its nearest heading.

## Why

- **For the articles:** Joel's rules are that every paragraph passes alone and that less than High confidence is not done. This is the first full map of where each article stands on both, under 4.1. It is a snapshot of the masters at that commit, not an edit and not certification of any article; one census check counts as one attempt in its paragraph's lineage under the 2026-10-20 budget.
- **For the lab:** about 1,500 labelled paragraphs from distinct passage families in real articles. Rounds 1 and 2 drew on 98 saved lane outputs. This set supports measuring which tells actually go with AI windows in his finished prose, and calibrating forecasts on paragraphs nobody chose for checking.

## Rules

No article text changes. Results go to the lab, not into any article's detector evidence, until Joel asks. Paragraphs are sent one per check, never whole articles.

## Result (2026-11-03)

Transport: API (Joel, 16:04 UTC: all his credits expire in a few weeks, so the census used API credits for window confidence). All 1,536 paragraphs returned version 4.1; `CENSUS-RESULTS.json` holds each result with its window confidences and public link, and `CENSUS-REPORT.md` (from `make_report.py`) lists per article every paragraph that is not 100% Human at High confidence.

Of 1,536 paragraphs, 664 pass Joel's standard; 166 read Human below High; 619 are Mixed; 87 read fully AI. The finished articles are close: Intentional Communities 197 of 234 pass with none fully AI, Romance 250 of 350 with none fully AI, Nibbāna 137 of 205 with one. For Inner Child, Inner Signal, Somatic Therapies and Neuro De-Armoring the registered master can be older than the lane's current draft, so those rows map the registered text only.

Dispositions: the per-article lists are **article-specific** work for each lane, not a lesson; the corpus is **provisional** research material for tell-precision and forecasting studies.
