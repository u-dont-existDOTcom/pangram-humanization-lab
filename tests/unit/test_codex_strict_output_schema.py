from __future__ import annotations

import copy

from authorial_flow.models.codex_cli import _codex_output_schema
from authorial_flow.models.common import validate_schema_contract
from authorial_flow.runtime import DEVELOPMENTAL_SCHEMA


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def test_developmental_schema_projection_is_codex_strict_without_mutating_runtime_contract():
    original = copy.deepcopy(DEVELOPMENTAL_SCHEMA)
    architecture = original["properties"]["architecture_card"]
    # Regression shape that failed live: Pydantic defaults make these properties optional
    # and add default metadata before the provider projection.
    assert "required" not in architecture
    assert any("default" in node for node in _walk(architecture))

    projected = _codex_output_schema(DEVELOPMENTAL_SCHEMA)

    assert DEVELOPMENTAL_SCHEMA == original
    validate_schema_contract(projected)
    for node in _walk(projected):
        assert "default" not in node
        assert "title" not in node
        if node.get("type") == "object" and isinstance(node.get("properties"), dict):
            assert node.get("additionalProperties") is False
            assert node.get("required") == list(node["properties"])


def test_projection_recurses_through_defs_arrays_and_combiners():
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"$ref": "#/$defs/Thing"},
            },
            "choice": {
                "anyOf": [
                    {"type": "string", "default": "x"},
                    {"type": "null"},
                ]
            },
        },
        "$defs": {
            "Thing": {
                "type": "object",
                "title": "Thing",
                "properties": {
                    "name": {"type": "string", "default": ""},
                },
            }
        },
    }

    projected = _codex_output_schema(schema)
    assert projected["required"] == ["items", "choice"]
    thing = projected["$defs"]["Thing"]
    assert thing["additionalProperties"] is False
    assert thing["required"] == ["name"]
    assert "title" not in thing
    assert "default" not in thing["properties"]["name"]
    assert "default" not in projected["properties"]["choice"]["anyOf"][0]


def test_projection_preserves_original_types_and_enums():
    schema = {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["PASS", "FAIL"], "default": "PASS"},
            "confidence": {"type": "number", "default": 1.0},
        },
    }
    projected = _codex_output_schema(schema)
    assert projected["properties"]["verdict"] == {
        "type": "string",
        "enum": ["PASS", "FAIL"],
    }
    assert projected["properties"]["confidence"] == {"type": "number"}
