# Romance monogamy/polyamory detector incident — 2026-08-13

## Source span

AI-target span supplied by Joel:

> That is not true of everyone, and it does not make polyamory wrong. It may still be more honest than pretending you can do monogamy when you cannot.
>
> A lot of relationships end up in the murky middle between honest monogamy and polyamory: attractions denied, changes in feeling suppressed, possessiveness called love, and both people quietly knowing more than the agreement allows them to say. What's left unsaid is the gap where honesty breaks down.
>
> Sometimes the concealment does more damage than an outside connection would have done.

Immediate prior sentence already says polyamory is **often** used in the criticized ways, so `That is not true of everyone` repeats a scope limitation already present. The source also already says polyamory `can be dishonest`, not that polyamory itself is categorically wrong, so `it does not make polyamory wrong` answers a claim the passage did not make.

The `murky middle between honest monogamy and polyamory` frame is also conceptually weak: attraction to other people does not itself put a monogamous relationship midway toward polyamory. Earlier prose already says two people can choose sexual exclusivity while acknowledging attraction, and immediately before this span Joel says he wants even low-stakes attractions to be mentionable. The list therefore partly repeats already-established material and organizes distinct problems into a false continuum.

`What's left unsaid is the gap where honesty breaks down` is explanatory aftercare: if relevant feelings are being concealed, the honesty failure is already visible.

## Detector trajectory

First-pass full-context candidates A–C: all Pangram 4 = 100% AI.

Second-pass local candidates D–G retaining the full two-part explanatory architecture: all Pangram 4 = 100% AI.

Compressed candidates H–K, which removed the redundant caveat and the `murky middle` taxonomy/list: all Pangram 4 = 100% Human, high confidence.

Attempts Q/R to restore a separate sentence about changing feelings recreated the explanatory sequence and returned to 100% AI in this boundary.

Final exact candidate S:

> If you can't do monogamy, saying so is still more honest than pretending you can. Sometimes the pretending does more damage than an outside connection would have.

Tested together with the immediately preceding retained sentence:

> These days, I believe polyamory is often a way to cope with an inability to connect deeply with one person, or a way to admit a lack of self-control without necessarily doing the self-development that would make the arrangement ethical.

Pangram 4 result: **100% Human, high confidence**; `fraction_ai=0.0`, `fraction_human=1.0`, `ai_assistance_score=0.03103630617260933`; ordinary normalized whitespace. Measurement SHA-256: `063453edec7521496f075a33732f5e93a07db90f7ad763adde462059fa77e937`.

## Editorial conclusion

Use final S unless Joel changes the claim. The repair is primarily deletion/recovery, not synonym-level humanization.

Preserved unique claims:
- some polyamory may be more honest than false monogamy;
- concealment/pretending can sometimes cause more damage than an outside connection.

Omitted here as redundant or overcompleted:
- `not everyone` caveat: already encoded by `often`;
- categorical `polyamory is not wrong` defense: the retained comparison explicitly allows polyamory to be the more honest choice;
- `murky middle` taxonomy/list: attractions are already discussed immediately above, and the continuum itself is semantically misleading;
- `What's left unsaid...`: tautological aftercare;
- separate `changes in feeling` sentence: valid thought, but already supported elsewhere in the marriage-vow/future-feeling discussion and did not need to be repeated here.

## Durable lesson

Before humanizing a detector-red passage, ask whether the AI span is doing redundant qualification or manufacturing a taxonomy/continuum that the underlying thought does not require. If the surrounding prose already carries the scope and examples, deleting the explanatory completion can improve both semantic precision and detector performance. Do not infer that brevity by itself causes the Pangram result; the failed candidates differed in architecture and semantic redundancy as well as length.
