from pathlib import Path
from pangram_lab.cache import PangramCache
from pangram_lab.engine import Engine

class InvalidCodex:
    def run_json(self,role,prompt,schema,out,log):
        if role!='designer': raise AssertionError(role)
        out.parent.mkdir(parents=True,exist_ok=True); log.parent.mkdir(parents=True,exist_ok=True)
        plan={"status":"planned","summary":"bad","owner_question":"","objective":"o","factors":[],"probes":[
          {"id":"AI_ENDPOINT","text":"ai","provenance":"x","controlled_variable":"c","semantic_fidelity_note":"x","synthetic":False,"assignments":[]},
          {"id":"HUMAN_ENDPOINT","text":"human","provenance":"x","controlled_variable":"c","semantic_fidelity_note":"x","synthetic":False,"assignments":[]}
        ],"contrasts":[{"id":"bad","label":"bad","left_probe":"AI_ENDPOINT","right_probe":"mean[(x)]","interpretive_question":"q","repeat_eligible":True}],"repeat_threshold":0.03,"blind_editorial_judgments":[],"stop_rule":"s","why_high_information":"w"}
        import json
        out.write_text(json.dumps(plan)); log.write_text('designer output')
        return plan
class NoPangram: model='pangram-4'; expected_version='4.0'
class RecordingGit:
    def __init__(self): self.reasons=[]
    def sync(self,r): self.reasons.append(r)

def test_invalid_designer_output_and_failure_are_checkpointed(tmp_path):
    (tmp_path/'prompts').mkdir(); (tmp_path/'schemas').mkdir()
    (tmp_path/'prompts/designer.md').write_text('d'); (tmp_path/'schemas/plan.schema.json').write_text('{}')
    git=RecordingGit(); e=Engine(tmp_path,InvalidCodex(),NoPangram(),PangramCache(tmp_path/'cache'),git,max_rounds=1)
    import pytest, json
    with pytest.raises(ValueError): e.run('ai','human')
    cases=list((tmp_path/'cases').iterdir()); rdir=cases[0]/'r01'
    assert (rdir/'plan-attempt01.json').is_file()
    assert (rdir/'plan-attempt03.json').is_file()
    assert (rdir/'failure.json').is_file()
    assert any('designer raw output' in x for x in git.reasons)
    assert any('plan validation failure' in x for x in git.reasons)
