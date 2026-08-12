# Current working detector lessons — Romance continuation, 2026-08-12

Research state only. These are contextual findings, not phrase blacklists and not article-skill rules.

- Human editorial quality and fidelity are hard gates. Pangram never outranks the preferred Human endpoint.
- The pronoun instruction `however they fit your life` was detector-sensitive in one opening; `around as you please` and omission did not reproduce the same Pangram regression. Treat this as realization/boundary evidence, not a banned phrase.
- An open-ended conceptual list (`and so forth` or `etc.`) converted one love-definition passage to high-confidence Human where the same closed list did not. This supports list openness/topology as a local variable; the literal words were not causal because both open markers worked.
- Explanatory aftercare can matter: reducing a multi-sentence completion of the selfless-love inference to `It's not about them being yours.` improved Pangram materially in that boundary.
- In the romantic-love passage, a reconstructed Human endpoint reached high-confidence Human. Controlled tests then showed two strong local flips:
  - `Trouble starts when the romantic part is enormous and the selfless part is mostly decorative.` flipped the full passage to AI, while `Trouble starts when there's a lot of romantic love and hardly any selfless love.` stayed Human.
  - `But it is, by its nature, about what I want from one particular person.` flipped AI, while `Romantic love is about...`, `Romantic love is, by its nature, about...`, and `But romantic love is, by its nature, about...` stayed Human.
- Further controls falsified several simplistic explanations:
  - sentence packing/splitting was null in the tested ending;
  - abstract category labels alone were not causal;
  - `by its nature` alone was not causal;
  - `Trouble starts` alone was not causal;
  - `mostly decorative` alone was not causal.
- One remaining local interaction is the matched `the X part is A / the Y part is B` realization: `the romantic part is enormous and the selfless part is tiny` also regressed, while a mixed realization using `there's a lot of romantic love` plus `selfless part is mostly decorative` stayed Human.
- Another remaining local interaction involves anaphoric `But it is, by its nature...`; replacing `it` with `romantic love` removed the regression in the tested boundary.
- Broad lexical rules repeatedly fail. Prefer complete-boundary controlled pairs, factor interactions, nulls, and counterexamples.
- Stop subdividing when the remaining effect is clearly distributed/interactive or the next contrast would become token hunting.
