# Romance exclusivity — owner short-text minimal pair — 2026-08-21

Status: **article-specific / provisional detector evidence**. Owner-reported Pangram 4 confidence classifications; no exact numeric fractions or API result JSON supplied. Do not promote a lexical or rhetorical-question rule from this case alone.

## Context

During the Romance detector-repair handoff, assistant rewrites of the `Attraction and exclusivity` passage repeatedly retained a model-shaped explanatory cadence. Joel rewrote the passage directly and manually tested it in Pangram 4 as a short text.

The important evidence has two layers:

1. the owner rewrite is qualitatively different from the assistant's compressed report-style realization; and
2. Joel supplied a near-minimal Pangram control in which adding only `have you ever looked?` changed the reported confidence classification from MEDIUM Human to HIGH Human.

## Owner-selected HIGH-confidence Human version — owner-reported

> It's hard to find sexually monogamous animals, have you ever looked? And as it turns out, we humans aren't a natural exception to the rule, either.  Plenty of tribal cultures were (and some still are) much looser about this, while still generally retaining the primary-partner "social monogamy."  Sexclusivity started gaining sway around the time we started planting carrots and peas, and owning land. That's when it made sense to keep track of how to keep our land in the family bloodline. By the Industrial Revolution, this ironically bureaucratic basis of romance became the only definition of marriage, by law.  I'm not trying to say we're just like bonobos, but the academic consensus is that humans  tend toward flexible pair-bonding, with a propensity for occasional infidelity. And now we've gone one step further, so that even the brief inkling of attraction to another person becomes almost a sure sign that sexual infidelity is next. That's why I felt I had no choice but to address the issue head on  when B. wanted to marry me. I told her, “I can't fully commit to you if I’m still attracted to other women, so before I do, let's see if I can fix that."

## Near-minimal MEDIUM-confidence Human control — owner-reported

> It's hard to find sexually monogamous animals. And as it turns out, we humans aren't a natural exception to the rule, either.  Plenty of tribal cultures were (and some still are) much looser about this, while still generally retaining the primary-partner "social monogamy."  Sexclusivity started gaining sway around the time we started planting carrots and peas, and owning land. That's when it made sense to keep track of how to keep our land in the family bloodline. By the Industrial Revolution, this ironically bureaucratic basis of romance became the only definition of marriage, by law.  I'm not trying to say we're just like bonobos, but the academic consensus is that humans  tend toward flexible pair-bonding, with a propensity for occasional infidelity. And now we've gone one step further, so that even the brief inkling of attraction to another person becomes almost a sure sign that sexual infidelity is next. That's why I felt I had no choice but to address the issue head on  when B. wanted to marry me. I told her, “I can't fully commit to you if I’m still attracted to other women, so before I do, let's see if I can fix that."

Reported delta:

- MEDIUM: `It's hard to find sexually monogamous animals.`
- HIGH: `It's hard to find sexually monogamous animals, have you ever looked?`

Everything else in the supplied pair is identical.

## Assistant comparison — owner-reported ~60% AI

The immediately preceding assistant attempt was much shorter:

> Sexual exclusivity got much more important once agriculture, property and inheritance entered the picture. By the Industrial Revolution, the strict version was everywhere, with law and social pressure behind it. Plenty of tribal cultures have been much looser about what could happen outside a primary partnership, including other sexual or emotional relationships. There’s a term for some of that: social monogamy.
>
> I took exclusivity further than that. B. wanted to marry me, but I was still attracted to other women, and somehow I decided that meant I shouldn’t marry her yet. I told her, “It’s not fair of me to commit to you if I’m still attracted to other women, so before I do, let me see if I can fix that.”

Joel reports this attempt at about **60% AI**.

## Editorial interpretation

The owner version is not simply less polished or more irregular. Its thought route is different:

- it begins from a concrete curiosity about sexually monogamous animals rather than a historical thesis;
- `planting carrots and peas` makes agriculture concrete at the causal hinge rather than adding arbitrary specificity;
- the coined `Sexclusivity` and `ironically bureaucratic basis of romance` carry actual author judgment instead of neutralizing the history into report prose;
- the bonobo caveat answers a real inference created by the animal opening, so it is a live complication rather than mandatory objection-completion;
- the history does not terminate in a mini-essay synthesis before autobiography resumes: `And now we've gone one step further... That's why... when B. wanted to marry me` keeps one causal current running into the personal decision;
- the richer, longer owner version outperforming the compressed assistant version is further counterevidence against `shorter = more Human`.

This extends the owner-labeled `recursive mini-essay rhythm / outline pulse` finding from `joel-articles`: report-style compression can preserve the same model architecture even after sentence rhythm is improved.

## Pangram-specific interpretation

Because the MEDIUM and HIGH versions differ only by `have you ever looked?`, this is unusually clean local evidence that a tiny pragmatic change at the opening can materially alter Pangram 4 confidence on a short boundary.

The plausible detector-level variable is **discourse mode / interlocutor address**, not the literal phrase. Adding a direct question changes the opening from a flat declarative observation into a conversational turn directed at a reader. It also changes the cadence of the first boundary before the rest of the factual chain arrives.

However:

- this is one owner-reported short-text result;
- short boundaries are already known to be less reliable;
- no exact numeric fractions, hashes from Pangram, repeat, or API result record were supplied;
- the result does not establish that second-person questions, rhetorical questions, `have you ever`, or reader address are generally Human signals.

Disposition: **article-specific / provisional**. Preserve the pair for future replication or Pangram-5 comparison; do not promote a general detector rule without independent evidence.
