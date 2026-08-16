from __future__ import annotations

import json
from pathlib import Path

from scripts.assemble_romance_current import apply_operations


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = PROJECT_ROOT / "work" / "romance-current-assembly"


def _assemble() -> str:
    baseline = (WORK_ROOT / "baseline.md").read_text(encoding="utf-8")
    spec = json.loads((WORK_ROOT / "assembly-spec.json").read_text(encoding="utf-8"))
    output, _ = apply_operations(baseline, spec["operations"], WORK_ROOT)
    return output


def test_if_slow_uses_aug14_owner_recovery_lived_sequence() -> None:
    output = _assemble()
    start = output.index("## If slow isn’t realistic for you")
    end = output.index("### Slow steady may win the race, but turtles have problems too!")
    slow = output[start:end]

    assert "I pretty much always intend to wait long enough to have this conversation and figure out who I'm dealing with." in slow
    assert "I just want to please her" in slow
    assert "Masturbating first isn't such a good solution unless I'm the one initiating, and generally I'm not." in slow
    assert "My refractory period is too short for that to be effective for more than a short while anyway." in slow
    assert (
        "Since I know avoidance won't work every time, "
        "[Gandarussa](https://thediplomat.com/2013/09/a-male-contraceptive-pill-for-indonesia/) matters too."
    ) in slow
    assert "The evidence ranges, and nothing is 100 percent proven, but it looks quite effective as a male contraceptive." in slow
    assert "Would my twin flame behave like this?" in slow
    assert "Basically I need to stop one-dimensionalizing women as whoever they are in relation to me right now." in slow
    assert "I can know I want her much faster than I can know whether I want to raise children with her, live in community with her, or build a life with her." in slow

    assert "Men naturally love to please women" not in slow
    assert "Before meeting somebody you’re extremely attracted to, masturbate a lot." not in slow
    assert "safe birth-control options that work better than condoms" not in slow
    assert "The Bible also says something, I think, about marriage beginning when you sleep in the same tent together." not in slow


def test_if_slow_owner_recovery_places_entanglement_check_before_life_choice() -> None:
    output = _assemble()
    attached = "And once I'm attached, “I'm taking a chance on her” starts turning into “she's the right person”"
    checkin = "pick actual dates to ask how it's going"
    life = "I can know I want her much faster than I can know whether I want to raise children with her"
    special = "At some point one of you will ask, “Why am I special to you? Why are you with me and not somebody else?”"
    assert output.index(attached) < output.index(checkin) < output.index(life) < output.index(special)


def test_turtles_keeps_sex_fit_limit_without_generic_aftercare() -> None:
    output = _assemble()
    assert "Some of those things might get better if both partners are committed to helping each other through it. Sometimes bad sexual fit still feels like, “Let’s just be friends!”" in output
    assert "Saying, “The sex isn’t working for me,” may sound like, “I only love you if the sex is good.” But universal love doesn’t make someone special." in output
    assert "tomorrow’s not a given and every situation is unique" not in output
    assert "That conversation is hard because saying" not in output
    assert "I can still love you and not want to be in a romantic relationship with you." in output


def test_two_pillars_removes_thesis_aftercare_and_keeps_unique_lifetime_claim() -> None:
    output = _assemble()
    assert (
        "Romantic love can last, but it needs the right conditions, and community is one of them. "
        "Both people have to support it, and support from a community makes that much more realistic."
    ) not in output
    assert "Community isn’t magic either." not in output

    lifetime = "I do think romantic love can last for a lifetime."
    assert output.count(lifetime) == 1
    assert (
        "I just don't think two people should have to become each other's entire social world to keep it alive. "
        "So keep your friendships. They aren't automatically a threat to the relationship; "
        "they're part of what keeps you healthy enough to be in one."
    ) not in output

    practical_end = "two completely separate social worlds will automatically start taking sides when something goes wrong."
    next_heading = "# What are you actually choosing together?"
    assert output.index(practical_end) < output.index(lifetime) < output.index(next_heading)


def test_sexual_monogamy_paragraph_is_not_replaced_by_social_monogamy_analysis() -> None:
    output = _assemble()
    paragraph = (
        "Sexual exclusivity has a different history. Strict sexual exclusivity backed by law and social enforcement "
        "grew alongside agriculture, settled property, and inheritance, and became a mass norm during the Industrial "
        "Revolution. Tribal cultures across the world have generally had more flexible forms of primary partnership, "
        "or 'social monogamy,' with accepted ways for sexual or emotional connection to exist outside it."
    )
    assert paragraph in output
