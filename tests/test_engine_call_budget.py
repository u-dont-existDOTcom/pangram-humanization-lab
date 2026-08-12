from pangram_lab.cache import PangramCache
from pangram_lab.engine import Engine


def plan():
    return {"status":"planned","summary":"budget","owner_question":"","objective":"o","factors":[],"probes":[
      {"id":"AI_ENDPOINT","text":"ai","provenance":"endpoint","controlled_variable":"control","semantic_fidelity_note":"exact","synthetic":False,"assignments":[]},
      {"id":"HUMAN_ENDPOINT","text":"human","provenance":"endpoint","controlled_variable":"control","semantic_fidelity_note":"exact","synthetic":False,"assignments":[]}
    ],"contrasts":[{"id":"C","label":"endpoints","left_probe":"AI_ENDPOINT","right_probe":"HUMAN_ENDPOINT","interpretive_question":"q","repeat_eligible":False}],"repeat_threshold":0.03,"blind_editorial_judgments":[],"stop_rule":"s","why_high_information":"w"}


class Codex:
    def run_json(self,role,prompt,schema,out,log):
        out.parent.mkdir(parents=True,exist_ok=True); log.parent.mkdir(parents=True,exist_ok=True); log.write_text(role)
        if role=='designer': return plan()
        if role=='reviewer': return {"status":"approved","approved_probe_ids":["AI_ENDPOINT","HUMAN_ENDPOINT"],"rejected":[],"notes":[],"owner_question":""}
        raise AssertionError('analyst must not run after budget stop')


class PangramThatWouldCharge:
    model='pangram-4'; expected_version='4.0'
    def __init__(self): self.calls=[]
    def detect_cached(self,text,cache,measurement_key='base'):
        self.calls.append((text,measurement_key))
        raise AssertionError('paid detector path must not be entered when budget is exhausted')


class Git:
    def sync(self,reason): pass


def setup(root):
    (root/'prompts').mkdir(); (root/'schemas').mkdir()
    for r in ('designer','reviewer','analyst'): (root/'prompts'/f'{r}.md').write_text(r)
    for s in ('plan','review','analysis'): (root/'schemas'/f'{s}.schema.json').write_text('{}')


def test_budget_is_checked_before_a_new_detector_submission(tmp_path):
    import pytest
    setup(tmp_path); p=PangramThatWouldCharge()
    e=Engine(tmp_path,Codex(),p,PangramCache(tmp_path/'cache'),Git(),max_rounds=1,max_calls=0)
    with pytest.raises(RuntimeError,match='budget'):
        e.run('ai','human')
    assert p.calls == []
