# Romance Vows — 20-call rule-learning synthesis (R1–R4)

**Date:** 2026-08-16  
**Status:** detector research; no article authority  
**Detector:** Pangram 4.0  
**Program audit:** `romance-vows-rule-learning-2026-08-16`

## Owner/editorial boundary

Joel's direct 897-word Vows rewrite remains the editorial endpoint regardless of detector results. It tested Human `1.0` / AI `0.0` before this program. The research variants below are synthetic probes only.

The 20-call program began after the earlier 12-call Vows isolation work. It used the full owner-authorized allowance and therefore stops here pending renewed permission.

## Research question

The old assistant Vows candidate had tested about 39.4% AI while Joel's direct rewrite tested 0% AI. Earlier local experiments had already isolated two effects:

1. formal source-certification wording around Ecclesiastes;
2. a three-move closing package that overcompleted the section after a real stopping point.

The remaining question was whether those effects explained the full difference, and if not, which larger realization/architecture factors mattered.

## R1 — falsifying obvious middle-section explanations

### R1a disclosure 2×2 — 4 calls

Factors:

- compact owner setup `open up` vs assistant-explicit setup `say the actual thing without hiding the insecurity behind anger`;
- no post-example interpretation vs the assistant four-sentence interpretation after the jealousy example.

All four cells were Human `1.0` / AI `0.0`.

AI-assistance scores:

- compact / no aftercare: `0.0038541914`;
- explicit / no aftercare: `0.0026886584`;
- compact / aftercare: `0.0182067323`;
- explicit / aftercare: `0.0142003978`.

**Finding:** neither the more explanatory setup, the post-example interpretation, nor their interaction is detector-causal on Joel's owner backbone. Their editorial redundancy can still be real. This is a direct counterexample to treating `interpretive aftercare` as an intrinsically AI lexical/syntactic pattern.

### R1b full-section middle cluster swaps — 3 calls

On the full owner backbone, restore:

- the assistant story/diagnosis cluster;
- the assistant disclosure/aftercare cluster;
- both together.

All three full-section variants remained Human `1.0` / AI `0.0`.

Assistance scores rose modestly (`0.1532`, `0.1700`, `0.1850`) but did not cross into an AI segment.

**Finding:** the old assistant middle prose is not sufficient to recreate the old full-section detector result. The causal problem lies elsewhere or requires a different backbone interaction.

## R2 — whole-section composition of the two known local mechanisms

Owner full section A0B0 was reused from cache at AI `0.0`.

A = owner Bible source relation vs formal `explicitly states...` realization.  
B = owner stopping point vs appending the old three-move conclusion package.

Paid cells:

- A1B0 formal Bible only: AI `0.0443450734`;
- A0B1 old ending only: AI `0.0681494698`;
- A1B1 both: AI `0.1103803739`.

The single-factor fractions sum to `0.1124945432`, almost identical to the combined `0.1103803739`.

**Finding:** on the owner backbone the formal source-reporting sentence and overcompleted closing behave as approximately independent/local additive regions. Together they explain only about 11 percentage points of the old 39.4% AI result.

## Exact old-assistant raw anchor — 1 call

The exact 984-word developmental candidate was captured in the lab:

- SHA-256: `8ce5810925d0ed8d19195dfa5ca177348c2d9dd19e91fcdd1bed1f18315171e3`;
- AI: `0.3936096728`;
- Human: `0.6063903570`.

Pangram marked:

1. the 46-word formal Ecclesiastes sentence AI, assistance `0.5282391310`;
2. a 327-word late tail AI, assistance `0.6450310349`, High confidence.

This reproduced the prior UI/PDF result almost exactly and established raw detector provenance.

## R3 — reverse repairs on the old assistant backbone — 3 calls

Baseline: AI `0.3936096728`.

- replace only the formal Bible paragraph with Joel's natural source relation: AI `0.3528699875`;
- remove only the old final three-move conclusion package: AI `0.2858434319`;
- apply both: AI `0.2430769205`.

The reductions are again close to additive.

After both repairs, one contiguous 211-word AI tail remained, assistance `0.6100592613`, High confidence. It covered the history/property/polyamory/old-murky movement.

**Finding:** the two known mechanisms generalize back to the old backbone, but most of the old assistant regression remains in the late-tail realization.

## R4 — functional tail decomposition — 6 calls

Frozen baseline: R3 both-repairs variant, AI `0.2430769205`.

Functional factors:

- C: remove generic `Those origins still matter.` bridge;
- D: replace old abstract murky-middle inventory/summary with Joel's behavioral murky realization;
- E: add Joel's Tamera provenance parenthetical/link;
- F: restore Joel's `y'all are less likely...` in the preceding disclosure sentence instead of `people are less likely...`.

### Main/interaction cells

- C only: AI `0.3190831244` — worse;
- D only: AI `0.2723928690` — slightly worse;
- E only: AI `0.2551965117` — essentially null/slightly worse;
- D+E: AI `0.1756253392` — substantial improvement;
- C+D+E with `people`: AI `0.1715100706` — essentially the same as D+E;
- C+D+E+F (`y'all`): Human `1.0` / AI `0.0`.

### Window interpretation

In E-only, the history/property span remained AI and the old murky close remained AI. With D+E, the later polyamory/murky portion became Human, leaving the preceding chosen-exclusivity/history/property span as the main AI region.

C did not solve that region. The C+D+E structural package still had a 151-word history/property AI window with assistance `0.6061039567`, High confidence.

The final C+D+E+F variant differs from C+D+E by one local realization: `people are less likely...` → `y'all are less likely...`. That exact 940-word variant became entirely Human, one High-confidence window, assistance `0.1842810959`.

## What this supports

### 1. Detector effects are strongly epistatic/contextual

Several factors have null or adverse main effects but a favorable interaction. D and E are the clearest example. This makes simple surface blacklists unreliable even when a local minimal pair looks dramatic.

### 2. Overcompletion is a real functional mechanism, not an intrinsic sentence property

The earlier ending work showed three individually Human closing moves became Mixed only as a stacked package after the thought had already landed. R1 then showed that another apparently redundant explanatory passage can remain completely Human on a different backbone. The transferable rule is about **function and stopping point**, not a syntactic class called `aftercare`.

### 3. Formal source-certification wording is a repeatable local mechanism in this section

The `explicitly states...` Ecclesiastes realization repeatedly created the same localized AI segment; the owner `teaches that...` relation removed it. It also reduced AI when repaired on the old backbone. This remains a section-local realization lesson until replicated elsewhere.

### 4. A tiny idiolect change can gate a large Pangram reclassification after structural repairs

The final exact minimal pair is unusually strong: C+D+E with `people` remained 17.15% AI, while changing that one realization to Joel's `y'all` made the 940-word boundary 100% Human.

This must **not** be promoted as `use y'all`. The best current interpretation is that after the larger architecture has moved a boundary near Pangram's decision surface, a highly author-specific lexical realization can act as a classifier anchor and change segmentation of a much larger region. The effect may be specific to this boundary/model and could be a threshold/segmentation artifact.

### 5. Owner realization as a distribution can matter more than individually interpretable repairs

The experiments repeatedly resist a simple additive story. Many Joel changes that are editorially meaningful are detector-null alone; some unfavorable factors become favorable in combination; one idiolect marker finishes a global flip only after a larger tail package is in place. Humanization therefore appears partly **distributional/interactional**, not reducible to a checklist of local banned constructions.

## What this does not support

Do not promote any of these as generic tricks:

- `y'all`;
- adding a URL or named authority;
- deleting `Those origins still matter`;
- always shortening paragraphs;
- always removing interpretive explanation;
- always splitting source-reporting sentences;
- avoiding one specific word solely because it flipped this boundary.

The nulls and sign reversals directly argue against those simplifications.

## Editorial consequence for Vows

None. Joel's direct rewrite was already the chosen endpoint and already tested Human `1.0`. This research explains detector behavior; it does not license re-editing the section.

## Call accounting

Owner-authorized new learning allowance used: **20 / 20 paid calls**.

By section:

- disclosure factorial: 4;
- full middle-cluster swaps: 3;
- Bible/ending composition: 3;
- old assistant raw anchor: 1;
- old-backbone reverse repairs: 3;
- tail functional decomposition: 6.

Pending resumes: 0.

No further paid rule-learning call should be made without renewed Joel authorization.

## Highest-value next research if authorization is extended

Do **not** continue subdividing Vows words. The next useful work is cross-boundary replication/holdout:

1. test cumulative overcompletion in a different owner/assistant section where the real stopping point is already known;
2. test formal source-certification vs natural source relation in a different cited passage;
3. test whether an owner-specific idiolect marker can produce a similar threshold/segmentation flip in a different near-boundary passage, using multiple natural realizations rather than `y'all` variants;
4. preserve nulls and sign reversals so a transferable rule is promoted only if it survives another boundary.

A small follow-up of roughly 6–8 calls would be enough to distinguish `Vows-local classifier quirk` from a more general interaction/idiolect phenomenon without turning the work into phrase hunting.