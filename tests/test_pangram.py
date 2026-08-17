from pangram_lab.cache import PangramCache
from pangram_lab.pangram4 import PangramClient


class FakeTransport:
    def __init__(self):
        self.calls=[]
    def request(self, method, url, headers=None, body=None):
        self.calls.append((method,url,body))
        if method == "POST":
            return {"status":200,"json":{"task_id":"t123"}}
        return {"status":200,"json":{"stage":"STAGE_SUCCESS","version":"4.0","headline":"Human Written","prediction_short":"Human","fraction_ai":0.0,"fraction_ai_assisted":0.0,"fraction_human":1.0,"text":"abc"}}


def test_checkpoint_before_poll_and_reuse_success(tmp_path):
    t=FakeTransport(); cache=PangramCache(tmp_path)
    synced=[]
    client=PangramClient("secret", transport=t, sleep=lambda _:None, sync=lambda reason:synced.append(reason))
    first=client.detect_cached("abc", cache, "base")
    assert first["prediction_short"] == "Human"
    assert [x[0] for x in t.calls] == ["POST","GET"]
    assert cache.lookup("pangram-4","4.0","abc","base")["status"] == "success"
    t.calls.clear()
    second=client.detect_cached("abc", cache, "base")
    assert second["prediction_short"] == "Human"
    assert t.calls == []
    assert any("task checkpoint" in x for x in synced)
    assert any("result" in x for x in synced)


def test_pending_task_polls_without_resubmit(tmp_path):
    t=FakeTransport(); cache=PangramCache(tmp_path)
    cache.save_pending("pangram-4","4.0","abc","base","existing")
    client=PangramClient("secret", transport=t, sleep=lambda _:None, sync=lambda _:None)
    client.detect_cached("abc",cache,"base")
    assert [x[0] for x in t.calls] == ["GET"]

class AmbiguousPostTransport:
    def __init__(self): self.calls=0
    def request(self, method, url, headers=None, body=None):
        self.calls += 1
        raise OSError('connection vanished after write')


def test_ambiguous_submit_is_never_automatically_resubmitted(tmp_path):
    t=AmbiguousPostTransport(); cache=PangramCache(tmp_path)
    client=PangramClient('secret',transport=t,sleep=lambda _:None,sync=lambda _:None)
    import pytest
    with pytest.raises(Exception): client.detect_cached('abc',cache,'base')
    rec=cache.lookup('pangram-4','4.0','abc','base')
    assert rec['status'] == 'submit_ambiguous'
    calls=t.calls
    with pytest.raises(Exception,match='ambiguous'):
        client.detect_cached('abc',cache,'base')
    assert t.calls == calls

class CurrentContractTransport:
    def __init__(self): self.calls=[]
    def request(self,method,url,headers=None,body=None):
        self.calls.append((method,url,headers,body))
        if method=='GET' and url.endswith('/task/00000000-0000-0000-0000-000000000000'):
            return {'status':404,'json':{'detail':'not found'}}
        if method=='POST': return {'status':200,'json':{'task_id':'t9'}}
        return {'status':200,'json':{'stage':'STAGE_SUCCESS','version':'4.0','headline':'Human Written','prediction_short':'Human','fraction_ai':0,'fraction_ai_assisted':0,'fraction_human':1,'text':'abc'}}


def test_current_async_contract_uses_zero_task_auth_probe_and_explicit_pangram4_model(tmp_path):
    t=CurrentContractTransport(); cache=PangramCache(tmp_path)
    client=PangramClient('secret',transport=t,sleep=lambda _:None,sync=lambda _:None)
    client.probe_auth()
    result=client.detect_cached('abc',cache,'base')
    assert result['version']=='4.0'
    assert not any(url.endswith('/models') for _,url,_,_ in t.calls)
    post=[x for x in t.calls if x[0]=='POST'][0]
    assert post[3] == {'text':'abc','public_dashboard_link':False,'model':'pangram-4'}
    assert post[2]['x-api-key']=='secret'


def test_zero_task_404_does_not_claim_authentication(capsys):
    t=CurrentContractTransport()
    client=PangramClient('secret',transport=t,sleep=lambda _:None,sync=lambda _:None)
    client.probe_auth()
    output=capsys.readouterr().out
    assert 'authentication not established' in output
    assert 'auth probe reached' not in output

class Http500SubmitTransport:
    def __init__(self): self.calls=0
    def request(self, method, url, headers=None, body=None):
        self.calls += 1
        if method == 'POST':
            return {'status':500,'json':{'detail':'server failed after request reached service'}}
        raise AssertionError('poll must not occur without task id')


def test_submit_http_5xx_is_treated_as_ambiguous_and_not_reposted(tmp_path):
    import pytest
    t=Http500SubmitTransport(); cache=PangramCache(tmp_path)
    client=PangramClient('secret',transport=t,sleep=lambda _:None,sync=lambda _:None)
    with pytest.raises(Exception): client.detect_cached('abc',cache,'base')
    rec=cache.lookup('pangram-4','4.0','abc','base')
    assert rec['status']=='submit_ambiguous'
    calls=t.calls
    with pytest.raises(Exception,match='ambiguous'):
        client.detect_cached('abc',cache,'base')
    assert t.calls==calls


class LegacyDefaultThenV4Transport:
    def __init__(self): self.calls=[]
    def request(self,method,url,headers=None,body=None):
        self.calls.append((method,url,body))
        if method=='GET' and url.endswith('/task/existing'):
            return {'status':200,'json':{'stage':'STAGE_SUCCESS','version':'3.3.2','headline':'AI Generated','prediction_short':'AI','fraction_ai':1.0,'fraction_ai_assisted':0.0,'fraction_human':0.0,'text':'abc','task_id':'existing'}}
        if method=='POST':
            return {'status':200,'json':{'task_id':'new-v4'}}
        if method=='GET' and url.endswith('/task/new-v4'):
            return {'status':200,'json':{'stage':'STAGE_SUCCESS','version':'4.0','headline':'Human Written','prediction_short':'Human','fraction_ai':0.0,'fraction_ai_assisted':0.0,'fraction_human':1.0,'text':'abc','task_id':'new-v4'}}
        raise AssertionError((method,url,body))


def test_legacy_pending_default_v3_result_is_archived_then_corrected_once(tmp_path):
    import json
    t=LegacyDefaultThenV4Transport(); cache=PangramCache(tmp_path)
    # v2.0 wrote pending records before it included the requested model in POST.
    cache.save_pending('pangram-4','4.0','abc','base','existing')
    synced=[]
    client=PangramClient('secret',transport=t,sleep=lambda _:None,sync=lambda reason:synced.append(reason))
    result=client.detect_cached('abc',cache,'base')
    assert result['version']=='4.0'
    assert [x[0] for x in t.calls] == ['GET','POST','GET']
    post=[x for x in t.calls if x[0]=='POST'][0]
    assert post[2]['model']=='pangram-4'
    base=cache.lookup('pangram-4','4.0','abc','base')
    assert base['status']=='success'
    assert base['submitted_model']=='pangram-4'
    archives=[]
    for path in tmp_path.rglob('*.json'):
        obj=json.loads(path.read_text())
        if obj.get('status')=='terminal_wrong_version': archives.append(obj)
    assert len(archives)==1
    assert archives[0]['task_id']=='existing'
    assert archives[0]['result']['version']=='3.3.2'
    assert any('wrong-version' in reason for reason in synced)


class ExplicitModelWrongVersionTransport:
    def __init__(self): self.calls=[]
    def request(self,method,url,headers=None,body=None):
        self.calls.append((method,url,body))
        if method=='GET':
            return {'status':200,'json':{'stage':'STAGE_SUCCESS','version':'3.3.2','headline':'AI Generated','prediction_short':'AI','fraction_ai':1.0,'fraction_ai_assisted':0.0,'fraction_human':0.0,'text':'abc','task_id':'explicit'}}
        raise AssertionError('must not POST another task after an explicit pangram-4 request returns the wrong version')


def test_explicit_pangram4_wrong_version_fails_closed_without_new_post(tmp_path):
    import pytest
    t=ExplicitModelWrongVersionTransport(); cache=PangramCache(tmp_path)
    cache.save_pending('pangram-4','4.0','abc','base','explicit',submitted_model='pangram-4')
    client=PangramClient('secret',transport=t,sleep=lambda _:None,sync=lambda _:None)
    with pytest.raises(Exception,match='version mismatch'):
        client.detect_cached('abc',cache,'base')
    assert [x[0] for x in t.calls] == ['GET']
    rec=cache.lookup('pangram-4','4.0','abc','base')
    assert rec['status']=='terminal_wrong_version'
    calls=len(t.calls)
    with pytest.raises(Exception,match='version mismatch'):
        client.detect_cached('abc',cache,'base')
    assert len(t.calls)==calls
