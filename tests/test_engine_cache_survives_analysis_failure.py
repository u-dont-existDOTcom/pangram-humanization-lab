import json
from pathlib import Path
from pangram_lab.cache import PangramCache
from pangram_lab.engine import Engine


class FakeCodex:
    def __init__(self): self.calls=[]
    def run_json(self,role,prompt,schema,out,log):
        self.calls.append(role)
        if role=='designer':
            return {"status":"planned","summary":"one","owner_question":"","objective":"o","factors":[],"probes":[
              {"id":"AI_ENDPOINT","text":"ai","provenance":"endpoint","controlled_variable":"control","semantic_fidelity_note":"exact","synthetic":False,"assignments":[]},
              {"id":"HUMAN_ENDPOINT","text":"human","provenance":"endpoint","controlled_variable":"control","semantic_fidelity_note":"exact","synthetic":False,"assignments":[]}
            ],"contrasts":[{"id":"C","label":"endpoints","left_probe":"AI_ENDPOINT","right_probe":"HUMAN_ENDPOINT","interpretive_question":"q","repeat_eligible":False}],"repeat_threshold":0.03,"blind_editorial_judgments":["human"],"stop_rule":"stop","why_high_information":"why"}
        if role=='reviewer': return {"status":"approved","approved_probe_ids":["AI_ENDPOINT","HUMAN_ENDPOINT"],"rejected":[],"notes":[],"owner_question":""}
        raise RuntimeError('analysis exploded')

class FakePangram:
    model='pangram-4'; expected_version='4.0'
    def detect_cached(self,text,cache,measurement_key='base'):
        rec=cache.lookup(self.model,self.expected_version,text,measurement_key)
        if rec: return rec['result']
        r={"stage":"STAGE_SUCCESS","version":"4.0","headline":"Human Written" if text=='human' else "AI Generated","prediction_short":"Human" if text=='human' else "AI","fraction_ai":0 if text=='human' else 1,"fraction_ai_assisted":0,"fraction_human":1 if text=='human' else 0,"text":text}
        cache.save_success(self.model,self.expected_version,text,measurement_key,'t-'+text,r)
        return r

class NoopGit:
    def sync(self,reason): pass


def test_results_are_durable_before_analyst_failure(tmp_path):
    (tmp_path/'prompts').mkdir(); (tmp_path/'schemas').mkdir()
    for role in ('designer','reviewer','analyst'):
        (tmp_path/'prompts'/f'{role}.md').write_text(role)
        (tmp_path/'schemas'/f'{role if role != 'designer' else 'plan'}.schema.json').write_text('{}')
    cache=PangramCache(tmp_path/'cache'); engine=Engine(tmp_path,FakeCodex(),FakePangram(),cache,NoopGit(),max_rounds=1,max_calls=10)
    try: engine.run('ai','human')
    except RuntimeError as e: assert 'analysis exploded' in str(e)
    assert cache.lookup('pangram-4','4.0','ai','base')["status"]=='success'
    assert cache.lookup('pangram-4','4.0','human','base')["status"]=='success'
from pathlib import Path
from pangram_lab.cache import PangramCache
from pangram_lab.engine import Engine


def planned(ai='ai', human='human'):
    return {"status":"planned","summary":"frozen plan","owner_question":"","objective":"o","factors":[],"probes":[
      {"id":"AI_ENDPOINT","text":ai,"provenance":"endpoint","controlled_variable":"control","semantic_fidelity_note":"exact","synthetic":False,"assignments":[]},
      {"id":"HUMAN_ENDPOINT","text":human,"provenance":"endpoint","controlled_variable":"control","semantic_fidelity_note":"exact","synthetic":False,"assignments":[]}
    ],"contrasts":[{"id":"C","label":"endpoints","left_probe":"AI_ENDPOINT","right_probe":"HUMAN_ENDPOINT","interpretive_question":"q","repeat_eligible":False}],"repeat_threshold":0.03,"blind_editorial_judgments":["human"],"stop_rule":"stop","why_high_information":"why"}


class FirstCodex:
    def run_json(self, role, prompt, schema, out, log):
        out.parent.mkdir(parents=True, exist_ok=True); log.parent.mkdir(parents=True, exist_ok=True); log.write_text(role)
        if role == 'designer': return planned()
        if role == 'reviewer': return {"status":"approved","approved_probe_ids":["AI_ENDPOINT","HUMAN_ENDPOINT"],"rejected":[],"notes":[],"owner_question":""}
        raise RuntimeError('analyst crashed after paid results')


class ResumeCodex:
    def __init__(self): self.calls=[]
    def run_json(self, role, prompt, schema, out, log):
        self.calls.append(role)
        if role in {'designer','reviewer'}:
            raise AssertionError(f'{role} must be resumed from frozen artifact, not rerun')
        if role == 'analyst':
            return {"next_action":"stop","novel_discrimination":True,"stop_reason":"done","owner_question":"","summary":"done","supported":[],"falsified":[],"unresolved":[],"next_experiment_goal":""}
        raise AssertionError(role)


class FakePangram:
    model='pangram-4'; expected_version='4.0'
    def __init__(self): self.calls=[]
    def detect_cached(self,text,cache,measurement_key='base'):
        self.calls.append((text, measurement_key))
        rec=cache.lookup(self.model,self.expected_version,text,measurement_key)
        if rec and rec.get('status') == 'success': return rec['result']
        r={"stage":"STAGE_SUCCESS","version":"4.0","headline":"Human Written" if text=='human' else "AI Generated","prediction_short":"Human" if text=='human' else "AI","fraction_ai":0 if text=='human' else 1,"fraction_ai_assisted":0,"fraction_human":1 if text=='human' else 0,"text":text}
        cache.save_success(self.model,self.expected_version,text,measurement_key,'t-'+text,r)
        return r


class NoopGit:
    def sync(self, reason): pass


def setup_root(root):
    (root/'prompts').mkdir(); (root/'schemas').mkdir()
    for role in ('designer','reviewer','analyst'): (root/'prompts'/f'{role}.md').write_text(role)
    for name in ('plan','review','analysis'): (root/'schemas'/f'{name}.schema.json').write_text('{}')


def test_restart_after_analyst_failure_reuses_frozen_plan_and_review(tmp_path):
    setup_root(tmp_path)
    cache=PangramCache(tmp_path/'cache')
    first=Engine(tmp_path,FirstCodex(),FakePangram(),cache,NoopGit(),max_rounds=1)
    try: first.run('ai','human')
    except RuntimeError as exc: assert 'analyst crashed' in str(exc)
    else: raise AssertionError('first run must fail')

    resumed_codex=ResumeCodex(); pangram=FakePangram()
    second=Engine(tmp_path,resumed_codex,pangram,cache,NoopGit(),max_rounds=1)
    out=second.run('ai','human')
    assert out['status']=='stopped'
    assert resumed_codex.calls == ['analyst']
    assert pangram.calls == [('ai','base'),('human','base')]

class TwoRoundFirstCodex:
    def __init__(self): self.designer_calls=0
    def run_json(self, role, prompt, schema, out, log):
        out.parent.mkdir(parents=True,exist_ok=True); log.parent.mkdir(parents=True,exist_ok=True); log.write_text(role)
        if role=='designer':
            self.designer_calls += 1
            if self.designer_calls == 2: raise RuntimeError('round2 designer crashed')
            return planned()
        if role=='reviewer': return {"status":"approved","approved_probe_ids":["AI_ENDPOINT","HUMAN_ENDPOINT"],"rejected":[],"notes":[],"owner_question":""}
        if role=='analyst': return {"next_action":"continue","novel_discrimination":True,"stop_reason":"","owner_question":"","summary":"round1 complete","supported":[],"falsified":[],"unresolved":["x"],"next_experiment_goal":"next"}
        raise AssertionError(role)

class Round2ResumeCodex:
    def __init__(self): self.calls=[]
    def run_json(self, role, prompt, schema, out, log):
        self.calls.append(role)
        out.parent.mkdir(parents=True,exist_ok=True); log.parent.mkdir(parents=True,exist_ok=True); log.write_text(role)
        if role=='designer': return planned()
        if role=='reviewer': return {"status":"approved","approved_probe_ids":["AI_ENDPOINT","HUMAN_ENDPOINT"],"rejected":[],"notes":[],"owner_question":""}
        if role=='analyst': return {"next_action":"stop","novel_discrimination":True,"stop_reason":"finished","owner_question":"","summary":"round2 complete","supported":[],"falsified":[],"unresolved":[],"next_experiment_goal":""}
        raise AssertionError(role)

def test_restart_skips_completed_rounds_from_history(tmp_path):
    setup_root(tmp_path); cache=PangramCache(tmp_path/'cache')
    first=Engine(tmp_path,TwoRoundFirstCodex(),FakePangram(),cache,NoopGit(),max_rounds=2)
    try: first.run('ai','human')
    except RuntimeError as exc: assert 'round2 designer crashed' in str(exc)
    else: raise AssertionError('first run must fail in round2')
    case=next((tmp_path/'cases').iterdir())
    history=__import__('json').loads((case/'history.json').read_text())
    assert [r['round_id'] for r in history['rounds']] == ['r01']

    codex=Round2ResumeCodex()
    out=Engine(tmp_path,codex,FakePangram(),cache,NoopGit(),max_rounds=2).run('ai','human')
    assert out['status']=='stopped'
    assert codex.calls == ['designer','reviewer','analyst']
