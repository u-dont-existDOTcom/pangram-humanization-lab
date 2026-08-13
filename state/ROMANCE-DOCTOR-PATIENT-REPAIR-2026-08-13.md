# Romance doctor/patient role repair — 2026-08-13

## Source boundary

Human owner-final lead-in:

> I also have to admit, I can become condescending when somebody stops taking responsibility for their behavior. I find that intolerable. If someone says, “I feel like your patient,” both people need to look at their roles.

The following questionnaire-style role analysis and acute-care/script paragraph were reported fully AI on Pangram 4.

## Coherence finding

The AI span was over-completing the sentence `both people need to look at their roles` as a matched two-sided questionnaire: client motive, doctor motive, then a balanced exception, then a therapy-style conversation script. The acute-care exception was also functionally duplicated later in the next subsection, where the prose already says roles can flip and one partner can carry more for a while.

The unique useful material was narrower:
- on Joel's side, helping can feel good and being needed can feel good;
- he often genuinely did have the information or perspective they needed;
- on the other side, the relevant question is whether they were also trying to take care of themselves without him.

## Preferred replacement

> I know what can happen on my side. Helping feels good. Being needed can feel good too. A lot of the time I really did have the information or perspective they needed, so of course they kept asking me. I also had to look at whether they were trying to take care of themselves without me.

Then go directly to `## Different levels in different domains can be complementary`.

## Detector result

Tested with the exact Human lead-in and the next heading/first paragraph as boundary context on Pangram 4.

- Candidate A: Human, fraction_ai 0.0, high confidence.
- Candidate B (shorter, omitting the `being needed` motive): Human, fraction_ai 0.0, high confidence.

Candidate A is preferred for fidelity because it preserves the unique `being needed can feel good` motive.

Evidence: `state/experiments/romance-doctor-patient-r1-2026-08-13-results.json`.

## Durable lesson

When a Human sentence ends with a live plural claim such as `both people need to look at their roles`, do not automatically unpack each side into a matched question battery. Follow the author's actual pressure asymmetrically. Here the natural route is self-implication first, then the partner-side criterion. If an exception and practical script are already handled later, delete the duplicate completion instead of humanizing it in place.
