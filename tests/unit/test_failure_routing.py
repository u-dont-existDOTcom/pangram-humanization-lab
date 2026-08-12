from authorial_flow.failures import FailureClass, FailureRecord, classify_failure
from authorial_flow.routing import route_failure


def test_provider_failure_is_machine_repair():
    assert route_failure(FailureClass.PROVIDER_PLUMBING) == 'repair'


def test_missing_authorial_meaning_is_owner_interrupt():
    assert route_failure(FailureClass.OWNER_JUDGMENT) == 'owner_interrupt'


def test_pangram_only_failure_is_not_owner_question():
    assert route_failure(FailureClass.PANGRAM_ONLY) == 'repair'


def test_timeout_without_authorial_information_is_provider_plumbing():
    rec=FailureRecord(originating_node='writer',failure_code='timeout',authorial_information_missing=False)
    assert classify_failure(rec) is FailureClass.PROVIDER_PLUMBING


def test_owner_judgment_requires_explicit_authorial_information_missing():
    rec=FailureRecord(originating_node='semantic_sanity',failure_code='ambiguous meaning',authorial_information_missing=True)
    assert classify_failure(rec) is FailureClass.OWNER_JUDGMENT


def test_generation_machine_failure_routes_to_repair():
    from authorial_flow.routing import route_generation
    assert route_generation({'status': 'machine_failure'}) == 'repair'


def test_detector_nonhuman_routes_to_machine_repair_not_owner():
    from authorial_flow.routing import route_after_detector
    assert route_after_detector({'status': 'detector_nonhuman'}) == 'repair'
    assert route_after_detector({'status': 'owner_review_ready'}) == 'owner_review'


def test_owner_bad_edge_reenters_regressions_after_learning():
    from authorial_flow.routing import route_after_owner_learning
    assert route_after_owner_learning({'owner_response': {'kind': 'BAD_EDGE'}}) == 'regressions'


def test_detector_variant_retry_stays_in_detector_search_before_machine_repair():
    from authorial_flow.routing import route_after_detector
    assert route_after_detector({'status':'detector_retry'}) == 'detector'


def test_pause_status_preempts_every_machine_route():
    from authorial_flow.routing import (
        route_after_cold_audit,
        route_after_detector,
        route_after_freeze,
        route_after_owner_learning,
        route_after_regressions,
        route_after_repair,
        route_after_representation,
        route_generation,
    )

    state = {"status": "supervisor_pause_requested"}
    for route in (
        route_after_cold_audit,
        route_after_detector,
        route_after_freeze,
        route_after_owner_learning,
        route_after_regressions,
        route_after_repair,
        route_after_representation,
        route_generation,
    ):
        assert route(state) == "supervisor_pause"


def test_supervisor_route_allows_natural_owner_and_finalize_destinations():
    from authorial_flow.routing import route_after_supervisor

    for destination in ("owner_review", "owner_ambiguity", "research_adoption", "finalize"):
        assert route_after_supervisor({
            "status": "supervisor_resumed",
            "supervisor_resume_node": destination,
        }) == destination

    assert route_after_supervisor({
        "status": "supervisor_resumed",
        "supervisor_resume_node": "unknown-node",
    }) == "supervisor_pause"
