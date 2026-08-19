import json
from pathlib import Path


def walk(obj):
    if isinstance(obj, dict):
        if obj.get("type") == "object":
            assert obj.get("additionalProperties") is False
            props=obj.get("properties",{})
            assert set(obj.get("required",[])) == set(props)
        for v in obj.values(): walk(v)
    elif isinstance(obj,list):
        for v in obj: walk(v)


def test_all_output_schemas_are_strict_recursively():
    root=Path(__file__).parents[1]/"schemas"
    files=sorted(root.glob("*.schema.json"))
    expected={
        "plan.schema.json",
        "review.schema.json",
        "analysis.schema.json",
        "authorial_flow_controller.schema.json",
        "authorial_flow_writer.schema.json",
        "authorial_flow_fidelity.schema.json",
        "authorial_flow_flow.schema.json",
    }
    assert {p.name for p in files} == expected
    for p in files:
        walk(json.loads(p.read_text()))