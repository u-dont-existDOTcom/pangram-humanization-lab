#!/usr/bin/env python3
import runpy
from pathlib import Path

runpy.run_path('scripts/apply_spiritual_bypassing_r05.py', run_name='__main__')
source=Path('/tmp/spiritual-bypassing-r05.md')
out=Path('/tmp/spiritual-bypassing-r06.md')
text=source.read_text(encoding='utf-8')

replacements=[
(
'''That doesn’t mean the retreats don’t help people. Obviously they do. If one helped you, I’m not trying to explain your own experience away. And if one hurt you, you don’t owe anybody the interpretation that you should have pushed through a “dark night.” I put the ugliest survivor accounts at the bottom; skip them if you don’t need them.''',
'''A lot of people love these retreats. I’m not asking them to reinterpret what happened. The same goes for people who were harmed: I’m not going to rename it a “dark night” they should have pushed through. The worst accounts are at the bottom, and they’re optional.'''
),
(
'''The method doesn’t suddenly become trauma therapy. The instruction is still to observe and not react. Maybe that is fine when what is coming up stays within what you can handle. If somebody is coming apart, I don’t understand why more non-reaction is automatically the answer.

People on [r/vipassana](http://Reddit.com/r/vipassana) describe exactly this kind of “dark night” material surfacing. Critics say the retreat culture can become “push through,” and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Eventually something can seize up.

This is where I worry about spiritual bypassing. Not reacting can start to feel virtuous even when reacting—by asking for help, changing course, or stopping—is exactly what makes sense. The same thing can happen outside a retreat when people ignore injustice and call it inner peace. Remember some of the Buddhist responses to the Myanmar coup?

This is why I keep wondering why metta doesn’t come first.''',
'''If somebody starts dissociating on day five, the instructions don’t turn into trauma therapy. They’re still practicing observation and non-reaction. And if I’m the one coming apart, I don’t want the fact that I’m reacting to become one more thing I’m failing at.

People on [r/vipassana](http://Reddit.com/r/vipassana) describe this kind of “dark night” material surfacing. Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Eventually something can seize up.

That is spiritual bypassing to me. Sometimes the sensible reaction is to ask for help, change course, or stop. Sometimes the sensible reaction to injustice isn’t inner peace either. Remember some of the Buddhist responses to the Myanmar coup?

This is why I keep wondering why metta doesn’t come first.'''
),
(
'''If I were choosing, the first thing I’d want to know is what the teacher does when I say, “This is making me worse.” A metta-heavy retreat might fit. Trauma-informed mindfulness might. Mindfulness-Based Stress Reduction alongside therapy might.''',
'''I’d probably look first for a metta-heavy retreat or a teacher who actually knows trauma. Mindfulness-Based Stress Reduction alongside therapy is another option. What I’d really want to know is what happens when I tell the teacher, “This is making me worse.”'''
),
]

for old,new in replacements:
    count=text.count(old)
    if count != 1:
        raise SystemExit(f'expected one r06 target, found {count}: {old[:80]!r}')
    text=text.replace(old,new,1)
out.write_text(text,encoding='utf-8')
print(out)
