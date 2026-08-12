# Romance oxytocin minimal-pair batch — 2026-08-12

Goal: isolate why the model-written oxytocin/attachment paragraph remains high-confidence AI while Joel's one-pass rewrite is high-confidence Human, without changing the underlying explanation more than necessary.

## Known endpoints (owner-reported, Pangram 4)

### AI endpoint

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or people disappearing on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious, turn hostile, feel worthless, or just want to run.

Owner report: full high-confidence AI.

### Human endpoint

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or if  people disappeared on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious. You might feel worthless or fight or flight mode may kick in.

Owner report: full high-confidence Human.

## First batch: 2×2 on information topology only

Hold the reaction content constant as closely as possible. Factors:

- R = conditional restart before the interpersonal event: `or people disappearing on you` → `or if people disappeared on you`
- S = split the reaction inventory after `suspicious` instead of packaging all reactions in one sentence

### R0S0 — baseline

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or people disappearing on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious, turn hostile, feel worthless, or just want to run.

### R1S0 — conditional restart only

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or if people disappeared on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious, turn hostile, feel worthless, or just want to run.

### R0S1 — sentence split only

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or people disappearing on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious. You might turn hostile, feel worthless, or just want to run.

### R1S1 — both topology changes

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or if people disappeared on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious. You might turn hostile, feel worthless, or just want to run.

## Interpretation of first batch

- If R1S0 flips while R0S1 does not: the local issue is primarily the flattened noun/gerund list versus restarted condition.
- If R0S1 flips while R1S0 does not: the local issue is primarily the single polished reaction inventory versus uneven sentence progression.
- If only R1S1 flips: interaction between conditional restart and inventory topology.
- If none flips: the owner reaction-content change matters and requires the second batch.
- If multiple cells flip: repeat the smallest changed Human cell before promoting any rule.

## Second batch only if first batch does not explain the endpoint

Reaction-content factor C changes the last reactions from `turn hostile ... just want to run` to Joel's `fight or flight mode may kick in`. This is not a pure syntax test because content/realization changes, so do not mix it into the first factorial.

### C1 — owner reaction content, baseline conditional, one-sentence inventory

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or people disappearing on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious, feel worthless, or fight or flight mode may kick in.

### C2 — owner reaction content, baseline conditional, split inventory

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or people disappearing on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious. You might feel worthless or fight or flight mode may kick in.

### C3 — exact owner wording normalized to one space

People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or if people disappeared on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious. You might feel worthless or fight or flight mode may kick in.

Compare C3 with the owner-reported exact endpoint containing a double space after `if`. This rules out a whitespace artifact cheaply if needed.

## Run discipline

1. Use exact complete boundaries above; do not test isolated sentences.
2. Pangram model must be explicit `pangram-4`; terminal result version must be `4.0`.
3. Reuse content-addressed cache if an exact variant is already present.
4. First run R1S0, R0S1, R1S1. R0S0 is already owner-reported AI; repeat only if needed for current-version stability.
5. If one first-batch cell flips Human, repeat that exact cell once before interpreting.
6. Run C1/C2/C3 only if the first batch does not isolate the effect.
7. Preserve exact text, SHA-256, detector version, AI fraction/classification, and repeated-call stability in the case record.
8. Do not promote `repeat if = human`, `sentence split = human`, or `fight-or-flight = human`. The target lesson is the editorial operation and its interaction, not a phrase blacklist.

## Editorial hypothesis before measurement

The strongest current hypothesis is that the model keeps flattening semantically non-equivalent material into grammatically uniform conceptual classes. Two possible manifestations are being separated here: (a) `neglect / abuse / people disappearing` rendered as one noun/gerund list rather than letting the interpersonal event restart the condition, and (b) several downstream reactions rendered as one polished exhaustive inventory rather than arriving in uneven thought-sized units.

This hypothesis is provisional until the controlled batch runs.
