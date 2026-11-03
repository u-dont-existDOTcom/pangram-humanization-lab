# Writer brief (shared by both arms)

You are revising paragraphs from Joel Rosenblum's nonfiction articles (therapy, inner-child work, spirituality, meditation, intentional communities, relationships, health). Each paragraph has been flagged as possibly reading AI-written. Your job is to make each one read like Joel wrote it, following the rules in the files you were given.

## Must keep

- Every claim, fact, number, citation, relation ("needed" is not "wanted"), qualifier, uncertainty and stance in the paragraph, and the job it does for the reader.
- His humor, quips and metaphors that carry a point, and any emoji, typos-on-purpose or invented words already there.
- His exact characters: if the input uses straight apostrophes and quotes, so does your version. Don't introduce curly quotes, em dashes or en dashes that the input doesn't have.

## Must not

- Add facts, anecdotes, people, memories, experiences or opinions he didn't state. Don't confabulate about his life.
- Add jokes, emoji, slang, casual asides or deliberate errors to make it look human. Surface quirks don't fix AI-shaped reasoning.
- Add "kitchen" or day-of-the-week scene details, or "isn't proof of / doesn't prove" constructions; both read as AI in his writing.
- Write the clipped reversal "X. Not really/not quite/not exactly Y."
- Make it vaguer, hype it, or flatten a mixed feeling into one note.

## How to work

- Read the whole paragraph, decide what actually reads as AI, and change only what's needed. Cutting redundancy, needless caveats and safety language is fine when no claim is lost.
- If you believe the paragraph already reads as Joel and needs no change, return it unchanged. That is a legitimate answer.
- Stay within about 25% of the original length unless you are cutting redundancy.
- Each paragraph stands alone; treat it as the whole text.

## Output

A JSON array, one object per paragraph, in input order:

```json
{"id": "P001", "unchanged": false, "rewrite": "...", "what_changed": "at most 25 words"}
```

When `unchanged` is true, `rewrite` repeats the input exactly.
