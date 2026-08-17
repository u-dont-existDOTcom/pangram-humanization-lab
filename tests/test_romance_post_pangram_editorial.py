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


def test_after_leaving_uses_aug17_owner_correction_and_preserves_continuation() -> None:
    output = _assemble()
    start = output.index("## After leaving")
    end = output.index("## What I gained from loss")
    after = output[start:end]

    assert "Make sure to look at yourself as much as you look at them, to see what you honestly contributed to the problems." in after
    assert "Try to see your ex's perspective in so far as it may have had some kernels of truth, including their own internal conflicts, rather than one-dimensionalizing them." in after
    assert "Seeing them now doesn’t automatically mean you are demonizing the other person." not in after
    assert "Try to see the situation from their perspective. Try to see where they may be internally conflicted." not in after

    owner_stop = "Avoid the New Age belief that everyone is simply a mirror of you. No, that isn’t true."
    continuation = "We partly mirror one another, but each person is also their own unique person"
    assert after.index(owner_stop) < after.index(continuation)
    assert "What would Mr. Rogers do?" in after


def test_card_game_closeness_is_not_treated_as_lived_evidence() -> None:
    output = _assemble()
    game = "A card game can create its own little high too."
    limit = "That may mean the game worked without telling us whether the relationship will."
    ordinary = "At some point, more questions mostly teach me what the person says about themself. Then I need ordinary time."
    assert game in output
    assert limit in output
    assert ordinary in output
    assert output.index(game) < output.index(limit) < output.index(ordinary)
    assert "I can learn a lot by talking, but there's a point where more questions mostly teach me" not in output


def test_shared_reality_seed_precedes_two_pillars_primary_home() -> None:
    output = _assemble()
    seed = "By community, I don't mean that she tells her friends her side while I tell mine."
    primary = "# Two Pillars Don't Hold The Roof Up"
    assert seed in output
    assert "the relationship isn't the only reality in the room" in output
    assert output.index("## Things get tricky fast") < output.index(seed) < output.index(primary)


def test_readiness_names_inner_parenting_and_literal_parenthood_without_lowering_floor() -> None:
    output = _assemble()
    early = "If you can't be a parent in either sense, you aren't ready to date."
    callback = "Nobody has to be completely healed before entering a relationship."
    standards = "Other people will have different standards above that minimum."
    minimum = "At the very least, there needs to be honesty, real effort at improving, and some ability to stop blaming everybody else for your own problems."
    reparent = "The present-day adult has to learn how to parent the child part instead of quietly hiring the partner for the job."
    assert early in output
    assert callback in output
    assert standards in output
    assert minimum in output
    assert reparent in output
    assert output.index(early) < output.index(callback) < output.index(standards) < output.index(minimum) < output.index(reparent)


def test_bundling_is_compact_historical_example_not_causal_claim() -> None:
    output = _assemble()
    start = output.index("Modern life barely has an intermediate stage between being interested in somebody and getting sexually entangled.")
    end = output.index("# Starting on the right foot")
    bundling = output[start:end]
    assert "https://doi.org/10.1093/maghis/18.4.9" in bundling
    assert "a mostly extinct practice now especially associated with the Amish even though it existed much more widely" in bundling
    assert "bundling coexisted with a lot of premarital pregnancy" in bundling
    assert "30–40 percent of brides were already pregnant" in bundling
    assert "hardly a perfect containment system" in bundling
    assert "bundling caused" not in bundling.lower()
    assert len(bundling.split()) < 150


def test_idealization_bridges_spiritual_depth_to_ordinary_dependability() -> None:
    output = _assemble()
    bridge = "Spiritual depth also doesn't tell me how dependable somebody is."
    ordinary = "She may meditate for two hours and still not show up for boring work, sickness, or something she promised yesterday."
    flaws = "## The conversation about flaws"
    assert bridge in output
    assert ordinary in output
    assert output.index("## Beware idealization in either direction") < output.index(bridge) < output.index(flaws)


def test_crucible_does_not_absorb_unilateral_coercion_into_mutual_triggering() -> None:
    output = _assemble()
    start = output.index("# Are you ready for the crucible?")
    end = output.index("# Don’t make your partner your whole world")
    crucible = output[start:end]
    warning = "sometimes this isn't two wounded people triggering each other"
    safety = "Get other people involved and think about safety first."
    resumed = "Relationship showed me how vulnerable I actually am when I open my heart."
    assert warning in crucible
    assert "Sometimes one person is terrorizing or controlling the other." in crucible
    assert safety in crucible
    assert resumed in crucible
    assert crucible.index(warning) < crucible.index(safety) < crucible.index(resumed)
    assert "It showed me how vulnerable I actually am when I open my heart." not in crucible


def test_labels_reveal_shared_meaning_without_creating_commitment() -> None:
    output = _assemble()
    assert "labels don't create commitment" in output
    assert "They can still expose whether two people think they're in the same relationship" in output
    assert "True commitment grows out of relational depth, not a label." in output
    assert "labels don't actually change anything" not in output


def test_bee_door_keeps_lying_and_adds_context() -> None:
    output = _assemble()
    start = output.index("# If you’re already in it")
    end = output.index("# Children")
    section = output[start:end]
    assert "Why would she lie like that? She was lying" in section
    assert "“she lied” only named the momentary behavior" in section
    assert "There was no strategy behind it, and she was usually quite honest." in section
    assert "some kind of mental illness" in section
    assert "rather than \"lying\"" not in section


def test_vows_heading_changes_without_rewriting_existing_action_feeling_distinction() -> None:
    output = _assemble()
    assert "## Which marriage vows are honest?" in output
    assert "## Why marriage vows are dishonest" not in output
    assert "Conventional marriage vows are dishonest, and most people know it." in output
    assert "You can't promise how you'll feel in the future. You can promise actions if you really believe you're capable of delivering them." in output
    assert "Ecclesiastes 5:4–6" in output
    assert "Sexual exclusivity has a different history." in output


def test_mdma_warning_precedes_attractive_psychedelic_material_and_preserves_sober_test() -> None:
    output = _assemble()
    start = output.index("## Psychedelics in relationship discernment")
    end = output.index("## Why all of this sounds artificial")
    section = output[start:end]
    warning = "You cannot negotiate consent on MDMA."
    positive = "Psychedelics, especially certain types of shrooms"
    state = "In neuroscience, this is called state-dependent learning."
    sober = "The question is what happens when you're sober again."
    assert warning in section
    assert "Advance planning doesn't turn getting high and starting a relationship into a safe procedure." in section
    assert section.index(warning) < section.index(positive) < section.index(state) < section.index(sober)


def test_explicit_no_change_locks_survive_concept_flow_pass() -> None:
    output = _assemble()
    oxytocin = (
        "People call oxytocin the “love hormone,” as if getting more attached should make you feel closer and safer. "
        "If closeness was safe when you were little, maybe it does feel a bit like coming home. But if it came with neglect, "
        "abuse, or if people disappeared on you, you can get more attached and more freaked out at the same time."
    )
    cervical = (
        "Komisaruk and Whipple showed that cervical stimulation can produce orgasm even in women with a severed spinal cord, "
        "because the vagus nerve can carry the signal without using the spinal route that clitoral orgasms use."
    )
    promoter = "Kim Anami, Diana Richardson, and other popular educators and promoters of cervical orgasms further claim"
    assert oxytocin in output
    assert cervical in output
    assert promoter in output
