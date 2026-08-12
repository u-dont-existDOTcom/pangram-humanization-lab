import json
from pathlib import Path
from authorial_flow.nodes.fidelity import relation_guard


def test_known_relation_failures_are_reproduced():
    gold=json.loads(Path("project/SEMANTIC-RELATION-GOLD.json").read_text())
    source=gold["source"]
    results=[relation_guard(source, case["candidate"]) for case in gold["cases"]]
    assert [r.verdict for r in results] == [case["expected"] for case in gold["cases"]]


def test_plain_source_statement_passes_relation_guard():
    source="AN 6.63 says intention is kamma and contact is its source."
    assert relation_guard(source, "AN 6.63 says intention is kamma.").verdict == "PASS"
