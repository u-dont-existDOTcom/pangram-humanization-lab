"""Claim-integrity checks carried by the lab's own runtime instructions.

The adaptive harness sends ``prompts/<role>.md`` to Codex on every designer,
reviewer, and analyst call (``Engine._prompt``), and chat workers operate from
``docs/CHATGPT-OPERATING-GUIDE.md``. These tests pin the claim-integrity text in
those files and in the assembled runtime prompt, so it cannot disappear silently.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from pangram_lab.engine import Engine


ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts"
OPERATING_GUIDE = ROOT / "docs" / "CHATGPT-OPERATING-GUIDE.md"

ASSIGNED_CHECKS = {f"CI-{n:02d}" for n in range(1, 12)}

ROLE_ANCHORS = {
    "designer": [
        ("CI-01", "Rest every statement about what an endpoint, probe, or prior round says or shows on the supplied text or record"),
        ("CI-02", "Put only exact words inside quotation marks, and mark a translation as a translation."),
        ("CI-03", "Before saying that no prior round tested something, check every supplied round."),
        ("CI-05", "take figures from the supplied stats rather than from summaries or lessons"),
        ("CI-06", "name exactly which words differ from `HUMAN_ENDPOINT`: replaced, moved, added, or removed"),
        ("CI-06", "Describe the change itself rather than its hoped-for effect."),
        ("CI-08", "Keep every quotation from the Human endpoint word for word in every probe, keep every number, date, and name exact, and add no factual claim the Human endpoint does not make."),
        ("CI-10", "label a predicted detector outcome as a prediction"),
        ("CI-10", "Keep the plan consistent with the prior analyses. If it departs from a prior conclusion, say so and why."),
    ],
    "reviewer": [
        ("CI-01", "Base each rejection on exact words: quote what the probe says and what `HUMAN_ENDPOINT` says at that point, and name the meaning that changed."),
        ("CI-02", "Put only exact words inside quotation marks."),
        ("CI-03", "Before saying a probe drops or adds something, check the whole probe and the whole Human endpoint for it."),
        ("CI-08", "Compare every quotation, number, date, and name in each synthetic probe with `HUMAN_ENDPOINT` word for word."),
        ("CI-11", "Approve only probes that preserve the Human endpoint's substantive thought: claims, certainty, actor/action/object, chronology, causality, attribution, examples, scope, and relationship between ideas."),
        ("CI-08", "Reject a synthetic probe that changes any of them or adds a factual claim the Human endpoint does not make."),
        ("CI-09", "state the strongest reading under which it is not a problem, and drop the note if that reading is plausible"),
        ("CI-09", "Call something a contradiction only when both statements cannot be true under any reasonable reading."),
        ("CI-09", "Mark which notes are verified problems and which are suggestions that depend on a reading."),
        ("CI-09", "If the supplied lessons or records show that Joel already settled a question about his meaning, follow his answer."),
        ("CI-09", "Do not raise it again, including as a warning about readers, unless new evidence appears."),
        ("CI-09", "There is no quota. A review with no rejections and no notes is valid when every probe preserves the Human endpoint's meaning."),
        ("CI-10", "check that `approved_probe_ids`, `rejected`, and `notes` agree: no probe is both approved and rejected, and no note contradicts a decision"),
    ],
    "analyst": [
        ("CI-01", "Rest every statement about what a probe, contrast, repeat, or prior round shows on a supplied record"),
        ("CI-01", "Words such as all, every, never, and always need the same support."),
        ("CI-02", "Quote probe text only with its exact words."),
        ("CI-03", "A null result covers only the probes and boundary tested."),
        ("CI-05", "Take every figure from the result, repeat, and stats records rather than from summaries or lessons."),
        ("CI-05", "Count a repeat as a reproduction only when the records show a separate detector call."),
        ("CI-05", "count the two as one measurement"),
        ("CI-05", "Say when evidence is weak, for example a short passage or a single measurement."),
        ("CI-06", "When you call a hypothesis supported or falsified, name the contrasts and records you compared."),
        ("CI-06", "do not report it as the number of paid detector calls"),
        ("CI-10", "agree with each other and with prior analyses. If you revise a prior conclusion, say so."),
        ("CI-10", "Label estimates and predictions as such, and report a derived number no more precisely than its inputs."),
    ],
}

GUIDE_ANCHORS = [
    ("CI-01", "must rest on a passage or record you can point to"),
    ("CI-01", "Never add backstory, motives, or history that Joel or anyone else did not state."),
    ("CI-02", "Put only a source's exact words inside quotation marks. Mark translations as translations."),
    ("CI-03", "search all of it for counterexamples. Say so when you searched less than all of it."),
    ("CI-04", "need a source, or say they come from memory. When Joel has stated expertise in the area, find a source before contradicting his usage."),
    ("CI-05", "Two figures that trace to one measurement are one finding, and a cached copy of a result is the same measurement."),
    ("CI-06", "must name what you compared against which source or version, such as the exact boundary SHA-256 and result path"),
    ("CI-06", 'Deleted or replaced text was not "fixed".'),
    ("CI-07", "check the source before agreeing, just as you would before defending it. Agreement is not verification."),
    ("CI-07", "Joel's account of what he meant or prefers is owner authority and needs no outside source."),
    ("CI-08", "If a rewrite adds or changes a factual claim, quotation, figure, or attribution, check it against its source at that moment, even if it was checked earlier."),
    ("CI-08", 'An attribution such as "according to X" must not move Joel\'s own characterization onto X.'),
    ("CI-08", "list each factual claim you added or changed and where it comes from"),
    ("CI-09", "Before flagging a problem in prose or claims Joel wrote, state the strongest reading under which it is not a problem, and drop the flag if that reading is plausible."),
    ("CI-09", "There is no minimum number of findings."),
    ("CI-10", "compare what you are about to say with what you already said on the same topic, including earlier detector results"),
    ("CI-10", "Label estimates as estimates, and report a derived number at the resolution of its inputs."),
    ("CI-11", "Before returning a rewrite that adds or changes facts, a review of Joel's prose, a source attribution, or a statement that something was verified, make a claim ledger."),
    ("CI-11", "If no separate checker is available, check each ledger entry against its source yourself immediately before delivery and do not call the result independently checked."),
]

# Rules that already covered part of a check before the claim-integrity text was added.
EXISTING_COVERAGE = {
    PROMPTS / "designer.md": [
        "Preserve claims, certainty, agency, chronology, attribution, claim object, examples, and substantive meaning in every synthetic probe.",
        "The Human endpoint is editorial authority.",
    ],
    PROMPTS / "reviewer.md": [
        "Approve only probes that preserve the Human endpoint's substantive thought: claims, certainty, actor/action/object, chronology, causality, attribution, examples, scope, and relationship between ideas.",
        "If a proposed factor cannot be judged without irreducible author intent, return `needs_owner_input` with one narrow question.",
    ],
    OPERATING_GUIDE: [
        "every detector-driven change has been re-audited for semantic/rhetorical loss",
        "user-facing detector claims come from measured results rather than prediction or intuition",
        "estimated credit/cost fields only when explicitly labeled as estimates",
    ],
}


def _flat(text: str) -> str:
    return " ".join(text.split())


def _missing(anchors, text: str) -> list[str]:
    flat = _flat(text)
    return [f"{check}: {anchor}" for check, anchor in anchors if _flat(anchor) not in flat]


@pytest.mark.parametrize("role", sorted(ROLE_ANCHORS))
def test_role_prompt_file_carries_claim_integrity_checks(role):
    text = (PROMPTS / f"{role}.md").read_text(encoding="utf-8")
    assert _missing(ROLE_ANCHORS[role], text) == []


@pytest.mark.parametrize("role", sorted(ROLE_ANCHORS))
def test_assembled_runtime_prompt_carries_claim_integrity_checks(role):
    # This is the exact text the harness hands to Codex, so the checks must survive assembly.
    engine = Engine(ROOT, codex=None, pangram=None, cache=None, git=None)
    prompt = engine._prompt(role, "AI endpoint text", "Human endpoint text", [])
    assert _missing(ROLE_ANCHORS[role], prompt) == []


def test_operating_guide_carries_claim_integrity_checks():
    text = OPERATING_GUIDE.read_text(encoding="utf-8")
    assert "\n## Claim integrity\n" in text
    assert _missing(GUIDE_ANCHORS, text) == []


def test_every_assigned_check_is_carried_by_a_runtime_surface():
    carried = {check for anchors in ROLE_ANCHORS.values() for check, _ in anchors}
    carried |= {check for check, _ in GUIDE_ANCHORS}
    assert carried == ASSIGNED_CHECKS


def test_rules_counted_as_existing_coverage_remain():
    for path, anchors in EXISTING_COVERAGE.items():
        text = _flat(path.read_text(encoding="utf-8"))
        for anchor in anchors:
            assert _flat(anchor) in text, f"{path.name}: {anchor}"


def test_runtime_instructions_do_not_depend_on_the_development_pack():
    for path in [*(PROMPTS / f"{role}.md" for role in ROLE_ANCHORS), OPERATING_GUIDE]:
        text = path.read_text(encoding="utf-8")
        assert "universal-dev-architecture" not in text, path.name
        assert re.search(r"\bCI-(?:\d{2}|X1)\b", text) is None, path.name
