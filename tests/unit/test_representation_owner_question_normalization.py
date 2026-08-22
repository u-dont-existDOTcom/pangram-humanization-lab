from authorial_flow.models.codex_cli import _normalize_representation_output


def _payload(question: str) -> dict:
    return {
        "section_job": "preserve the existing job",
        "semantic_sanity": {
            "status": "PASS",
            "defect_types": [],
            "research_trigger": False,
            "recommended_escalation": "BASIC",
            "owner_question": question,
        },
        "units": [{"id": "u1", "text": "x", "reason": "source"}],
    }


def test_exact_none_sentinels_become_empty_owner_question() -> None:
    for question in (
        "None",
        "None.",
        "No owner question.",
        "No unresolved owner questions.",
    ):
        normalized = _normalize_representation_output(_payload(question), "representation")
        assert normalized["semantic_sanity"]["owner_question"] == ""


def test_live_machine_resolvable_none_form_becomes_empty() -> None:
    question = (
        "None. Owner context resolves the potentially material meanings, identities, certainty, "
        "and sequencing boundaries; remaining repairs are machine-resolvable representation work."
    )
    normalized = _normalize_representation_output(_payload(question), "representation")
    assert normalized["semantic_sanity"]["owner_question"] == ""


def test_real_question_is_never_erased_by_no_prefix() -> None:
    question = "No change is required to the label, but should the owner choose between A and B?"
    normalized = _normalize_representation_output(_payload(question), "representation")
    assert normalized["semantic_sanity"]["owner_question"] == question


def test_nonrepresentation_roles_are_untouched() -> None:
    payload = _payload("None.")
    normalized = _normalize_representation_output(payload, "research_question")
    assert normalized["semantic_sanity"]["owner_question"] == "None."
