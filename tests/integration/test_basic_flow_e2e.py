import json
from pathlib import Path
import zipfile

from authorial_flow.authority import Authority, AuthorityUnit
from authorial_flow.candidates import CandidateRecord, freeze_editorial_winner
from authorial_flow.config import RuntimeConfig
from authorial_flow.finalize import build_evidence_package
from authorial_flow.models.pangram import PangramResult
from authorial_flow.nodes.detector_search import detector_node
from authorial_flow.nodes.fidelity import relation_guard
from authorial_flow.nodes.flow import judge_edge_locally
from authorial_flow.nodes.generate import candidate_semantic_spans
from authorial_flow.nodes.owner_interrupt import validate_owner_response


class FakeWriter:
    def __init__(self): self.seen_owner_gold=False
    def write(self, payload):
        self.seen_owner_gold = "owner_gold" in payload
        return "Choices happen and matter."


class FakePangram:
    def __init__(self): self.submit_count=0
    def evaluate(self,text,candidate_hash,pending=None):
        self.submit_count += 1
        return PangramResult("STAGE_SUCCESS","4.0","Human",0,0,(),{},True)


def _seed_package_dirs(root:Path):
    for name in ("policy","project"):
        d=root/name; d.mkdir(parents=True,exist_ok=True); (d/"MANIFEST.json").write_text('{}')


def test_full_mocked_basic_flow_reaches_owner_accept_and_packages_evidence(tmp_path,monkeypatch):
    writer=FakeWriter(); pangram=FakePangram()
    move=writer.write({"accepted_moves":["AN 3.61 rejects views that would make effort meaningless."]})
    assert candidate_semantic_spans(move) == [move]
    assert judge_edge_locally(["AN 3.61 rejects views that would make effort meaningless."],move).verdict == "PASS"

    candidate=freeze_editorial_winner([
        CandidateRecord(id="c1",text=move,editorial_score=9.2,hard_pass=True,lineage_id="L0")
    ])
    measured=detector_node(candidate,pangram)
    assert measured.status == "HUMAN"
    owner=validate_owner_response({"kind":"ACCEPT"},move_count=1)
    final_status="accepted" if owner["kind"]=="ACCEPT" else "blocked"

    cfg=RuntimeConfig.from_root(tmp_path); _seed_package_dirs(tmp_path)
    cfg.state_dir.mkdir(parents=True,exist_ok=True)
    (cfg.state_dir/"final-candidate.md").write_text(candidate.text)
    (cfg.state_dir/"owner-response.json").write_text(json.dumps(owner))
    monkeypatch.setenv("PANGRAM_API_KEY","secret-test-value")
    evidence_zip=build_evidence_package(cfg,reason="final")

    assert final_status == "accepted"
    assert pangram.submit_count == 1
    assert writer.seen_owner_gold is False
    assert evidence_zip.exists()
    with zipfile.ZipFile(evidence_zip) as z:
        payload=b"\n".join(z.read(name) for name in z.namelist() if not name.endswith("/"))
    assert b"PANGRAM_API_KEY" not in payload
    assert b"secret-test-value" not in payload


def test_fidelity_invalid_candidate_never_reaches_pangram_or_owner():
    pangram=FakePangram()
    source="AN 6.63 says intention is kamma and that contact is its source. Choices happen and matter."
    text="So choices happen and matter."
    fidelity=relation_guard(source,text)
    assert fidelity.verdict == "FAIL"
    candidate=freeze_editorial_winner([
        CandidateRecord(id="bad",text=text,editorial_score=8,hard_pass=False,lineage_id="L0")
    ])
    out=detector_node(candidate,pangram)
    assert out.status == "SKIPPED_LOCAL_FAILURE"
    assert pangram.submit_count == 0
