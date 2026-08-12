import json
from pathlib import Path
from pangram_lab.cache import PangramCache
from pangram_lab.legacy_import import import_legacy_tree


def test_imports_v4_success_from_old_campaign_state(tmp_path):
    legacy=tmp_path/"old"; legacy.mkdir()
    text="legacy passage"
    import hashlib
    h=hashlib.sha256(text.encode()).hexdigest()
    state={"measurements":{"M01":{"input_sha256":h,"status":"success","result":{"api_version":"4.0","headline":"Human Written","prediction_short":"Human","fraction_ai":0.0,"fraction_ai_assisted":0.0,"fraction_human":1.0,"raw_response_file":"raw/M01.json"}}}}
    (legacy/"campaign-state.json").write_text(json.dumps(state))
    (legacy/"raw").mkdir(); (legacy/"raw/M01.json").write_text(json.dumps({"stage":"STAGE_SUCCESS","version":"4.0","headline":"Human Written","prediction_short":"Human","fraction_ai":0.0,"fraction_ai_assisted":0.0,"fraction_human":1.0,"text":text,"task_id":"oldtask"}))
    cache=PangramCache(tmp_path/"cache")
    report=import_legacy_tree(legacy,cache)
    rec=cache.lookup("pangram-4","4.0",text,"base")
    assert report["v4_success_imported"] == 1
    assert rec and rec["status"] == "success"


def test_imports_live_v1_harness_result_but_skips_dry_run(tmp_path):
    legacy=tmp_path/"newer"; run=legacy/"runs/case"; run.mkdir(parents=True)
    live="live endpoint"; dry="dry endpoint"
    import hashlib
    state={"config":{"dry_run":False,"pangram_model":"pangram-4","expected_pangram_version":"4.0"},"results":{
      hashlib.sha256(live.encode()).hexdigest():{"text":live,"pangram":{"stage":"STAGE_SUCCESS","version":"4.0","headline":"Human Written","prediction_short":"Human","fraction_ai":0,"fraction_ai_assisted":0,"fraction_human":1,"text":live,"task_id":"live-task"}}
    }}
    (run/"state.json").write_text(json.dumps(state))
    dryrun=legacy/"runs/_dry/case"; dryrun.mkdir(parents=True)
    (dryrun/"state.json").write_text(json.dumps({"config":{"dry_run":True},"results":{hashlib.sha256(dry.encode()).hexdigest():{"text":dry,"pangram":{"dry_run":True,"version":"4.0","text":dry}}}}))
    cache=PangramCache(tmp_path/"cache")
    report=import_legacy_tree(legacy,cache)
    assert cache.lookup("pangram-4","4.0",live,"base") is not None
    assert cache.lookup("pangram-4","4.0",dry,"base") is None

def test_legacy_import_is_idempotent_and_does_not_rewrite_existing_success(tmp_path):
    legacy=tmp_path/'old'; raw=legacy/'raw'; raw.mkdir(parents=True)
    text='same'; obj={"stage":"STAGE_SUCCESS","version":"4.0","headline":"Human Written","prediction_short":"Human","fraction_ai":0,"fraction_ai_assisted":0,"fraction_human":1,"text":text,"task_id":"t"}
    (raw/'one.json').write_text(json.dumps(obj))
    cache=PangramCache(tmp_path/'cache')
    first=import_legacy_tree(legacy,cache)
    path=cache.path_for('pangram-4','4.0',text,'base')
    before=path.read_bytes()
    second=import_legacy_tree(legacy,cache)
    after=path.read_bytes()
    assert first['v4_success_imported'] == 1
    assert second['v4_success_imported'] == 0
    assert before == after


def test_v1_state_import_is_idempotent(tmp_path):
    legacy=tmp_path/'newer'; run=legacy/'runs/case'; run.mkdir(parents=True)
    text='endpoint'; import hashlib
    state={'config':{'dry_run':False,'pangram_model':'pangram-4','expected_pangram_version':'4.0'},'results':{hashlib.sha256(text.encode()).hexdigest():{'text':text,'pangram':{'stage':'STAGE_SUCCESS','version':'4.0','headline':'Human Written','prediction_short':'Human','fraction_ai':0,'fraction_ai_assisted':0,'fraction_human':1,'text':text,'task_id':'t'}}}}
    (run/'state.json').write_text(json.dumps(state))
    cache=PangramCache(tmp_path/'cache')
    assert import_legacy_tree(legacy,cache)['v4_success_imported']==1
    path=cache.path_for('pangram-4','4.0',text,'base'); before=path.read_bytes()
    assert import_legacy_tree(legacy,cache)['v4_success_imported']==0
    assert path.read_bytes()==before
