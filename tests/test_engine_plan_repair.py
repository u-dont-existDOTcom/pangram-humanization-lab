from pangram_lab.cache import PangramCache
from pangram_lab.engine import Engine

class RepairingCodex:
    def __init__(self): self.designs=0
    def run_json(self,role,prompt,schema,out,log):
        out.parent.mkdir(parents=True,exist_ok=True); log.parent.mkdir(parents=True,exist_ok=True); log.write_text(role)
        if role=='designer':
            self.designs+=1
            bad=self.designs==1
            return {"status":"planned","summary":"plan","owner_question":"","objective":"o","factors":[],"probes":[
              {"id":"AI_ENDPOINT","text":"ai","provenance":"x","controlled_variable":"c","semantic_fidelity_note":"x","synthetic":False,"assignments":[]},
              {"id":"HUMAN_ENDPOINT","text":"human","provenance":"x","controlled_variable":"c","semantic_fidelity_note":"x","synthetic":False,"assignments":[]}
            ],"contrasts":[{"id":"C","label":"c","left_probe":"AI_ENDPOINT","right_probe":"mean[(bad)]" if bad else "HUMAN_ENDPOINT","interpretive_question":"q","repeat_eligible":False}],"repeat_threshold":0.03,"blind_editorial_judgments":[],"stop_rule":"s","why_high_information":"w"}
        if role=='reviewer': return {"status":"approved","approved_probe_ids":["AI_ENDPOINT","HUMAN_ENDPOINT"],"rejected":[],"notes":[],"owner_question":""}
        if role=='analyst': return {"next_action":"stop","novel_discrimination":True,"stop_reason":"done","owner_question":"","summary":"done","supported":[],"falsified":[],"unresolved":[],"next_experiment_goal":""}
        raise AssertionError(role)
class FakePangram:
    model='pangram-4'; expected_version='4.0'
    def detect_cached(self,text,cache,measurement_key='base'):
        r={"version":"4.0","headline":"Human Written" if text=='human' else "AI Generated","prediction_short":"Human" if text=='human' else "AI","fraction_ai":0 if text=='human' else 1,"fraction_ai_assisted":0,"fraction_human":1 if text=='human' else 0,"text":text}
        cache.save_success('pangram-4','4.0',text,measurement_key,'t',r); return r
class NoopGit:
    def sync(self,r): pass

def test_invalid_plan_is_repaired_by_codex_without_owner_intervention(tmp_path):
    (tmp_path/'prompts').mkdir(); (tmp_path/'schemas').mkdir()
    for role in ('designer','reviewer','analyst'): (tmp_path/'prompts'/f'{role}.md').write_text(role)
    for name in ('plan','review','analysis'): (tmp_path/'schemas'/f'{name}.schema.json').write_text('{}')
    c=RepairingCodex(); e=Engine(tmp_path,c,FakePangram(),PangramCache(tmp_path/'cache'),NoopGit(),max_rounds=1)
    out=e.run('ai','human')
    assert out['status']=='stopped'
    assert c.designs==2
    case=next((tmp_path/'cases').iterdir()); r=case/'r01'
    assert (r/'plan-attempt01.json').is_file()
    assert (r/'plan-attempt02.json').is_file()
