import pytest
from authorial_flow.nodes.owner_interrupt import validate_owner_response


def test_accept_owner_response_is_valid():
    assert validate_owner_response({"kind":"ACCEPT"}, move_count=4)["kind"] == "ACCEPT"


def test_bad_edge_requires_in_bounds_first_bad_move():
    with pytest.raises(ValueError):
        validate_owner_response({"kind":"BAD_EDGE","move_index":1}, move_count=4)
    assert validate_owner_response({"kind":"BAD_EDGE","move_index":3}, move_count=4)["move_index"] == 3


def test_unknown_owner_response_kind_rejected():
    with pytest.raises(ValueError):
        validate_owner_response({"kind":"DEBUG_THE_SCRIPT"}, move_count=4)
