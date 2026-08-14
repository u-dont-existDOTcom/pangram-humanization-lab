#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/experiments/spiritual-bypassing-invitation-batch-2026-08-13-results.json"
OUT = Path("/tmp/spiritual-bypassing-visible-boundary-r07-2026-08-14.json")
AUDIT_ID = "spiritual-bypassing-visible-boundary-2026-08-14"
EXPECTED_R6_SHA = "ec5a59dfd61d3cc3263ccff836a935d12104c85ab9d64f2707026a363ab2f4e9"

OLD_OPEN = """I have a problem with Goenka retreats: people with a recent history of mental instability are screened out, but the people who get in are still taught basically one response to whatever surfaces—observe it and don’t react.

Some people love Goenka retreats. I also know people who came out in pieces. Both are real. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.

My bias here is that healing starts with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com)."""

NEW_OPEN = """I’m using Goenka retreats as the clearest example here, but the problem is bigger than Goenka. A spiritual practice can help us face pain, or it can become a way to get above the pain without actually healing it.

If you love Goenka retreats, I’m not asking you to decide that your experience was fake. I know people who loved them too. I also know people who came out in pieces. I want to leave room for both while asking one question: when something starts going seriously wrong inside you, how do you know whether non-reaction is helping you or teaching you to ignore a warning?

That question matters because people with a recent history of mental instability are screened out, while the people who get in are still taught basically one response to whatever surfaces—observe it and don’t react. I put the survivor accounts at the bottom so you can skip them if you already know what this kind of harm looks like.

My bias is that healing starts with learning how to be kind to the parts of us that hurt. That is what I mean by [inner-child self love reparenting](http://Innerchild.u-dont-exist.com)."""

OLD_DAY = """Day five is where I get stuck. Suppose I’m dissociating. Am I supposed to read that as a warning, or as another reaction to observe without reacting?

There are plenty of “dark night” accounts on [r/vipassana](http://Reddit.com/r/vipassana). Critics describe a “push through” culture, and some teachers compare intense practice without emotional groundwork to revving an engine without oil. Things can seize up."""

NEW_DAY = """By day five, that question stops being theoretical for me. If I start dissociating, I don’t know how the instruction tells me whether this is a warning or simply another reaction I should observe without reacting.

People on [r/vipassana](http://Reddit.com/r/vipassana) write about plenty of “dark nights,” and critics describe a culture of pushing through. That ambiguity is what bothers me. Some teachers compare intense practice without emotional groundwork to revving an engine without oil. Sometimes the useful response to a warning light is to stop revving it."""

OLD_TAIL = """- **[A story about someone becoming suicidal after a retreat, beginning with escalating anxiety](https://www.reddit.com/r/Buddhism/comments/a6m9z8/i_have_read_a_story_about_a_person_who_went_into/):** Users recount Goenka retreats causing deep depression, nihilism, and unprocessed trauma surfacing as suicidal ideation.

- **A retreat ending in psychosis—or a dark night—with three-dimensional hallucinations and psychiatric commitment:** [This detailed personal log](https://www.dharmaoverground.org/discussion/-/message_boards/message/16879352) describes jhana-like states turning into a breakdown on day ten, with mixed techniques exacerbating the crisis.

- **Severe harm to mental health through an exacerbation of OCD:** [The original poster explains](https://www.reddit.com/r/vipassana/comments/1d25cj6/vipassana_retreats_severely_harm_my_mental_health/) how retreats intensified intrusive thoughts and compulsions to a debilitating level and advises caution for people with similar conditions."""

NEW_TAIL = """- **[A story about someone becoming suicidal after a retreat, beginning with escalating anxiety](https://www.reddit.com/r/Buddhism/comments/a6m9z8/i_have_read_a_story_about_a_person_who_went_into/):** The anxiety kept escalating until the person became suicidal. People in the thread also describe deep depression, nihilism, and unprocessed trauma surfacing into suicidal thinking.

- **A retreat ending in psychosis—or a dark night—with three-dimensional hallucinations and psychiatric commitment:** [This detailed personal log](https://www.dharmaoverground.org/discussion/-/message_boards/message/16879352) starts with jhana-like states and ends with a breakdown on day ten. The writer thought mixing techniques may have made things worse.

- **Severe harm to mental health through an exacerbation of OCD:** [The original poster explains](https://www.reddit.com/r/vipassana/comments/1d25cj6/vipassana_retreats_severely_harm_my_mental_health/) that the retreat drove their intrusive thoughts and compulsions to a debilitating level. They warn people with similar conditions to be careful."""


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
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    selected = next(row for row in source["results"] if row["id"] == "OWNER_B_MINIMAL_COMPRESS_FULL")
    if selected["text_sha256"] != EXPECTED_R6_SHA:
        raise SystemExit(f"r6 hash mismatch: {selected['text_sha256']}")
    base = selected["text"]
    repaired = replace_once(base, OLD_OPEN, NEW_OPEN, "opening")
    repaired = replace_once(repaired, OLD_DAY, NEW_DAY, "day-five")
    repaired = replace_once(repaired, OLD_TAIL, NEW_TAIL, "survivor-tail")

    control_visible = visible_text(base)
    repaired_visible = visible_text(repaired)
    if len(control_visible.split()) != 1482:
        raise SystemExit(f"visible control word count drift: {len(control_visible.split())}")

    candidate = ROOT / "state/candidates/spiritual-bypassing-r07-invitational-visible-repair.md"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(repaired, encoding="utf-8")

    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "spiritual-bypassing-visible-boundary-r07-2026-08-14",
        "audit_id": AUDIT_ID,
        "variants": [
            {"id": "VISIBLE_CONTROL_R06", "section_id": "FULL_ARTICLE", "text": control_visible},
            {"id": "INVITATIONAL_REPAIR_R07", "section_id": "FULL_ARTICLE", "text": repaired_visible},
        ],
    }
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "control_words": len(control_visible.split()),
        "control_sha256": hashlib.sha256(control_visible.encode()).hexdigest(),
        "repaired_words": len(repaired_visible.split()),
        "repaired_sha256": hashlib.sha256(repaired_visible.encode()).hexdigest(),
        "candidate": str(candidate.relative_to(ROOT)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
