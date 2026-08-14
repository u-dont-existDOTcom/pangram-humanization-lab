#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/candidates/spiritual-bypassing-r09-owner-invitational-opening.md"
OUT = Path("/tmp/spiritual-bypassing-visible-boundary-r10-2026-08-14.json")
AUDIT_ID = "spiritual-bypassing-visible-owner-repair-2026-08-14"

OLD_DAY = """Day five is where I get stuck. Suppose I’m dissociating. Am I supposed to read that as a warning, or as another reaction to observe without reacting?

There are plenty of “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana). Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up."""

NEW_DAY = """Day five is where I get stuck. If I’m dissociating, is that a sign to stop or just another reaction I’m supposed to observe? I don’t see how the instruction itself tells me.

There are plenty of “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana), and critics describe a “push through” culture. Some teachers compare intense practice without emotional groundwork to revving an engine without oil."""

REPLACEMENTS = [
    (
        """- **[Anxiety about attending a first retreat after reading accounts of psychosis, depression, and suicidal thoughts](https://www.reddit.com/r/vipassana/comments/15xd21v/im_about_to_go_in_my_first_10_day_vipassana/):** The thread includes people sharing or referring to breakdowns, emotional storms, and deep pain after buried trauma resurfaced.""",
        """- **[Anxiety about attending a first retreat after reading accounts of psychosis, depression, and suicidal thoughts](https://www.reddit.com/r/vipassana/comments/15xd21v/im_about_to_go_in_my_first_10_day_vipassana/):** One person was about to attend their first retreat and got scared after reading those accounts. Replies include people talking about breakdowns and buried trauma coming up hard.""",
    ),
    (
        """- **Risks of intensive retreats such as Goenka’s, including psychosis and bad-trip-like experiences:** [Users describe](https://www.reddit.com/r/Wakingupapp/comments/18o4t27/what_are_the_risks_of_an_intensive_retreat/) Goenka retreats triggering psychosis, with one person comparing a derailment on day five to a psychedelic crisis.""",
        """- **Risks of intensive retreats such as Goenka’s, including psychosis and bad-trip-like experiences:** [In this thread](https://www.reddit.com/r/Wakingupapp/comments/18o4t27/what_are_the_risks_of_an_intensive_retreat/), people describe psychosis after Goenka retreats. One person compares going off the rails on day five to a psychedelic crisis.""",
    ),
    (
        """- **[A story about someone becoming suicidal after a retreat, beginning with escalating anxiety](https://www.reddit.com/r/Buddhism/comments/a6m9z8/i_have_read_a_story_about_a_person_who_went_into/):** Users recount Goenka retreats causing deep depression, nihilism, and unprocessed trauma surfacing as suicidal ideation.""",
        """- **[A story about someone becoming suicidal after a retreat, beginning with escalating anxiety](https://www.reddit.com/r/Buddhism/comments/a6m9z8/i_have_read_a_story_about_a_person_who_went_into/):** The anxiety kept escalating until the person became suicidal. People in the thread also describe deep depression, nihilism, and unprocessed trauma coming up.""",
    ),
    (
        """- **Severe harm to mental health through an exacerbation of OCD:** [The original poster explains](https://www.reddit.com/r/vipassana/comments/1d25cj6/vipassana_retreats_severely_harm_my_mental_health/) how retreats intensified intrusive thoughts and compulsions to a debilitating level and advises caution for people with similar conditions.""",
        """- **Severe harm to mental health through an exacerbation of OCD:** [One poster says](https://www.reddit.com/r/vipassana/comments/1d25cj6/vipassana_retreats_severely_harm_my_mental_health/) the retreats made their OCD much worse, with intrusive thoughts and compulsions becoming debilitating. They warn people with similar conditions to be careful.""",
    ),
]


def visible_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()


def replace_once(text: str, old: str, new: str, name: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one {name} span, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    base = SOURCE.read_text(encoding="utf-8")
    repaired = replace_once(base, OLD_DAY, NEW_DAY, "day-five")
    for index, (old, new) in enumerate(REPLACEMENTS, start=1):
        repaired = replace_once(repaired, old, new, f"survivor-{index}")
    repaired_visible = visible_text(repaired)

    candidate = ROOT / "state/candidates/spiritual-bypassing-r10-visible-repair.md"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(repaired, encoding="utf-8")

    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "spiritual-bypassing-visible-boundary-r10-2026-08-14",
        "audit_id": AUDIT_ID,
        "variants": [
            {"id": "OWNER_OPEN_PLUS_VISIBLE_REPAIRS", "section_id": "FULL_ARTICLE", "text": repaired_visible}
        ],
    }
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "repaired_words": len(repaired_visible.split()),
        "repaired_sha256": hashlib.sha256(repaired_visible.encode()).hexdigest(),
        "candidate": str(candidate.relative_to(ROOT)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
