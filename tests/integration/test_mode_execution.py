from authorial_flow.modes import TaskMode
from authorial_flow.nodes.conservative import execute_mode


def test_p0_never_rewrites():
    result=execute_mode(TaskMode.P0,source='original',candidate=None,changes={},report_text='audit')
    assert result.report_ref == 'audit'
    assert result.candidate_ref is None
    assert result.writer_call_count == 0


def test_p2s_rejects_substantive_delta_and_research_remains_off():
    result=execute_mode(TaskMode.P2S,source='claim',candidate='candidate',changes={'claim_deleted':'c1'})
    assert result.status == 'MODE_VIOLATION'
    assert result.research_call_count == 0


def test_p1_rejects_paragraph_rearchitecture():
    result=execute_mode(TaskMode.P1,source='a\nb',candidate='b\na',changes={'paragraph_order_changed':True})
    assert result.status == 'MODE_VIOLATION'


def test_p1_allows_punctuation_only():
    result=execute_mode(TaskMode.P1,source='Hello world',candidate='Hello, world.',changes={'punctuation':True})
    assert result.status == 'PASS'


def test_p2_rejects_argument_order_change():
    result=execute_mode(TaskMode.P2,source='x',candidate='y',changes={'argument_order_changed':True})
    assert result.status == 'MODE_VIOLATION'
