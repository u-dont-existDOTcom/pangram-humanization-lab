#!/usr/bin/env python3
import runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r05.py', run_name='__main__')
source=Path('/tmp/spiritual-bypassing-r05.md')
out=Path('/tmp/spiritual-bypassing-r07.md')
text=source.read_text(encoding='utf-8')
replacements=[
(
'''That doesn’t mean the retreats don’t help people. Obviously they do. If one helped you, I’m not trying to explain your own experience away. And if one hurt you, you don’t owe anybody the interpretation that you should have pushed through a “dark night.” I put the ugliest survivor accounts at the bottom; skip them if you don’t need them.''',
'''Some people love Goenka retreats. I also know people who came out in pieces. Both are real. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.'''
),
(
'''The screening policy is what makes this so strange to me. The centers already accept that some people are too vulnerable for the retreat. But screening can’t tell you everything that is going to surface. So what happens when somebody who looked stable on the application starts dissociating on day five?

The method doesn’t suddenly become trauma therapy. The instruction is still to observe and not react. Maybe that is fine when what is coming up stays within what you can handle. If somebody is coming apart, I don’t understand why more non-reaction is automatically the answer.

People on [r/vipassana](http://Reddit.com/r/vipassana) describe exactly this kind of “dark night” material surfacing. Critics say the retreat culture can become “push through,” and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Eventually something can seize up.

This is where I worry about spiritual bypassing. Not reacting can start to feel virtuous even when reacting—by asking for help, changing course, or stopping—is exactly what makes sense. The same thing can happen outside a retreat when people ignore injustice and call it inner peace. Remember some of the Buddhist responses to the Myanmar coup?

This is why I keep wondering why metta doesn’t come first.''',
'''Screening is already an admission that “observe and don’t react” is not equally safe for everybody. That is the part I can’t get around. A questionnaire can’t know everything that is going to surface once somebody is inside.

So say I start dissociating on day five. Telling me to keep observing isn’t neutral. Maybe it helps; maybe it makes things worse. What I really don’t want is for the fact that I’m reacting to become evidence that I need to practice non-reaction harder.

There are plenty of these “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana). Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up.

That is where vipassana can turn into spiritual bypassing for me. Sometimes you should react. Ask for help. Change course. Leave. And sometimes equanimity outside a retreat can become a reason not to react to what is happening around you. Remember some of the Buddhist responses to the Myanmar coup?

I would rather have people learn how to meet suffering with love before any of that starts.'''
),
(
'''If I were choosing, the first thing I’d want to know is what the teacher does when I say, “This is making me worse.” A metta-heavy retreat might fit. Trauma-informed mindfulness might. Mindfulness-Based Stress Reduction alongside therapy might.

[Insight Meditation Society](http://dharma.org) and [Plum Village](http://plumvillage.org) are two places I’d look, but I’d still ask: What if I start dissociating? What if I need to stop?

You can stop. A teacher, a retreat center, or Buddhism itself doesn’t get to overrule that for you. Your path is yours to shape.''',
'''I’d start with metta. If I still wanted a retreat, I’d talk to a teacher who understands trauma before committing to ten silent days. I’d ask what happens if I start dissociating or need to leave. [Insight Meditation Society](http://dharma.org) and [Plum Village](http://plumvillage.org) are two places I’d look. Mindfulness-Based Stress Reduction alongside therapy is another route.

And if the practice is destabilizing you, stop. I mean that literally. A teacher, a retreat center, or Buddhism itself doesn’t get to overrule that for you. Your path is yours to shape.'''
),
]
for old,new in replacements:
    count=text.count(old)
    if count != 1:
        raise SystemExit(f'expected one r07 target, found {count}: {old[:80]!r}')
    text=text.replace(old,new,1)
out.write_text(text,encoding='utf-8')
print(out)
