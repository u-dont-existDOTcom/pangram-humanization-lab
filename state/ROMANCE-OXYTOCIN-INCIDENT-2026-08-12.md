# Romance oxytocin incident — 2026-08-12

## Why this case matters

A detector-sensitive Romance passage stayed high-confidence AI through multiple assistant rewrites even though the substantive explanation was already coherent. Joel then repaired it in one pass without changing the basic explanation. Pangram 4 returned high-confidence Human.

This is useful because it falsifies the assistant's prior diagnosis that the main problem was the secure-vs-insecure explanatory architecture or that the passage needed a lived anecdote.

## Assistant candidate — high-confidence AI

> People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or people disappearing on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious, turn hostile, feel worthless, or just want to run.

## Joel one-pass repair — high-confidence Human

> People call oxytocin the “love hormone,” which makes it sound like bonding should always feel nice. If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, abuse, or if people disappeared on you, you can get more attached and more freaked out at the same time. You might get anxious or suspicious. You might feel worthless or fight or flight mode may kick in.

## Literal delta

The first two sentences are identical.

Sentence 3 changes only:

- AI: `neglect, abuse, or people disappearing on you`
- Human: `neglect, abuse, or if people disappeared on you`

The Human version breaks the polished noun/gerund coordination by repeating the conditional `if` for the third case.

The final reaction sentence changes from one flat four-part coordinated inventory:

- `anxious or suspicious, turn hostile, feel worthless, or just want to run`

into two sentences with unequal realization:

- `You might get anxious or suspicious.`
- `You might feel worthless or fight or flight mode may kick in.`

The exact semantic inventory is not identical because `turn hostile` / `want to run` becomes `fight or flight mode may kick in`. Therefore this is not yet a pure syntax-only minimal pair.

## Best current interpretation

The strongest current hypothesis is **flat coordination / conceptual-class packaging**, not explanatory content.

The assistant repeatedly tried to make the reactions into one polished complete set. Joel's repair keeps the explanation but stops presenting every response as one grammatically uniform conceptual class. This strongly resembles the earlier MP-003 finding where the same scientific items changed detector behavior when a canonical flat list was replaced by relation-aware syntax.

Important distinction: do **not** infer `rough grammar = human`. The relevant editorial question is whether the syntax is falsely equalizing things that the thought experiences differently. Natural repetition (`or if ...`) and unequal sentence realization may be better because they preserve the actual semantic relations instead of forcing a tidy list.

## Failed assistant diagnosis

The assistant initially concluded that it needed a real-world observation or anecdote to escape abstraction. Joel correctly challenged this. A lived example is not required. The passage was already conceptually sufficient.

The assistant then suspected the secure/insecure explanatory architecture itself had to be removed. Joel's Human endpoint falsified that too: the explanations remained.

## Next controlled tests if useful

Use the Joel Human endpoint as the fixed baseline and isolate only high-information variables:

1. Conditional topology only: `or if people disappeared on you` ↔ `or people disappearing on you`, with the final two sentences held Human.
2. Sentence boundary only: keep the Human reaction wording but combine the last two sentences without converting them into a flat list.
3. Flat-list pressure: express the same Human reaction meanings as one canonical coordinated list, preserving content as closely as possible.
4. Relation-aware one-sentence control: keep one sentence but preserve different predicates rather than one flat enumeration.

Do not spend calls on random vocabulary substitutions.

## Promotion status

High-value replication candidate for the existing `flat coordination × apparent semantic class` lesson. Do not promote a new universal rule until controlled variants separate content change, sentence boundary, repeated conditional syntax, and flat coordination.
