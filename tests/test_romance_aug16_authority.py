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


def test_doing_it_consciously_uses_current_approved_boundary() -> None:
    output = _assemble()
    assert (
        "I learned most of this by screwing it up. Some of it I just thought through, and I’m still not sure about all of it.\n\n"
        "## Imagination as a discernment tool"
    ) in output
    assert "All of this advice is also way too idealistic and unrealistic" not in output
    assert "Probably one of the most important benefits we can hope to get long term from any therapy" in output
    assert "So I would say the therapy worked if a week or two later" in output
    assert "You can put some rose petals around you or something to build the feeling" in output
    assert "The main takeaway here is, don’t let the medicine become the only time" not in output
    assert (
        "Well, yeah. It is painfully artificial. In a healthy communal society, the couple would have access to "
        "witnesses, elders, friends, and other emotional outlets and resources."
    ) in output
    assert "I’m trying to replace a missing community with instructions" not in output


def test_if_already_in_it_uses_aug16_owner_final() -> None:
    output = _assemble()
    assert "before jumping head first into head over shoulders" in output
    assert "one person can’t fix the relationship (unless they're the main problem in it)" in output
    assert "sometimes I was more honest than my partner could handle, which was its own kind of damage" in output
    assert "This is the time for agape to shine" in output
    assert "one person can’t create mutual honesty" not in output
    assert "I'm not saying to start dumping every hidden thought" not in output


def test_children_removes_non_authoritative_reconstruction_without_touching_owner_case() -> None:
    output = _assemble()
    assert "Never recruit children into the adult war. They get their own relationship with the other parent." in output
    assert "This was particularly difficult for me because Ann was very much unfit at the time to care for our son, Bear." in output
    assert "It takes a village." in output
    assert "I’m sorry that you see Mommy and Daddy arguing" not in output
    assert "That is the ordinary case. My situation with my first wife, Ann, became an extreme exception" not in output


def test_tough_love_uses_corrected_aug16_owner_final_and_terminal_stop() -> None:
    output = _assemble()
    assert "Romantic love is not easy, and the things that actually make it work are not very marketable." in output
    assert "the relationship is bigger and more important than the egos in it" in output
    assert "That spirit is like the universe living its desire to know itself through us" in output
    assert "But pathology festers when the environment is perfect for it." in output
    assert "hermetically seals two people together and calls that a luxurious privacy" in output
    assert "like mold that grows out of nowhere" in output
    assert "But pathology it festers" not in output
    assert "keep doing our own inner play & work (pl/ork)" not in output
    assert "Romantic love ain't easy" not in output

    rumi = "I believe Rumi was right: A sacred relationship will open and purify your hearts regardless of whether it ends."
    button = "[NATIVE BUTTON — Subscribe now — %%checkout_url%%]"
    assert output.count(rumi) == 1
    assert output.index(rumi) < output.index(button)
    assert output[output.index(rumi) + len(rumi) : output.index(button)].strip() == ""
