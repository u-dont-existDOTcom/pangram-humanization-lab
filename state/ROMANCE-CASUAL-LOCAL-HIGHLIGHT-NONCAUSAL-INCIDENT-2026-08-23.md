# Romance Casual local-highlight noncausality incident — 2026-08-23

Status: article-specific detector evidence reinforcing the existing rule that displayed AI windows localize detector output, not necessarily causal prose.

## Source boundary

Joel manually tested a 211-word natural boundary from the Romance `Can Casual Sex or a Situationship Actually Be Honest?` opening in Pangram 4 GUI. In the original boundary, Pangram showed a mixed result at about 40% AI, with only the beginning and ending highlighted while the middle remained Human.

Original highlighted beginning:

> Your body doesn’t know that you picked someone up at a bar and agreed it was only for fun. Oxytocin, vasopressin, and the rest can start attaching you anyway.

Original highlighted ending:

> The STI part is easy: say what you know, or say you don’t know. Feelings aren’t. You can both mean it when you say this is only sex and still have one of you get attached afterward. If you’re both really numb or robotic about sex, maybe not.

The middle — including the next-morning consequence, Russian-Roulette judgment, candid-intention quote, and pregnancy-responsibility sequence — was displayed Human.

## Assistant hypothesis and minimal-pair attempt

The assistant hypothesized that the red beginning and ending were detector-sensitive because they acted as polished conceptual wrappers around a more lived middle: thesis→mechanism at the start and category→rule→exception at the end.

A diagnostic candidate therefore changed only those two displayed-red wrappers and left the previously Human middle unchanged:

Opening candidate:

> Suppose you pick someone up at a bar and you both agree it's just for fun. You can both mean it. Your oxytocin and vasopressin aren't making the same promise.

Ending candidate:

> With STIs I can at least tell you what I know and what I don’t. I can’t tell you in advance whether I’ll get attached. Neither can you. We can both mean “this is only sex” and still find out afterward that one of us got pulled in. If sex is pretty numb for both of us, maybe neither of us does.

No middle prose was intentionally changed.

## Owner-reported result

Joel reran that whole natural boundary manually in Pangram 4 GUI and reported:

> `that whole thing is now 100% high conf ai!`

Treat this as owner-reported GUI evidence until/unless an exact History/result wrapper is later recovered. Do not invent exact numeric fractions beyond the owner's report.

## Falsified interpretation

The result falsifies the prior claim that the displayed-red beginning and ending were sufficient causal loci whose local repair should leave the Human middle stable.

The stronger supported interpretation is:

- within this ~211-word boundary, Pangram classification is strongly compositional/nonlocal;
- changing only boundary ends can reclassify byte-identical middle prose from Human to high-confidence AI;
- displayed highlights identify where the model currently assigns AI probability, not necessarily where the prose-level cause lives;
- therefore local-highlight rewriting without a controlled whole-boundary comparison can worsen the detector result and create false causal stories.

This is consistent with the already-promoted long-document split/context-sensitivity lesson, but demonstrates the same noncausal-localization problem at a much smaller natural-section scale.

## Editorial consequence

Do not promote the assistant wrapper rewrite into the article. Keep it diagnostic-only and fidelity-neutral/rejected for production. The original Casual opening remains higher authority until Joel supplies direct wording or a stronger preservation-safe owner/source realization.

## Next experiment rule

If further testing is worthwhile, change **one** variable at a time on the original 211-word boundary (for example only the first two sentences, or only the final paragraph) and preserve all other bytes. Do not infer that the original GUI highlight defines the causal edit scope. Because Casual's repository local-call loop is already exhausted, assistant-run paid local experiments remain closed unless the owner explicitly authorizes a new budget; owner-run manual controls may still be recorded as external evidence.
