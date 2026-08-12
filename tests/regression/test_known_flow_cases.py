import json
from pathlib import Path
from authorial_flow.nodes.pressure import PressureVote, commit_pressure
from authorial_flow.nodes.flow import judge_edge_locally


def test_open_vote_vetoes_ordinary_premature_stop():
    result = commit_pressure([
        PressureVote(state="NATURAL_STOP", confidence=.84, live_pressure=""),
        PressureVote(state="OPEN", confidence=.81, live_pressure="what follows?"),
    ])
    assert result.state == "OPEN"


def test_known_owner_bad_edges_are_reproduced():
    gold=json.loads(Path("project/HUMAN-FLOW-GOLD.json").read_text())
    got=[]
    for case in gold["cases"]:
        result=judge_edge_locally(case["accepted_moves"], case["candidate"])
        got.append(result.verdict)
    assert got == [case["expected"] for case in gold["cases"]]
