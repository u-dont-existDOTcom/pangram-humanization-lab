#!/usr/bin/env python3
import runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r04.py', run_name='__main__')
source = Path('/tmp/spiritual-bypassing-r04.md')
out = Path('/tmp/spiritual-bypassing-r05.md')
text = source.read_text(encoding='utf-8')

replacements = [
(
'''Goenka retreats scare me a little. Not because everybody has a bad time—lots of people love them—but because when they go wrong they can go really, really wrong, and the answer can still be some version of “keep observing.”

I know some people reading this had beautiful experiences there. I’m not trying to take that away from you. And if yours was awful, you don’t need to read the survivor stories at the bottom just so I can convince you it was awful. I’m trying to understand what the method is asking a traumatized nervous system to do.

You can read this the same way: keep whatever helps and leave the rest. A practice being old, Buddhist, or life-changing for somebody else doesn’t mean you owe it your trust.

For me, healing starts with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com).''',
'''I have a problem with Goenka retreats that I wish somebody had explained to me earlier: the people most likely to be destabilized are screened out, but the people who get in are still taught basically one response to whatever surfaces—observe it and don’t react.

That doesn’t mean the retreats don’t help people. Obviously they do. If one helped you, I’m not trying to explain your own experience away. And if one hurt you, you don’t owe anybody the interpretation that you should have pushed through a “dark night.” I put the ugliest survivor accounts at the bottom; skip them if you don’t need them.

My bias here is that healing starts with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com).'''
),
(
'''A Goenka retreat gives you ten silent days to watch your body closely. Old *sankharas*—mental habits—come up; the practice is not to react to them. That can be powerful. It can also surface a ridiculous amount of material before you have any idea what to do with it.''',
'''A Goenka retreat is ten silent days of watching the body while old *sankharas*—mental habits—come up. The practice is to notice the sensations without reacting. Sometimes that is powerful. Sometimes an awful lot comes up at once.'''
),
(
'''The accounts I found on Reddit include someone becoming dissociated after a near-death sensation, somebody whose OCD and violent thoughts intensified, and a family member becoming manic after being sent home early. I put those links at the end.

The part I can’t get past is the screening rule. If destabilization is serious enough that people with a recent history of mental instability aren’t allowed in, what happens when somebody who passed the screening starts destabilizing anyway?

The main tool is still the same: observe and don’t react. If what comes up is manageable, fine. But if somebody is dissociating or coming apart, I don’t see why more non-reaction is automatically the answer.

[r/vipassana](http://Reddit.com/r/vipassana) has plenty of people describing “dark night” experiences after buried material came up. Critics say the retreat culture can still become “push through.” Some teachers warn that doing this without emotional groundwork is like revving an engine without oil. Eventually something can seize up.

Spiritual bypassing is the other side of the same problem for me. Equanimity is good. Equanimity used to avoid the emotional mess isn’t. Neither is ignoring injustice and calling it inner peace. Remember some of the Buddhist responses to the Myanmar coup?

So why not teach people how to meet suffering with love before asking them to sit inside it for ten days?''',
'''The accounts I found on Reddit include someone becoming dissociated after a near-death sensation, somebody whose OCD and violent thoughts intensified, and a family member becoming manic after being sent home early. I put those links at the end.

The screening policy is what makes this so strange to me. The centers already accept that some people are too vulnerable for the retreat. But screening can’t tell you everything that is going to surface. So what happens when somebody who looked stable on the application starts dissociating on day five?

The method doesn’t suddenly become trauma therapy. The instruction is still to observe and not react. Maybe that is fine when what is coming up stays within what you can handle. If somebody is coming apart, I don’t understand why more non-reaction is automatically the answer.

People on [r/vipassana](http://Reddit.com/r/vipassana) describe exactly this kind of “dark night” material surfacing. Critics say the retreat culture can become “push through,” and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Eventually something can seize up.

This is where I worry about spiritual bypassing. Not reacting can start to feel virtuous even when reacting—by asking for help, changing course, or stopping—is exactly what makes sense. The same thing can happen outside a retreat when people ignore injustice and call it inner peace. Remember some of the Buddhist responses to the Myanmar coup?

This is why I keep wondering why metta doesn’t come first.'''
),
(
'''Metta itself is simple: wish ease and happiness for beings, including yourself. That’s what the [Metta Sutta or MN 118](https://suttacentral.net/snp1.8/en/mills?lang=en) is about. It calms the hindrances and builds goodwill, and it lets you want suffering to end without that wish turning into desperation or fear of failure. That is why I think it belongs before vipassana.''',
'''In the [Metta Sutta or MN 118](https://suttacentral.net/snp1.8/en/mills?lang=en), you wish ease and happiness to beings, yourself included. Metta calms the hindrances and builds goodwill. It also lets you want suffering to end without that wish turning into desperation or fear of failure.'''
),
(
'''Theravada and most Mahayana Buddhist traditions treat metta as essential groundwork before the deeper work of [unweaving the sense streams](http://nibbana.u-dont-exist.com) that make up the mind.

Goenka waits until day ten to bring [metta](http://Dhamma.org) in, briefly, mainly to share merit. That feels backwards to me. It skips the Buddha’s kindness-first approach, which he taught was necessary to bring the mind to a state ready for real [nibbana](http://nibbana.u-dont-exist.com) meditation. The kindness I would most want available when somebody’s trauma starts surfacing arrives after nine days of the intense part.''',
'''Theravada and most Mahayana Buddhist traditions treat metta as essential groundwork before the deeper work of [unweaving the sense streams](http://nibbana.u-dont-exist.com) that make up the mind.

Goenka puts [metta](http://Dhamma.org) on day ten. Briefly. Mostly to share merit. I think that’s backwards. It skips the Buddha’s kindness-first approach, which he taught was necessary to bring the mind to a state ready for real [nibbana](http://nibbana.u-dont-exist.com) meditation. By the time the kindness I’d want available when trauma surfaces arrives, nine days of the intense part are already over.'''
),
(
'''Personally, I would care less about the lineage and more about what the teacher does when I say, “This is making me worse.” Maybe a metta-heavy retreat fits. Maybe trauma-informed mindfulness does. Mindfulness-Based Stress Reduction alongside therapy may fit better for some people. [Insight Meditation Society](http://dharma.org) and [Plum Village](http://plumvillage.org) are two places I would look.

And I would ask them directly: What happens if I start dissociating? What if I need to stop? Do you treat that as information, or as resistance I’m supposed to push through? A good name is not a reason to hand over your judgment.

If something is destabilizing you, you are allowed to stop. Your path is yours to shape.''',
'''If I were choosing, the first thing I’d want to know is what the teacher does when I say, “This is making me worse.” A metta-heavy retreat might fit. Trauma-informed mindfulness might. Mindfulness-Based Stress Reduction alongside therapy might.

[Insight Meditation Society](http://dharma.org) and [Plum Village](http://plumvillage.org) are two places I’d look, but I’d still ask: What if I start dissociating? What if I need to stop?

You can stop. A teacher, a retreat center, or Buddhism itself doesn’t get to overrule that for you. Your path is yours to shape.'''
),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'expected one r05 target, found {count}: {old[:80]!r}')
    text = text.replace(old, new, 1)

out.write_text(text, encoding='utf-8')
print(out)
