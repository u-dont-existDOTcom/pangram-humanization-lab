#!/usr/bin/env python3
import runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r07.py', run_name='__main__')
source=Path('/tmp/spiritual-bypassing-r07.md')
out=Path('/tmp/spiritual-bypassing-r08.md')
text=source.read_text(encoding='utf-8')
replacements=[
(
'''Screening is already an admission that “observe and don’t react” is not equally safe for everybody. That is the part I can’t get around. A questionnaire can’t know everything that is going to surface once somebody is inside.

So say I start dissociating on day five. Telling me to keep observing isn’t neutral. Maybe it helps; maybe it makes things worse. What I really don’t want is for the fact that I’m reacting to become evidence that I need to practice non-reaction harder.

There are plenty of these “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana). Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up.''',
'''That leaves the question the application can’t answer. If I start dissociating on day five, how am I supposed to tell the difference between “something difficult is coming up” and “this is actually making me worse”? I don’t want the fact that I’m reacting to become evidence that I need to practice non-reaction harder.

There are plenty of “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana). Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up.'''
),
(
'''I’d start with metta. If I still wanted a retreat, I’d talk to a teacher who understands trauma before committing to ten silent days. I’d ask what happens if I start dissociating or need to leave. [Insight Meditation Society](http://dharma.org) and [Plum Village](http://plumvillage.org) are two places I’d look. Mindfulness-Based Stress Reduction alongside therapy is another route.

And if the practice is destabilizing you, stop. I mean that literally. A teacher, a retreat center, or Buddhism itself doesn’t get to overrule that for you. Your path is yours to shape.''',
'''I’d start with metta. If I wanted more, I’d look for trauma-informed mindfulness—maybe Mindfulness-Based Stress Reduction with a therapist—before jumping into ten silent days. If I still wanted a retreat, I’d call [Insight Meditation Society](http://dharma.org) or [Plum Village](http://plumvillage.org) and ask what happens if I start dissociating or need to leave.

And if the practice were destabilizing me, I’d stop. I wouldn’t wait for a teacher, a retreat center, or Buddhism to give me permission. Your path is yours to shape.'''
),
]
for old,new in replacements:
    count=text.count(old)
    if count != 1:
        raise SystemExit(f'expected one r08 target, found {count}: {old[:80]!r}')
    text=text.replace(old,new,1)
out.write_text(text,encoding='utf-8')
print(out)
