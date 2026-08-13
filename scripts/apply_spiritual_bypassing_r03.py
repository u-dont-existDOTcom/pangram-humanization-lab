#!/usr/bin/env python3
from pathlib import Path

SOURCE = Path('inputs/spiritual-bypassing-r02-2026-08-13.md')
OUT = Path('/tmp/spiritual-bypassing-r03.md')
text = SOURCE.read_text(encoding='utf-8')

replacements = [
(
'''Hey lovey bunnies. This one is about Goenka retreats, trauma, and spiritual bypassing, so I’m going to try not to turn it into either a takedown or a meditation pep talk.

If you’ve had a wonderful Goenka retreat, I’m not trying to argue you out of what helped you. If you’ve been harmed by one, I’m also not going to tell you the harm was just a “dark night” you should have pushed through. I’m interested in what happens when a practice built around not reacting meets a nervous system that may have very good reasons for reacting.

And because this is sensitive territory, take what is useful and leave what isn’t. You don’t owe any meditation method your trust just because it is old, Buddhist, or worked beautifully for somebody else.

For me, healing has to start with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com).

---

# The Dark Side of Deep Dives: When Intensity Meets Unhealed Wounds

A Goenka retreat is ten days of silence, scanning body sensations, watching whatever comes up and trying not to react while old *sankharas*—mental habits—surface. For plenty of people this is powerful and life-changing. It can build discipline and give a real taste of equanimity.

But it is also a lot to throw at somebody.''',
'''Hey lovey bunnies. Goenka retreats are one of those things where people can do the same ten days and sound like they went to different planets. Some come out saying it changed their life. Some come out badly destabilized.

So I’m not going to tell anybody what their retreat “really” was. If it helped you, great. If it hurt you, I’m definitely not going to tell you the harm was a “dark night” you should have pushed through. What I want to look at is what happens when a method whose main instruction is not to react runs into a nervous system that may have very good reasons for reacting.

This is sensitive territory too. Read as much or as little as is useful to you. You don’t owe a meditation method your trust because it is old, Buddhist, or worked beautifully for somebody else.

For me, healing starts with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com).

---

# The Dark Side of Deep Dives: When Intensity Meets Unhealed Wounds

Ten days of silence. You scan body sensations while old *sankharas*—mental habits—surface, and whatever happens you practice not reacting. Lots of people love this. They come away with more discipline and a real taste of equanimity.

It is also a lot to throw at somebody.'''
),
(
'''The Goenka instruction is to observe whatever comes up without reacting. That can be useful. But when what comes up is trauma, simply witnessing it may not be enough. You can uncover something enormous without yet having a way to work through it.

Forums like [r/vipassana](http://Reddit.com/r/vipassana) are full of these “dark night” experiences. The practice can bring buried material to the surface while giving the practitioner little besides continued non-reaction with which to meet it. Retreat centers do screen for problems, but critics say the screening is not enough, and that the “push through” ethos can nudge people past their limits. Some teachers warn that without emotional groundwork it is a bit like revving an engine without oil: eventually something can seize up.

And this is where spiritual bypassing enters the picture for me. Equanimity can become a way to avoid emotional mess instead of healing it. It can also become a way to ignore injustice while calling that inner peace. Remember some of the Buddhist responses to the Myanmar coup?

So I keep coming back to a pretty simple question: why not teach people how to meet suffering with love before asking them to sit inside it for ten days?''',
'''What bothers me isn’t that old stuff can come up. That is partly the point. It’s that the basic instruction stays the same no matter what comes up: observe it and don’t react. If what is surfacing is manageable, maybe that is exactly useful. If somebody is starting to dissociate or come apart, I’m not convinced more non-reaction is what they need.

That worry isn’t theoretical. [r/vipassana](http://Reddit.com/r/vipassana) has plenty of people describing “dark night” experiences after buried material came up. Retreat centers already screen people out because they know some nervous systems are at higher risk. Critics say that once somebody is inside, though, the culture can still become “push through.” Some teachers warn that doing this without emotional groundwork is like revving an engine without oil. Eventually something can seize up.

That is also where I think spiritual bypassing can sneak in. Equanimity is useful. Using equanimity to sidestep the emotional mess is something else. So is ignoring injustice and calling that inner peace. Remember some of the Buddhist responses to the Myanmar coup?

Which leaves me with the question I actually care about: why not teach people how to meet suffering with love before asking them to sit inside it for ten days?'''
),
(
'''The Buddha understood the need for that kind of groundwork too. In suttas like the [Metta Sutta or MN 118](https://suttacentral.net/snp1.8/en/mills?lang=en), the practice is to wish ease and happiness for all beings, including the tricky one: yourself. Metta is a prelim to vipassana: it calms the hindrances, builds goodwill, and helps the mind want suffering to end without turning that wish into desperation or fear of failure.''',
'''The Buddha didn’t treat kindness as something you tack on after the hard part. In suttas like the [Metta Sutta or MN 118](https://suttacentral.net/snp1.8/en/mills?lang=en), the practice is almost embarrassingly simple: wish beings ease and happiness. Yourself too. Metta is a prelim to vipassana because it calms the hindrances and builds goodwill. It lets you want suffering to end without that wish turning into desperation or fear that you’ll fail.'''
),
(
'''In [Goenka’s](http://Dhamma.org) system, though, metta shows up briefly on day ten, mainly as a way of sharing merit. To me that feels backwards. It skips the Buddha’s kindness-first approach, which he taught was necessary to bring the mind to a state ready for real [nibbana](http://nibbana.u-dont-exist.com) meditation. The kindness I would most want available when somebody’s trauma starts surfacing is introduced after nine days of the intense part.''',
'''[Goenka](http://Dhamma.org) does include metta, but basically at the finish line: briefly on day ten, mainly to share merit. That feels backwards to me. It skips the Buddha’s kindness-first approach, which he taught was necessary to bring the mind to a state ready for real [nibbana](http://nibbana.u-dont-exist.com) meditation. The kindness I would most want available when somebody’s trauma starts surfacing arrives after nine days of the intense part.'''
),
(
'''There is another problem I have with the Goenka approach even apart from trauma.

Vipassana, as I understand it, is supposed to unweave perception—not just leave somebody watching experience from the position of a cosmic spectator. Goenka’s body scanning can refine awareness and make *anicca*—impermanence—very obvious, but some Theravada practitioners say it can leave the “unified witness” intact.''',
'''My second problem with Goenka has nothing to do with trauma. I don’t think watching perception and unweaving perception are the same thing.

Vipassana, as I understand it, is supposed to unweave perception. Goenka’s body scanning can make *anicca*—impermanence—very obvious. But some Theravada practitioners say it can leave you at the “unified witness” level: there is still somebody back there watching the whole show.'''
),
(
'''Punching bags don’t help [rid you of anger](https://open.substack.com/pub/ibogaqueen/p/anger-cant-afford-the-rent-my-heart?utm_source=share\\&utm_medium=android\\&r=5vdc6m); they just help you use it better. I think intense concentration can do something similar: create temporary calm without fully unwinding what is underneath. If trauma is still there, that calm can eventually flip back into distress.

Maybe Goenka’s path sparks nibbana for some people.''',
'''Punching bags don’t help [rid you of anger](https://open.substack.com/pub/ibogaqueen/p/anger-cant-afford-the-rent-my-heart?utm_source=share\\&utm_medium=android\\&r=5vdc6m); they just help you use it better. That’s why temporary calm might flip to distress if traumas aren’t fully unwound.

Maybe Goenka’s path sparks nibbana for some people.'''
),
(
'''A metta-heavy retreat is one possibility. Trauma-informed mindfulness is another. Mindfulness-Based Stress Reduction combined with therapy may fit some people better. So might working with a teacher who is actually willing to slow down when your nervous system says no. [Insight Meditation Society](http://dharma.org) and [Plum Village](http://plumvillage.org) are two places to look.

None of those names means you have to hand over your judgment. Ask questions. Notice how teachers respond when somebody says a practice is making them worse. If something feels destabilizing, you are allowed to stop.

Your path is yours to shape.''',
'''Personally, I would care less about the lineage and more about what the teacher does when I say, “This is making me worse.” Maybe a metta-heavy retreat fits. Maybe trauma-informed mindfulness does. Mindfulness-Based Stress Reduction alongside therapy may fit better for some people. [Insight Meditation Society](http://dharma.org) and [Plum Village](http://plumvillage.org) are two places I would look.

And I would ask them directly: What happens if I start dissociating? What if I need to stop? Do you treat that as information, or as resistance I’m supposed to push through? A good name is not a reason to hand over your judgment.

If something is destabilizing you, you are allowed to stop. Your path is yours to shape.'''
),
(
'''Here are some of the most severe personal accounts I found about negative experiences at Goenka Vipassana retreats. I prioritized reports involving intense psychological breakdowns, hospitalization, and long-term distress. These are direct permalinks to threads where people—or their loved ones—describe what happened.

They are anecdotal. Many contain detailed descriptions of mental-health crises, so there is no reason to read them just to prove to yourself that you can.''',
'''I’m putting the worst accounts down here instead of making the whole article one long horror story. They are anecdotes, not incidence data, but I don’t want to hide them either. These are direct links to people—or their loved ones—describing severe breakdowns, hospitalization, and long-term distress.

Some are rough to read. If you already got the point, there is no virtue in making yourself read all nine.'''
),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'expected exactly one replacement target, found {count}: {old[:80]!r}')
    text = text.replace(old, new, 1)

OUT.write_text(text, encoding='utf-8')
print(OUT)
