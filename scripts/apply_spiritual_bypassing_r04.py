#!/usr/bin/env python3
import runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r03.py', run_name='__main__')
source = Path('/tmp/spiritual-bypassing-r03.md')
out = Path('/tmp/spiritual-bypassing-r04.md')
text = source.read_text(encoding='utf-8')

replacements = [
(
'''Hey lovey bunnies. Goenka retreats are one of those things where people can do the same ten days and sound like they went to different planets. Some come out saying it changed their life. Some come out badly destabilized.

So I’m not going to tell anybody what their retreat “really” was. If it helped you, great. If it hurt you, I’m definitely not going to tell you the harm was a “dark night” you should have pushed through. What I want to look at is what happens when a method whose main instruction is not to react runs into a nervous system that may have very good reasons for reacting.

This is sensitive territory too. Read as much or as little as is useful to you. You don’t owe a meditation method your trust because it is old, Buddhist, or worked beautifully for somebody else.

For me, healing starts with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com).''',
'''Goenka retreats scare me a little. Not because everybody has a bad time—lots of people love them—but because when they go wrong they can go really, really wrong, and the answer can still be some version of “keep observing.”

I know some people reading this had beautiful experiences there. I’m not trying to take that away from you. And if yours was awful, you don’t need to read the survivor stories at the bottom just so I can convince you it was awful. I’m trying to understand what the method is asking a traumatized nervous system to do.

You can read this the same way: keep whatever helps and leave the rest. A practice being old, Buddhist, or life-changing for somebody else doesn’t mean you owe it your trust.

For me, healing starts with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com).'''
),
(
'''Ten days of silence. You scan body sensations while old *sankharas*—mental habits—surface, and whatever happens you practice not reacting. Lots of people love this. They come away with more discipline and a real taste of equanimity.

It is also a lot to throw at somebody.''',
'''A Goenka retreat gives you ten silent days to watch your body closely. Old *sankharas*—mental habits—come up; the practice is not to react to them. That can be powerful. It can also surface a ridiculous amount of material before you have any idea what to do with it.'''
),
(
'''The accounts I found on Reddit include someone becoming dissociated after a near-death sensation, somebody whose OCD and violent thoughts intensified, and a family member becoming manic after being sent home early. I left those links at the end.

If this is close to home for you, you can skip that postscript. The point does not depend on reading nine frightening stories in a row.

What bothers me isn’t that old stuff can come up. That is partly the point. It’s that the basic instruction stays the same no matter what comes up: observe it and don’t react. If what is surfacing is manageable, maybe that is exactly useful. If somebody is starting to dissociate or come apart, I’m not convinced more non-reaction is what they need.

That worry isn’t theoretical. [r/vipassana](http://Reddit.com/r/vipassana) has plenty of people describing “dark night” experiences after buried material came up. Retreat centers already screen people out because they know some nervous systems are at higher risk. Critics say that once somebody is inside, though, the culture can still become “push through.” Some teachers warn that doing this without emotional groundwork is like revving an engine without oil. Eventually something can seize up.

That is also where I think spiritual bypassing can sneak in. Equanimity is useful. Using equanimity to sidestep the emotional mess is something else. So is ignoring injustice and calling that inner peace. Remember some of the Buddhist responses to the Myanmar coup?

Which leaves me with the question I actually care about: why not teach people how to meet suffering with love before asking them to sit inside it for ten days?''',
'''The accounts I found on Reddit include someone becoming dissociated after a near-death sensation, somebody whose OCD and violent thoughts intensified, and a family member becoming manic after being sent home early. I put those links at the end.

The part I can’t get past is the screening rule. If destabilization is serious enough that people with a recent history of mental instability aren’t allowed in, what happens when somebody who passed the screening starts destabilizing anyway?

The main tool is still the same: observe and don’t react. If what comes up is manageable, fine. But if somebody is dissociating or coming apart, I don’t see why more non-reaction is automatically the answer.

[r/vipassana](http://Reddit.com/r/vipassana) has plenty of people describing “dark night” experiences after buried material came up. Critics say the retreat culture can still become “push through.” Some teachers warn that doing this without emotional groundwork is like revving an engine without oil. Eventually something can seize up.

Spiritual bypassing is the other side of the same problem for me. Equanimity is good. Equanimity used to avoid the emotional mess isn’t. Neither is ignoring injustice and calling it inner peace. Remember some of the Buddhist responses to the Myanmar coup?

So why not teach people how to meet suffering with love before asking them to sit inside it for ten days?'''
),
(
'''The Buddha didn’t treat kindness as something you tack on after the hard part. In suttas like the [Metta Sutta or MN 118](https://suttacentral.net/snp1.8/en/mills?lang=en), the practice is almost embarrassingly simple: wish beings ease and happiness. Yourself too. Metta is a prelim to vipassana because it calms the hindrances and builds goodwill. It lets you want suffering to end without that wish turning into desperation or fear that you’ll fail.''',
'''Metta itself is simple: wish ease and happiness for beings, including yourself. That’s what the [Metta Sutta or MN 118](https://suttacentral.net/snp1.8/en/mills?lang=en) is about. It calms the hindrances and builds goodwill, and it lets you want suffering to end without that wish turning into desperation or fear of failure. That is why I think it belongs before vipassana.'''
),
(
'''[Goenka](http://Dhamma.org) does include metta, but basically at the finish line: briefly on day ten, mainly to share merit. That feels backwards to me.''',
'''Goenka waits until day ten to bring [metta](http://Dhamma.org) in, briefly, mainly to share merit. That feels backwards to me.'''
),
(
'''I’m putting the worst accounts down here instead of making the whole article one long horror story. They are anecdotes, not incidence data, but I don’t want to hide them either. These are direct links to people—or their loved ones—describing severe breakdowns, hospitalization, and long-term distress.

Some are rough to read. If you already got the point, there is no virtue in making yourself read all nine.''',
'''I’m putting the worst accounts down here instead of making the whole article one long horror story. They’re anecdotes, not incidence data. Some are rough. Skip them if you don’t need them.'''
),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'expected one r04 target, found {count}: {old[:80]!r}')
    text = text.replace(old, new, 1)

out.write_text(text, encoding='utf-8')
print(out)
