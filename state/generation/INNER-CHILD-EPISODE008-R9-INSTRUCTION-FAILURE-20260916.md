# Inner Child Episode 008 R9 — instruction-design versus implementation failure

Status: PROVISIONAL METHOD EVIDENCE
Date: 2026-09-16
Branch: `task/humanization-method-fingerprint-20260916`

## Exact observed result

The Joel Articles experiment `EPISODE-008-BEFORE-YOU-TRY-TO-GO-DEEP-R9-A-PLAYFUL-DECOMPRESSION-20260916.md` was generated after a frozen sentence/span guide instructed Strategy A: uneven thought-duration/decompression plus sparse playful/cultural lenses.

Owner Pangram screenshot on 2026-09-16 showed:
- 2379 UI words;
- 4 segments total;
- 3 segments AI;
- first visible segment 472 words AI / High;
- only visible Human segment 58 words Human Written / High beginning `I love using one foot to massage the ot...`;
- lower two individual AI segment counts/boundaries were not visible.

If the four displayed segment counts partition the 2379-word UI total, this implies approximately 2321 AI words / 58 Human words = 97.56% AI / 2.44% Human. The exact individual lower segment boundaries are unknown and must not be reconstructed.

R8 had displayed approximately 92.51% AI by word share. R9 therefore regressed by roughly 5.05 percentage points AI despite becoming substantially longer and more playful.

## Was the guide wrong or was the writer wrong?

**Both, with instruction design upstream.**

### Primary: instruction-design failure

The guide stated the right abstract goal—unequal thought duration—but its operational form undermined that goal.

1. It gave a repair row to nearly every conceptual station. This made almost every station look locally rewrite-worthy.
2. Many rows offered an optional playful/meme lens. Even though the prose said play should be sparse, the table made playful realization continuously salient.
3. There was no global edit-dose budget. Local expansions could all look compliant while accumulating into broad expansion. R9 grew from R8's 1549 UI words to 2379 UI words, about 54% longer.
4. The guide did not sharply distinguish `hot thought` from `housekeeping`. Protected semantic functions therefore continued to receive explicit prose instead of being carried inside neighboring sentences or left implicit when an already-preserved example/action performed the function.

The result was a paradox: an instruction intended to create unequal emphasis was represented as an exhaustive, evenly distributed set of local generation opportunities.

### Secondary: implementation failure

The writer then amplified those upstream pressures:

- selected many optional playful images instead of treating them as rare candidates;
- expanded housekeeping as well as hot thoughts;
- preserved the hidden inner-monologue ladder and relationship/checking mini-essay architecture underneath the extra words;
- often used a crafted image as an additional explanatory beat rather than as a replacement for explanation.

Examples of the added recurrent image layer include the steering-wheel image, Pixar committee, movie/theater reset, Supreme Court relationship pause, original-footage/subtitles image, customer-support reversal, and note-under-door image.

So the writer did not faithfully realize the guide's *stated* sparsity, but the guide itself made that error likely by offering too many local playful/decompression affordances.

## Repair to the method

The next guide should not classify every span as `decompress/rewrite`. Instead use four roles:

- `HOT`: selectively expand the psychologically live thought;
- `CARRY`: preserve function without giving it a standalone rhetorical stop;
- `LOCK`: exact known-good wording;
- `SCAFFOLD`: remove/replace realization-only packaging while proving protected function survives elsewhere.

Additional enforcement:

- set a whole-boundary edit-dose range so local expansion must be offset by compression elsewhere;
- cap new crafted playful/metaphorical images across the complete section, not per paragraph;
- admit a playful image only when it replaces explanation rather than adding a second beat;
- allow multiple preservation units to map to one natural sentence/paragraph;
- do not require every paragraph to conclude itself;
- audit whether the instruction artifact itself creates a repeated generation opportunity at every station.

## General lesson

**A method can preserve the correct local instruction schema and still generate global regularity if the instruction artifact distributes that schema too evenly.**

`literal span -> operation -> positive target` remains useful, but a long-boundary guide also needs a **sparsity topology**: which spans deserve generative attention, which should merely carry forward, which are locked, and which model scaffold should disappear without a one-for-one replacement.

The planning artifact is part of the writing environment. If the plan gives every idea a row, a positive target, and an optional creative device, the writer may produce a more polished version of the same comprehensive model coverage even when each row is locally sensible.

This supplements `HUMANIZATION-METHOD-FINGERPRINT-20260916.md`. It does not supersede the existing fingerprint; it adds a long-boundary constraint: **method identity must include not only local instruction structure but also the distribution/sparsity of instructions across the natural boundary.**
