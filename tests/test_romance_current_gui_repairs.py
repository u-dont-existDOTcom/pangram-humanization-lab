from __future__ import annotations

import json
from pathlib import Path

from scripts.assemble_romance_current import apply_operations


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work" / "romance-current-assembly"


def _assemble() -> str:
    baseline = (WORK / "baseline.md").read_text(encoding="utf-8")
    spec = json.loads((WORK / "assembly-spec.json").read_text(encoding="utf-8"))
    output, _ = apply_operations(baseline, spec["operations"], WORK)
    return output


def test_maturity_stops_after_roles_flip_before_default_caregiver_consequence() -> None:
    output = _assemble()
    kept = "The roles can flip, teacher one day, student the next. That’s healthy."
    next_move = "Once one person has become the default caregiver and that's taken for granted"
    redundant = (
        "A partner can comfort you, teach you, protect you, or carry more for a while, but they can’t permanently "
        "take over the job of reparenting your inner child. Each person still has to do that for themself, but that's "
        "easier said than done."
    )
    assert redundant not in output
    assert output.index(kept) < output.index(next_move)
    between = output[output.index(kept) + len(kept) : output.index(next_move)]
    assert between.strip() == ""


def test_primal_restores_owner_final_subsection_order_without_losing_current_prose() -> None:
    output = _assemble()
    start = output.index("# Primal attraction: channeling the Divine Masculine & Feminine")
    end = output.index("# Twin Flames?", start)
    primal = output[start:end]

    headings = [
        "## Fantasy",
        "## The Queen of Orgasms",
        "## Muses & Directors",
        "## Not A Performance",
        "## Desire is expressed differently for men & women",
    ]
    positions = [primal.index(heading) for heading in headings]
    assert positions == sorted(positions)

    protected = [
        "For me, safety gives the space for desire, even if it doesn't spark it.",
        "One time, Bee said she almost got enlightened, but I came too fast. Woops...",
        "She might say, “Thank you, I’ll consider that. What do you think about doing it this way?” as a kind of gentle, almost hypnotic leadership.",
        "The woman may argue with the plan, change it, improve it, or refuse it.",
        "Mandar obedeciendo, as the Zapatistas say.",
        "Bee once called me her “wife.” I don’t recommend that as a polarity exercise, by the way.",
        "That's called invitational: Would you rather go to a party where you were invited or a war you got drafted into?",
        "Women often show wanting directly. They ask, reach, name what they want, and ask the man to do things for them, even when they could do it themselves.",
        "The polarity evaporates when he keeps reaching without satisfaction, loses control of himself, or makes the woman responsible for regulating his emotions.",
        "[NATIVE YOUTUBE — preserve from Substack source — videoId: QqP3p_ysd84]",
    ]
    for sentence in protected:
        assert primal.count(sentence) == 1, sentence

    assert "## What I'm Not Saying" not in primal


def test_primal_owner_order_does_not_duplicate_two_pillars_caveat() -> None:
    output = _assemble()
    start = output.index("# Primal attraction: channeling the Divine Masculine & Feminine")
    end = output.index("# Twin Flames?", start)
    primal = output[start:end]
    assert "Polarity does not make two people sufficient for each other." not in primal
    assert output.count("Polarity does not make two people sufficient for each other.") == 1


def test_toft_anami_pass_adds_new_functions_without_duplicate_doctrines() -> None:
    output = _assemble()

    assert "## Affection and the simmer" in output
    assert output.count("https://dougtoft.substack.com/p/50-things-i-learned-from-50-years") == 1
    assert "Kim Anami calls the current between encounters" in output
    assert "You need both. Affection has to be safe from escalation, and the erotic current has to stay alive." in output

    assert "That’s what made me fall in love with her." in output
    assert output.count("I would rather be with you in the forest than with any other man in a mansion") == 1
    assert "there was the forest-and-mansion line I mentioned earlier" in output
    assert "She did nurse me, but a bit reluctantly." in output
    assert "What makes me desirable is not the same question as what makes me loved" in output

    assert "She got much better at receiving me." in output
    assert "some sexual responsiveness seems to be co-created between particular people" in output
    assert "At Temple University, I had a Colombian lawyer as an English/Spanish conversation partner." in output

    assert "after fifty years of marriage his main spiritual practice is being in relationship with his wife" in output
    assert "feminine energy from nature, music, poetry, art, flowers, food" in output
    assert "Role-play isn’t the problem. Getting trapped in the role is." in output

    assert "## Can making love be a spiritual practice?" in output
    assert "reserved for monastics" in output
    assert "When both husband and wife are faithful and generous, restraintful, living righteously, speaking pleasant words to each other" in output
    assert "[NATIVE YOUTUBE — preserve from Substack source — videoId: Li--FKwJu0Q]" in output

    assert "Maybe women are poetry and men are prose." in output
    assert "Do you want me to help figure this out, or do you mostly want me to listen?" in output
    assert "A woman earning more than her man doesn’t automatically make her masculine or him feminine." in output
    assert "Women can get trapped between opposite insecurities here." in output

    assert "## Boss Babe" not in output
    assert "## Boss babe" not in output
    assert "## Why marriage vows are honest?" not in output


def test_toft_anami_pass_preserves_primal_native_objects_and_order() -> None:
    output = _assemble()
    start = output.index("# Primal attraction: channeling the Divine Masculine & Feminine")
    end = output.index("# Twin Flames?", start)
    primal = output[start:end]

    ordered = [
        "## Fantasy",
        "## The Queen of Orgasms",
        "[NATIVE YOUTUBE — preserve from Substack source — videoId: QqP3p_ysd84]",
        "## Can making love be a spiritual practice?",
        "[NATIVE YOUTUBE — preserve from Substack source — videoId: Li--FKwJu0Q]",
        "## Muses & Directors",
        "## Not A Performance",
        "## Desire is expressed differently for men & women",
    ]
    positions = [primal.index(item) for item in ordered]
    assert positions == sorted(positions)
    for item in ordered:
        assert primal.count(item) == 1, item
