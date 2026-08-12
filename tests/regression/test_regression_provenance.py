from pathlib import Path
import json
from authorial_flow.nodes.regression import suite_identity, cached_result_matches, RegressionSummary
from authorial_flow.project import ProjectInputs, compute_thread_id
from authorial_flow.policy import PolicySnapshot


def test_stale_other_suite_cannot_pass(tmp_path):
    expected_hash, expected_ids = suite_identity({"cases": [{"id": "a"}, {"id": "b"}]})
    stale = {"suite_sha256": expected_hash, "case_ids": ["x"], "pass": True}
    assert cached_result_matches(stale, expected_hash, expected_ids) is False


def test_diagnostic_positive_is_not_hard_gate():
    summary = RegressionSummary(owner_flow_pass=True, semantic_pass=True, positive_diagnostic_pass=False)
    assert summary.hard_pass is True


def test_thread_id_changes_when_owner_gold_changes(tmp_path: Path):
    policy_dir=tmp_path/"policy"; policy_dir.mkdir()
    (policy_dir/"MASTER-INSTRUCTIONS.md").write_text("policy")
    PolicySnapshot.write_manifest(policy_dir)
    project=tmp_path/"project"; project.mkdir()
    required={
        "INPUT.md":"source", "REQUIREMENTS.md":"req", "AUTHOR_CONTEXT.md":"ctx",
        "HUMAN-FLOW-GOLD.json":json.dumps({"cases":[{"id":"a"}]}),
        "SEMANTIC-RELATION-GOLD.json":json.dumps({"cases":[]}),
        "SOURCE-FLOW-POSITIVE.json":json.dumps({"cases":[]}),
        "PANGRAM-SOURCE-BASELINE.json":"{}",
    }
    for name,text in required.items(): (project/name).write_text(text)
    ProjectInputs.write_manifest(project)
    p=PolicySnapshot.load(policy_dir); one=ProjectInputs.load(project)
    first=compute_thread_id(one,p,"g1","l1")
    (project/"HUMAN-FLOW-GOLD.json").write_text(json.dumps({"cases":[{"id":"b"}]}))
    ProjectInputs.write_manifest(project); two=ProjectInputs.load(project)
    assert first != compute_thread_id(two,p,"g1","l1")
