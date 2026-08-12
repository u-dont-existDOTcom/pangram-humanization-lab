from authorial_flow.nodes.boundary import generation_boundary_id


def test_generation_boundary_id_is_stable_for_equivalent_state():
    first=generation_boundary_id(
        ['One move.'],{'u2':False,'u1':True},graph_version='1.1',program_version='abc'
    )
    second=generation_boundary_id(
        ['One move.'],{'u1':True,'u2':False},graph_version='1.1',program_version='abc'
    )
    assert first==second


def test_generation_boundary_id_changes_with_every_controlling_dimension():
    base=generation_boundary_id(
        ['One move.'],{'u1':True},graph_version='1.1',program_version='abc'
    )
    variants=[
        generation_boundary_id(['One move.','Two.'],{'u1':True},graph_version='1.1',program_version='abc'),
        generation_boundary_id(['One move.'],{'u1':False},graph_version='1.1',program_version='abc'),
        generation_boundary_id(['One move.'],{'u1':True},graph_version='1.2',program_version='abc'),
        generation_boundary_id(['One move.'],{'u1':True},graph_version='1.1',program_version='def'),
    ]
    assert len({base,*variants})==5

