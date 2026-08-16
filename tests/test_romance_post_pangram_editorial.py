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


def test_if_slow_places_checkin_after_attachment_certainty_problem() -> None:
    output = _assemble()
    wanting = (
        "Wanting somebody doesn't tell me whether I should have children with her or build a life with her, "
        "and I can know the first part much faster than the second."
    )
    checkin = "Formal check-ins help too."
    special = "At some point one of you will ask, “Why am I special to you? Why are you with me and not somebody else?”"
    assert output.index(wanting) < output.index(checkin) < output.index(special)


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
