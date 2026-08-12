from authorial_flow.authority import Authority, AuthorityUnit
from authorial_flow.nodes.developmental import (
    ArchitectureCard, validate_developmental_result, build_developmental_result,
)


def test_owner_locked_unit_cannot_be_dropped():
    locked=[AuthorityUnit(id='u1',text='owner fact',authority=Authority.OWNER_LOCKED)]
    errors=validate_developmental_result(locked,[])
    assert any('u1' in e for e in errors)


def test_ai_provisional_unit_may_be_omitted_with_reason():
    units=[AuthorityUnit(id='u2',text='AI bridge',authority=Authority.AI_PROVISIONAL)]
    proposed=[{'id':'u2','disposition':'omit','reason':'unsupported bridge'}]
    assert validate_developmental_result(units,proposed) == []


def test_ai_provisional_omission_requires_reason():
    units=[AuthorityUnit(id='u2',text='AI bridge',authority=Authority.AI_PROVISIONAL)]
    errors=validate_developmental_result(units,[{'id':'u2','disposition':'omit','reason':''}])
    assert errors


def test_owner_position_change_stays_candidate_only():
    units=[AuthorityUnit(id='u1',text='I think X',authority=Authority.OWNER_GROUNDED)]
    card=ArchitectureCard(heading_promise='q',real_pressure='p',reader_stake='s',controlling_claim='X',certainty='tentative',governing_movement='inquiry',stopping_point='open')
    result=build_developmental_result(units,[{'id':'u1','disposition':'use','text':'I think Y','reason':'alternative reasoning'}],card=card,owner_position_changed=True)
    assert result.candidate_only is True
    assert result.original_units[0].text == 'I think X'


def test_owner_locked_unit_cannot_be_banked_out_of_active_prose():
    locked=[AuthorityUnit(id='u1',text='owner fact',authority=Authority.OWNER_LOCKED,exact_lock=True)]
    errors=validate_developmental_result(
        locked,[{'id':'u1','text':'owner fact','disposition':'bank','reason':'move aside'}]
    )
    assert any('u1' in e and 'cannot be dropped' in e for e in errors)


def test_owner_position_change_does_not_suppress_owner_lock_validation_errors():
    locked=[AuthorityUnit(id='u1',text='owner fact',authority=Authority.OWNER_LOCKED,exact_lock=True)]
    card=ArchitectureCard(heading_promise='q',real_pressure='p',reader_stake='s',controlling_claim='X',certainty='owner',governing_movement='inquiry',stopping_point='open')
    try:
        build_developmental_result(
            locked,[{'id':'u1','text':'changed','disposition':'use','reason':'alternative'}],
            card=card,owner_position_changed=True,
        )
    except ValueError as exc:
        assert 'exact-lock text changed' in str(exc)
    else:
        raise AssertionError('owner_position_changed must not waive exact-lock validation')
